"""Read-only remeasurement of archived synthetic horizon videos.

Execute only function AST nodes from measure_ripple_spectral.py; never import
the generator or run archive-writing main functions. Original measure() math
is retained. Its profile loop is replaced by an algebraically identical
vectorized mean and checked against the original on sampled frames.

Example (all paths explicit; output must be outside the source archive):
  python reproduce_horizon.py --source-root E:/D_Folder/download/test \
      --output-root C:/paper/output/horizon_reproduction
Use --inspect-only for sparse fixed-frame PNGs and mask diagnostics, without
remeasuring or hashing entire videos. Dependencies: NumPy and OpenCV.
"""
import argparse
import ast
import csv
import hashlib
import json
import math
import platform
import sys
from concurrent.futures import ProcessPoolExecutor, as_completed
from datetime import datetime, timezone
from pathlib import Path

import cv2
import numpy as np

AUDITED_MEASUREMENT_SHA256 = "ccad2778ba0efb27d132ec7a27ac5d495c09ab25e77cd8257cb3c4fb1937e834"
CASES = [("Outdoor-1", "cam3_out_h", "captures6"),
         ("Outdoor-2", "cam3_c5_h", "captures5"),
         ("Indoor", "cam3_horizon", "captures")]
METHODS = [("Raw", "unstab.mp4"), ("G-locked", "our_stab.mp4"),
           ("Optical flow", "of_stab.mp4")]


def fingerprint(path):
    path = Path(path)
    before = path.stat()
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(4 * 1024 * 1024), b""):
            h.update(block)
    after = path.stat()
    return dict(path=path.as_posix(), bytes=after.st_size, sha256=h.hexdigest(),
                stable_during_hash=before.st_size == after.st_size and before.st_mtime_ns == after.st_mtime_ns)


def vector_profile(frame):
    b, g, r = cv2.split(frame)
    mask = (r > 150) & (g < 95) & (b < 95)
    count = mask.sum(axis=0)
    sums = np.arange(mask.shape[0], dtype=np.float64) @ mask
    out = np.full(mask.shape[1], np.nan)
    np.divide(sums, count, out=out, where=count >= 2)
    return out


