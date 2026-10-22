"""Audit saved stitching outputs; never run a renderer/network or alter inputs.

Requires numpy, opencv-python, scikit-image. The legacy evaluator's pixel
formula, thresholds and method-specific masks are deliberately retained.
Matching case/pair identities does NOT make masks, scale or information equal.
Writes derived JSON/CSV only under --output (default: this script's directory).
"""
import argparse
import csv
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import platform

import cv2
import numpy as np
import skimage
from skimage.metrics import peak_signal_noise_ratio, structural_similarity


def digest(path):
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def evaluate(a, b, mask):
    if int(mask.sum()) < 300:
        return None
    ys, xs = np.where(mask)
    y0, y1, x0, x1 = ys.min(), ys.max() + 1, xs.min(), xs.max() + 1
    a, b, mask = a[y0:y1, x0:x1], b[y0:y1, x0:x1], mask[y0:y1, x0:x1]
    if min(a.shape) < 7:
        return None
    aa, bb = cv2.GaussianBlur(a, (0, 0), 2.0), cv2.GaussianBlur(b, (0, 0), 2.0)
    _, sr = structural_similarity(a, b, data_range=255, full=True)
    _, sb = structural_similarity(aa, bb, data_range=255, full=True)
    return dict(rawP=float(peak_signal_noise_ratio(a[mask], b[mask], data_range=255)),
                strP=float(peak_signal_noise_ratio(aa[mask], bb[mask], data_range=255)),
                rawS=float(sr[mask].mean()), strS=float(sb[mask].mean()))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path,
                        default=Path("C:/SVNProjects/IMU_Stabilize_v40/DL_Comparison"))
    parser.add_argument("--output", type=Path, default=Path(__file__).resolve().parent)
    args = parser.parse_args()
    root, output = args.source.resolve(), args.output.resolve()
    if output == root or root in output.parents:
        raise SystemExit("Output must be outside the source evaluation tree")
    used = {}

    def record(path):
        path = path.resolve()
        if path not in used:
            used[path] = dict(path=path.as_posix(), bytes=path.stat().st_size,
                              sha256=digest(path))
        return path

    def load_image(path, gray=False):
        if not path.is_file():
            return None
        image = cv2.imread(str(record(path)), cv2.IMREAD_GRAYSCALE if gray else cv2.IMREAD_COLOR)
        if image is None:
            raise ValueError("Cannot decode " + str(path))
        return image

    manifest = json.loads(record(root / "results/eo_manifest.json").read_text())
    homo = json.loads(record(root / "results/homo_metrics.json").read_text())
    homo = {(r["case"], r["pair"]): r for r in homo["per_pair"]}
    cases = sorted(c["name"] for c in manifest)
    targets = [(case, pair) for case in cases for pair in ("pair_01", "pair_12")]
    rows = []
    for method in ("G-locked", "UDIS++", "StabStitch++", "SIFT+homography"):
        for case, pair in targets:
            row = dict(method=method, case=case, pair=pair, status="missing_output")
            i, j = int(pair[-2]), int(pair[-1])
            if method == "SIFT+homography":
                r = homo.get((case, pair))
                if r:
                    row.update({k: r[k] for k in ("status", "overlap_px", "overlap", "distant") if k in r})
                    row["metric_source"] = "saved in-memory-mask JSON; JPEG masks were not reconstructed"
            else:
                masks = None
                if method == "G-locked":
                    folder = root / "data/glock_runs" / ("strips_" + case + "_stab")
                    a_files, b_files = sorted(folder.glob("*strip_cam%d_*.bmp" % i)), sorted(folder.glob("*strip_cam%d_*.bmp" % j))
                    if len(a_files) != 1 or len(b_files) != 1:
                        row["status"] = "missing_or_ambiguous_strip"
                        rows.append(row)
                        continue
                    a, b = load_image(a_files[0]), load_image(b_files[0])
                elif method == "UDIS++":
                    folder = root / "data/udis_pairs" / case / pair
                    a, b = load_image(folder / "warp1.jpg"), load_image(folder / "warp2.jpg")
                    masks = [load_image(folder / ("mask%d.jpg" % k), True) for k in (1, 2)]
                else:
                    folder = root / "results/stab_warps" / case
                    a, b = load_image(folder / ("warp%d.png" % i)), load_image(folder / ("warp%d.png" % j))
                    masks = [load_image(folder / ("mask%d.png" % k), True) for k in (i, j)]
                if a is None or b is None or (masks is not None and any(m is None for m in masks)):
                    rows.append(row)
                    continue
                if a.shape != b.shape:
                    raise ValueError("Warp canvas mismatch: " + str(row))
                a, b = [cv2.cvtColor(x, cv2.COLOR_BGR2GRAY).astype(np.float64) for x in (a, b)]
                mask = (a > 3) & (b > 3) if masks is None else (masks[0] > 127) & (masks[1] > 127)
                mask = cv2.erode(mask.astype(np.uint8), np.ones((5, 5), np.uint8)).astype(bool)
                row.update(canvas_height=int(a.shape[0]), canvas_width=int(a.shape[1]), overlap_px=int(mask.sum()))
                whole = evaluate(a, b, mask)
                if whole is None:
                    row["status"] = "insufficient_overlap"
                else:
                    row["status"], row["overlap"] = "ok", whole
                    ys = np.where(mask.any(axis=1))[0]
                    top = mask.copy()
                    top[ys.min() + (ys.max() + 1 - ys.min()) // 3:, :] = False
                    row["distant"] = evaluate(a, b, top)
            rows.append(row)
        print(method + " complete", flush=True)

    def summary(keys):
        result = {}
        for method in sorted({r["method"] for r in rows}):
            selected = [r for r in rows if r["method"] == method and (r["case"], r["pair"]) in keys]
            entry = dict(target_count=len(keys), success_count=sum(r["status"] == "ok" for r in selected),
                         failures=[dict(case=r["case"], pair=r["pair"], status=r["status"]) for r in selected if r["status"] != "ok"])
            for region in ("overlap", "distant"):
                metrics = [r[region] for r in selected if r["status"] == "ok" and r.get(region)]
                entry[region] = dict(count=len(metrics), mean={k: float(np.mean([m[k] for m in metrics])) if metrics else None
                                                             for k in ("rawP", "strP", "rawS", "strS")})
            result[method] = entry
        return result

    common = set(targets)
    for r in rows:
        if r["status"] != "ok" or not r.get("overlap"):
            common.discard((r["case"], r["pair"]))
    capture_hashes = {}
    for c in manifest:
        hashes = [used[record(Path(c["raw"][str(i)]))]["sha256"] for i in range(3)]
        capture_hashes.setdefault(tuple(hashes), []).append(c["name"])
    for name in ("compile_excel.py", "prep_inputs.py", "run_udis.py", "run_stab_dump.py", "run_homo.py", "run_glock.py"):
        record(root / "scripts" / name)
    for name in ("stitching_comparison.xlsx", "stitching_comparison_v2.xlsx"):
        record(root / "results" / name)
    report = dict(schema_version=1, evaluated_at_utc=datetime.now(timezone.utc).isoformat(), source_root=root.as_posix(),
                  script_sha256=digest(Path(__file__)),
                  software=dict(python=platform.python_version(), numpy=np.__version__, opencv=cv2.__version__, skimage=skimage.__version__),
                  protocol="Legacy pre-blend warped-view consistency; Gaussian sigma2; grayscale; eroded5x5 method-specific mask; unweighted arithmetic seam means.",
                  limits=["Matching identities does not equalize output scale, validity masks, field of view, JPEG compression or calibration access.",
                          "Top third is an image-coordinate region, not verified distant geometry.",
                          "StabStitch++ used 16 repeated static frames of cameras0..2; this is not video-stability evaluation.",
                          "SIFT failures remain explicit in all-target results; common-success statistics are conditional on its success.",
                          "The captures are six named calibration cases, not necessarily independent scenes or acquisitions.",
                          "No neural network/renderer was rerun. G/UDIS/Stab metrics recomputed from archived outputs; SIFT metrics copied from saved JSON using original in-memory masks."],
                  targets=[dict(case=c, pair=p) for c, p in targets], all_target_summary=summary(set(targets)),
                  common_success_targets=[dict(case=c, pair=p) for c, p in sorted(common)],
                  common_success_summary=summary(common),
                  identical_cam0_cam1_cam2_capture_groups=[v for v in capture_hashes.values() if len(v) > 1],
                  inputs=[used[p] for p in sorted(used)], rows=rows)
    output.mkdir(parents=True, exist_ok=True)
    (output / "legacy_overlap_reanalysis.json").write_text(json.dumps(report, indent=2, allow_nan=False) + "\n", encoding="utf-8")
    fields = ["method", "case", "pair", "status", "canvas_height", "canvas_width", "overlap_px"] + [r + "_" + k for r in ("overlap", "distant") for k in ("rawP", "strP", "rawS", "strS")]
    with (output / "legacy_overlap_per_seam.csv").open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        for r in rows:
            flat = {k: r.get(k) for k in fields[:7]}
            for region in ("overlap", "distant"):
                for k, value in (r.get(region) or {}).items():
                    flat[region + "_" + k] = value
            writer.writerow(flat)
    print(json.dumps({"all_targets": report["all_target_summary"], "common_success": report["common_success_summary"],
                      "duplicate_capture_groups": report["identical_cam0_cam1_cam2_capture_groups"]}, indent=2))


if __name__ == "__main__":
    main()
