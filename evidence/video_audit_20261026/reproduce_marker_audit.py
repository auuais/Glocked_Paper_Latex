"""Reproduce saved-video ArUco statistics without writing to the source archive.

Requires Python, OpenCV-contrib (aruco), and NumPy. The original audit used
Python 3.9.6, OpenCV 4.8.0, and NumPy 1.25.2.

Example from any directory:
  python reproduce_marker_audit.py --source-root E:/D_Folder/download/test \
    --output-dir C:/work/marker-recompute

Defaults reproduce [900,1350) and [150,600), in zero-based encoded frames.
Supply repeated --interval F0:F1 arguments to select other windows.
"""
import sys
sys.dont_write_bytecode = True
import argparse, csv, hashlib, importlib.util, json, math, pathlib, platform, time
import cv2
import numpy as np

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--source-root', required=True, type=pathlib.Path)
parser.add_argument('--output-dir', required=True, type=pathlib.Path)
parser.add_argument('--interval', action='append', help='zero-based F0:F1, end exclusive; repeatable')
args = parser.parse_args()
ROOT = args.source_root.resolve(strict=True)
OUT = args.output_dir.resolve()
if OUT == ROOT or ROOT in OUT.parents:
    parser.error('--output-dir must be outside --source-root; the archive is read-only')
intervals = []
for value in args.interval or ['900:1350', '150:600']:
    try:
        f0, f1 = map(int, value.split(':'))
    except ValueError:
        parser.error('each --interval must be F0:F1')
    if not 0 <= f0 < f1:
        parser.error('interval must satisfy 0 <= F0 < F1')
    if (f0, f1) in intervals:
        parser.error('duplicate intervals are not allowed')
    intervals.append((f0, f1))
OUT.mkdir(parents=True, exist_ok=True)
SCRIPT = ROOT/'stab_compare/measure_aruco.py'
spec = importlib.util.spec_from_file_location('archived_measure_aruco', SCRIPT)
mod = importlib.util.module_from_spec(spec)
# The archived module parses its own positional argv at import time.
# Preserve our CLI arguments while importing it with only its filename.
cli_argv = sys.argv[:]
try:
    sys.argv = [str(SCRIPT)]
    spec.loader.exec_module(mod)
finally:
    sys.argv = cli_argv
orig_detect = mod.detect
fields = ['segment', 'method', 'frame_index', 'ids_json', 'selected_id',
          'angle_deg', 'center_x_px', 'center_y_px', 'corners_json',
          'corner_refinement_method', 'gray_sha256']
records = []
results = []

def numeric_summary(rows):
    a = np.asarray([r['angle_deg'] for r in rows],dtype=np.float64)
    xs = np.asarray([r['center_x_px'] for r in rows],dtype=np.float32)
    ys = np.asarray([r['center_y_px'] for r in rows],dtype=np.float32)
    return dict(n=len(a), angle_std_deg=float(a.std()), angle_mean_deg=float(a.mean()),
                angle_min_deg=float(a.min()), angle_max_deg=float(a.max()),
                y_std_px=float(ys.std()), x_std_px=float(xs.std())) if len(a) else {'n':0}

for f0,f1 in intervals:
    mod.F0, mod.F1 = f0,f1
    segment=f'{f0}:{f1}'
    by_method={}
    for filename,label in mod.VIDS:
        method=filename[:-4]
        current=[]
        def audited_detect(gray):
            cor,ids=orig_detect(gray)
            row=dict(segment=segment,method=method,frame_index=f0+len(current),
                     ids_json=json.dumps(ids.flatten().tolist()) if ids is not None else '[]',
                     selected_id='',angle_deg='',center_x_px='',center_y_px='',corners_json='[]',
                     corner_refinement_method=int(cv2.aruco.DetectorParameters().cornerRefinementMethod),
                     gray_sha256=hashlib.sha256(gray.tobytes()).hexdigest())
            if ids is not None and len(ids):
                c=cor[0][0]; e1=c[1]-c[0]; e2=c[2]-c[3]
                angle=(math.degrees(math.atan2(e1[1],e1[0]))+math.degrees(math.atan2(e2[1],e2[0])))/2
                row.update(selected_id=int(ids[0][0]),angle_deg=(angle+45)%90-45,
                           center_x_px=float(c[:,0].mean()),center_y_px=float(c[:,1].mean()),
                           corners_json=json.dumps(c.tolist()))
            current.append(row)
            return cor,ids
        mod.detect=audited_detect
        started=time.monotonic()
        exact=mod.measure(str(ROOT/'stab_compare/cam3_in'/filename))
        valid=[r for r in current if r['selected_id']!='']
        selected_ids=sorted(set(r['selected_id'] for r in valid))
        summary=numeric_summary(valid)
        assert summary['n']==exact['n']
        assert summary['angle_std_deg']==exact['astd']
        results.append(dict(segment=segment,method=method,frames_decoded=len(current),
            exact_archived_measure=exact,summary=summary,selected_ids=selected_ids,
            missing_frame_indices=[r['frame_index'] for r in current if r['selected_id']==''],
            non15_frame_indices=[r['frame_index'] for r in valid if r['selected_id']!=15],
            multiple_marker_frame_indices=[r['frame_index'] for r in current if len(json.loads(r['ids_json']))>1]))
        records.extend(current);by_method[method]=valid
        print(json.dumps(results[-1]),flush=True)
        print('elapsed_seconds',round(time.monotonic()-started,2),flush=True)
    common=set.intersection(*[set(r['frame_index'] for r in rows if r['selected_id']==15) for rows in by_method.values()])
    results.append(dict(segment=segment,matched_id15_frames=len(common),matched_frame_indices=sorted(common),
        methods={m:numeric_summary([r for r in rows if r['frame_index'] in common and r['selected_id']==15]) for m,rows in by_method.items()}))

matched = {r['segment']:set(r['matched_frame_indices']) for r in results if 'matched_id15_frames' in r}
means = {(r['segment'],method):s['angle_mean_deg'] for r in results if 'matched_id15_frames' in r for method,s in r['methods'].items()}
for row in records:
    row['nominal_encoded_time_s'] = row['frame_index'] / 30.0
    row['paired_common_id15'] = int(row['frame_index'] in matched[row['segment']])
    row['paired_centered_angle_deg'] = row['angle_deg']-means[row['segment'],row['method']] if row['paired_common_id15'] else ''
fields += ['nominal_encoded_time_s','paired_common_id15','paired_centered_angle_deg']
with (OUT/'marker_detections.csv').open('w',newline='',encoding='utf-8') as f:
    w=csv.DictWriter(f,fieldnames=fields);w.writeheader();w.writerows(records)
params=cv2.aruco.DetectorParameters()
default_params={k:getattr(params,k) for k in dir(params) if not k.startswith('_') and isinstance(getattr(params,k),(str,int,float,bool))}
payload=dict(environment=dict(python=sys.version,platform=platform.platform(),opencv=cv2.__version__,numpy=np.__version__),
    command=cli_argv,source_root=str(ROOT),output_dir=str(OUT),source=str(SCRIPT),source_sha256=hashlib.sha256(SCRIPT.read_bytes()).hexdigest(),
    script_sha256=hashlib.sha256(pathlib.Path(__file__).read_bytes()).hexdigest(),
    detector_parameters=default_params,results=results,
    detections_csv_sha256=hashlib.sha256((OUT/'marker_detections.csv').read_bytes()).hexdigest())
(OUT/'marker_recompute.json').write_text(json.dumps(payload,indent=2)+'\n',encoding='utf-8')
print('COMPLETE',len(records),'frame records',flush=True)