def worker(job):
    # Bound the aggregate native-thread count across three read-only workers.
    cv2.setNumThreads(1)
    source, f0, f1, case, folder, capture, method, filename = job
    source = Path(source)
    path = source / folder / filename
    namespace = {"cv2": cv2, "np": np, "F0": f0, "F1": f1,
                 "PX_PER_DEG": 540.0 / 51.0}
    source_path = source / "measure_ripple_spectral.py"
    if fingerprint(source_path)["sha256"] != AUDITED_MEASUREMENT_SHA256:
        raise RuntimeError("Measurement source changed; review it before executing function AST nodes")
    tree = ast.parse(source_path.read_text(encoding="utf-8"))
    tree.body = [n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name in ("profile", "measure")]
    exec(compile(tree, str(source_path), "exec"), namespace)
    original_profile = namespace["profile"]
    probe = cv2.VideoCapture(str(path))
    if not probe.isOpened():
        raise RuntimeError("Cannot open " + str(path))
    metadata = dict(width=int(probe.get(cv2.CAP_PROP_FRAME_WIDTH)),
                    height=int(probe.get(cv2.CAP_PROP_FRAME_HEIGHT)),
                    fps=float(probe.get(cv2.CAP_PROP_FPS)),
                    frame_count=int(probe.get(cv2.CAP_PROP_FRAME_COUNT)))
    probe.release()
    rows = []
    checks = 0
    sampled = {0, 1, 37, 149, 223, 300, 449}

    def observed_profile(frame):
        nonlocal checks
        ys = vector_profile(frame)
        i = len(rows)
        if i in sampled:
            old = original_profile(frame)
            if not np.array_equal(old, ys, equal_nan=True):
                raise AssertionError("Vector profile mismatch " + str(path) + " frame " + str(f0+i))
            checks += 1
        valid = np.isfinite(ys)
        count, width = int(valid.sum()), len(ys)
        row = dict(case=case, method=method, frame_index=f0+i,
                   video_time_s=(f0+i)/metadata["fps"],
                   width=width, height=frame.shape[0], valid_columns=count,
                   valid_fraction=count/width, ripple_used=count >= .3*width,
                   detrended_used=count >= .4*width)
        if count:
            x, y = np.flatnonzero(valid).astype(float), ys[valid]
            row.update(support_x_min=int(x.min()), support_x_max=int(x.max()),
                       mean_subtracted_rms_px=float(y.std()),
                       percentile_97_minus_3_px=float(np.percentile(y,97)-np.percentile(y,3)))
            if count >= .4*width:
                a,b = np.polyfit(x,y,1)
                residual = y-(a*x+b)
                total, err = np.sum((y-y.mean())**2), np.sum(residual**2)
                row.update(affine_detrended_rms_px=float(np.sqrt(np.mean(residual**2))),
                           fitted_slope_px_per_column=float(a), fitted_intercept_px=float(b),
                           affine_explained_fraction=float(1-err/total) if total>1e-9 else None)
        rows.append(row)
        return ys

    namespace["profile"] = observed_profile
    result = namespace["measure"](str(path), want_spectrum=method == "Raw")
    if len(rows) != f1-f0:
        raise AssertionError("Short decode: " + str(path) + " " + str(len(rows)))
    used = [r for r in rows if r["detrended_used"]]
    ripple_used = [r for r in rows if r["ripple_used"]]
    reference_check = float(np.mean([r["affine_detrended_rms_px"] for r in used]))
    assert reference_check == result["ihr_px"]
    summary = dict(case=case, method=method, directory=folder,
                   capture_directory_label=capture, video=metadata,
                   frames_requested=f1-f0, frames_decoded=len(rows),
                   frames_used_detrended=len(used), frames_used_ripple=len(ripple_used),
                   valid_fraction_min=min(r["valid_fraction"] for r in rows),
                   valid_fraction_mean=float(np.mean([r["valid_fraction"] for r in rows])),
                   original_profile_exact_checks=checks,
                   affine_detrended_mean_rms_px=float(result["ihr_px"]),
                   original_linear_degree_value=float(result["ihr_deg"]),
                   mean_subtracted_mean_rms_px=float(np.mean([r["mean_subtracted_rms_px"] for r in ripple_used])),
                   percentile_97_minus_3_mean_px=float(np.mean([r["percentile_97_minus_3_px"] for r in ripple_used])),
                   temporal_std_of_spatial_rms_px=float(np.std([r["mean_subtracted_rms_px"] for r in ripple_used])),
                   mean_affine_explained_fraction=float(result["s_global"]),
                   original_measure_function_executed=True,
                   file=fingerprint(path))
    if "spec" in result:
        power=result["spec"]
        summary["raw_residual_spectrum"]=dict(mean_power=power.tolist(),
            modes_1_to_3_fraction=float(power[1:4].sum()/power[1:].sum()),
            grid_points=256, interpolation="linear, per-frame first-to-last valid column",
            note="FFT modes over the resampled partial-panorama support, not physical full-360 azimuth harmonics.")
    return summary, rows


def parse_args():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--source-root", type=Path, required=True,
                        help="Read-only archive root containing stab_compare and captures* directories")
    parser.add_argument("--output-root", type=Path, required=True,
                        help="Writable destination outside the source archive")
    parser.add_argument("--first-frame", type=int, default=900)
    parser.add_argument("--last-frame-exclusive", type=int, default=1350)
    parser.add_argument("--workers", type=int, default=3)
    parser.add_argument("--inspect-only", action="store_true",
                        help="Only decode fixed sparse frames and write diagnostic PNGs/JSON")
    parser.add_argument("--inspect-frames", type=int, nargs="+", default=[900,1125,1349])
    args = parser.parse_args()
    args.source_root = args.source_root.resolve(strict=True)
    args.output_root = args.output_root.resolve()
    if args.output_root == args.source_root or args.source_root in args.output_root.parents:
        parser.error("output root must not be inside the read-only source archive")
    if not (args.source_root / "stab_compare/measure_ripple_spectral.py").is_file():
        parser.error("source root must contain stab_compare/measure_ripple_spectral.py")
    if args.first_frame < 0 or args.last_frame_exclusive <= args.first_frame or args.workers < 1:
        parser.error("require 0 <= first-frame < last-frame-exclusive and workers >= 1")
    if any(n < 0 for n in args.inspect_frames):
        parser.error("inspect frame indices must be nonnegative")
    return args


def inspect_sparse(source, out, frames):
    """Sparse diagnostics only; a mask diagnostic does not establish purity."""
    cv2.setNumThreads(1)
    out.mkdir(parents=True, exist_ok=True)
    records=[]
    for case, folder, _ in CASES[:2]:
        for method, filename in METHODS:
            path=source/folder/filename
            cap=cv2.VideoCapture(str(path))
            if not cap.isOpened():
                raise RuntimeError("Cannot open " + str(path))
            for n in frames:
                cap.set(cv2.CAP_PROP_POS_FRAMES,n)
                ok,frame=cap.read()
                if not ok:
                    raise RuntimeError("Cannot decode " + str(path) + " frame " + str(n))
                name=f"{case}_{method.replace(' ', '_')}_frame{n}.png"
                if not cv2.imwrite(str(out/name),frame):
                    raise RuntimeError("Cannot write diagnostic PNG")
                b,g,r=cv2.split(frame)
                mask=(r>150)&(g<95)&(b<95)
                count,labels,stats,centroids=cv2.connectedComponentsWithStats(mask.astype(np.uint8),8)
                components=[]
                for j in range(1,count):
                    x,y,w,h,area=[int(v) for v in stats[j]]
                    if area >= 4:
                        components.append(dict(x=x,y=y,width=w,height=h,area_px=area))
                components.sort(key=lambda c:c["area_px"],reverse=True)
                ys=vector_profile(frame); valid=np.isfinite(ys)
                x=np.flatnonzero(valid).astype(float); y=ys[valid]
                a,b=np.polyfit(x,y,1)
                records.append(dict(case=case,method=method,frame_index=n,
                    video_path=path.as_posix(),image=fingerprint(out/name),
                    valid_columns=int(valid.sum()),red_pixels=int(mask.sum()),
                    affine_detrended_rms_px=float(np.sqrt(np.mean((y-(a*x+b))**2))),
                    red_components_area_at_least_4=components))
            cap.release()
    # A post-inspection diagnostic demonstrates the indoor failure. This fixed
    # band is not a validated segmentation rule and is never used in main scores.
    cap=cv2.VideoCapture(str(source/"cam3_horizon/our_stab.mp4"))
    cap.set(cv2.CAP_PROP_POS_FRAMES,1276)
    ok,frame=cap.read();cap.release()
    if not ok:
        raise RuntimeError("Cannot decode Indoor G-locked frame 1276")
    diagnostic_path=out/"Indoor_G-locked_frame1276.png"
    if not cv2.imwrite(str(diagnostic_path),frame):
        raise RuntimeError("Cannot write indoor diagnostic PNG")
    b,g,r=cv2.split(frame); mask=(r>150)&(g<95)&(b<95)
    restricted=mask.copy();restricted[:250,:]=False;restricted[291:,:]=False
    def mask_rms(selected):
        count=selected.sum(axis=0)
        values=np.arange(selected.shape[0],dtype=np.float64)@selected
        valid=count>=2;x=np.flatnonzero(valid).astype(float)
        y=values[valid]/count[valid];a,b=np.polyfit(x,y,1)
        return dict(valid_columns=int(valid.sum()),
            mean_subtracted_rms_px=float(y.std()),
            affine_detrended_rms_px=float(np.sqrt(np.mean((y-(a*x+b))**2))))
    outside=mask & ~restricted
    locations=np.argwhere(outside)
    indoor=dict(case="Indoor",method="G-locked",frame_index=1276,
        image=fingerprint(diagnostic_path),full_mask=mask_rms(mask),
        diagnostic_band=mask_rms(restricted),diagnostic_band_rows_inclusive=[250,290],
        excluded_red_pixels=int(outside.sum()),excluded_columns=int(outside.any(axis=0).sum()),
        excluded_row_min=int(locations[:,0].min()),excluded_row_max=int(locations[:,0].max()),
        interpretation="Post-inspection band diagnostic only: demonstrates unrelated red scene pixels contaminate the original profile; not a corrected evaluation protocol.")
    report=dict(schema_version=1,script=fingerprint(Path(__file__)),frames=frames,
                scope="Fixed sparse outdoor inspection; no entire-video hash or measurement repeated; components are diagnostics, not a validated separator of paint and scene objects.",
                records=records,indoor_contamination_diagnostic=indoor)
    (out/"outdoor_sparse_inspection.json").write_text(json.dumps(report,indent=2,allow_nan=False)+"\n",encoding="utf-8")
    print("DONE",len(records),"sparse outdoor frames",out,flush=True)


def main():
    args=parse_args()
    source=args.source_root/"stab_compare"
    out=args.output_root
    f0,f1=args.first_frame,args.last_frame_exclusive
    if args.inspect_only:
        inspect_sparse(source,out,args.inspect_frames)
        return
    jobs=[(str(source),f0,f1,case,folder,capture,method,name) for case,folder,capture in CASES for method,name in METHODS]
    results=[]; all_rows=[]
    with ProcessPoolExecutor(max_workers=args.workers) as pool:
        futures={pool.submit(worker,j):j for j in jobs}
        for future in as_completed(futures):
            summary,rows=future.result();results.append(summary);all_rows.extend(rows)
            print(summary["case"],summary["method"],"RMSpx",summary["affine_detrended_mean_rms_px"],
                  "legacydeg",summary["original_linear_degree_value"],flush=True)
    order={(j[3],j[6]):i for i,j in enumerate(jobs)}
    results.sort(key=lambda r:order[(r["case"],r["method"])])
    all_rows.sort(key=lambda r:(order[(r["case"],r["method"])],r["frame_index"]))
    records=[fingerprint(source/name) for name in
             ("measure_ripple.py","measure_ripple_spectral.py","measure_horizon.py",
              "gen_our_videos.py","of_stabilize.py","filters.py","compile_stab_excel.py",
              "gen_outdoor_ripple_fig.py")]
    records += [fingerprint(source.parent/cap/"imu/imu_data.csv") for _,_,cap in CASES]
    records += [fingerprint(p) for p in sorted(source.glob("**/metrics*.json"))]
    matched={}
    for case,_,_ in CASES:
        sets=[{r["frame_index"] for r in all_rows if r["case"]==case and r["method"]==m and r["detrended_used"]} for m,_ in METHODS]
        matched[case]=dict(common_frame_count=len(set.intersection(*sets)),
                           note="Frame indices are matched; valid column supports remain method-specific.")
    report=dict(schema_version=1,created_at_utc=datetime.now(timezone.utc).isoformat(),
                audit_scope="Existing encoded synthetic-reference videos; no renderer, stabilizer or original archive-writing main executed.",
                script=fingerprint(Path(__file__)),
                software=dict(python=platform.python_version(),numpy=np.__version__,opencv=cv2.__version__),
                protocol=dict(first_frame=f0,last_frame_exclusive=f1,stride=1,
                              nominal_video_interval_s_at_30fps=[f0/30,f1/30],
                              color_threshold_bgr="R>150, G<95, B<95; at least 2 red pixels per column",
                              valid_support="All qualifying red pixels; no component isolation or independent horizon annotation",
                              ripple_minimum_fraction=.3,detrended_minimum_fraction=.4,
                              aggregation="Arithmetic mean of per-frame spatial RMS, not RMS across all spatiotemporal samples",
                              degree_conversion_legacy_only="RMSpx/(540/51); not an independently validated angular calibration"),
                results=results,matched_frames=matched,input_files=records,
                interpretive_verdict="Reproducible synthetic-reference/model-consistency diagnostic; not independent physical leveling accuracy or evidence against arbitrary global warps.")
    out.mkdir(parents=True,exist_ok=True)
    csv_path=out/"horizon_per_frame.csv"
    fields=[]
    for r in all_rows:
        for k in r:
            if k not in fields: fields.append(k)
    with csv_path.open("w",newline="",encoding="utf-8") as f:
        writer=csv.DictWriter(f,fieldnames=fields);writer.writeheader();writer.writerows(all_rows)
    report["per_frame_csv"]=fingerprint(csv_path)
    (out/"horizon_audit.json").write_text(json.dumps(report,indent=2,allow_nan=False)+"\n",encoding="utf-8")
    print("DONE",len(all_rows),"rows",out,flush=True)


if __name__=="__main__": main()
