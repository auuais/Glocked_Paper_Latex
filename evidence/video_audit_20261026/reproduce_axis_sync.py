"""Reproduce archived optical-flow/gyro alignment without writing to the archive.

Requires Python 3.9+, numpy, pandas, and OpenCV. Versions are in filter_audit.json.
All source/video/CSV hashes are checked before the reviewed track() function is
AST-selected; calib_axis.py top-level code is never executed. This is an offline
in-sample fit, not physical latency measurement or independent attitude accuracy.
"""
import argparse
import ast
import hashlib
import json
import math
import os
import platform
import sys
from pathlib import Path
sys.dont_write_bytecode = True
import cv2
import numpy as np
import pandas as pd
cv2.setNumThreads(2)

def digest(path):
    h = hashlib.sha256()
    with path.open('rb') as stream:
        for block in iter(lambda: stream.read(1048576), b''):
            h.update(block)
    return h.hexdigest()


def checked_paths(expected):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source', required=True, type=Path,
                        help='Read-only archived test directory containing captures*/ and stab_compare/.')
    parser.add_argument('--output', required=True, type=Path,
                        help='New output directory outside the source archive; existing files are refused.')
    args = parser.parse_args()
    source = args.source.resolve(strict=True)
    output = args.output.resolve()
    if output == source or source in output.parents:
        parser.error('--output must be outside --source; the archive is read-only')
    if output.exists() and any(output.iterdir()):
        parser.error('--output must be absent or empty; existing results are preserved')
    for relative, sha256 in expected.items():
        path = source / relative
        actual = digest(path)
        if actual != sha256:
            parser.error('Audited source hash mismatch for ' + relative + ': ' + actual)
    output.mkdir(parents=True, exist_ok=True)
    return source, output

EXPECTED_SHA256 = {'stab_compare/calib_axis.py': '7573c68436502d42d7247ab4cbd8747070e5d4e9775081de16d1225c00129056', 'stab_compare/unstab.mp4': 'f89f1646605a309be556c2223b32c071f2566470c946fe200cfc7bff483b351e', 'captures6/imu/imu_data.csv': '309e986a5f34f86ff05091e33f03f4c3bb6256f7a86d8903e079e126bb90a4ed', 'stab_compare/cam3_in/unstab.mp4': '57cecb6cd06db4514df7fad0c50d55735c8f407a30e08af8679eafbdce2494f7', 'captures/imu/imu_data.csv': 'e9458471213fb158a439e2bb43dd206a52c4214f0883d1c004acca6ad65a3079', 'stab_compare/cam3_c5/unstab.mp4': '59bc1f3be3832a0c4ed07653fc9fcc69cba336eee529e62438a54a2d44890367', 'captures5/imu/imu_data.csv': '35e86040f7d5a961cc33bb42b61b8afddcba34bbde3b790cbeaeb7e3009e5557'}
ROOT, OUT = checked_paths(EXPECTED_SHA256)
src = ROOT/'stab_compare/calib_axis.py'
tree = ast.parse(src.read_text(encoding='utf-8'))
functions = [node for node in tree.body if isinstance(node, ast.FunctionDef) and node.name == 'track']
if len(functions) != 1:
    raise RuntimeError('Expected exactly one audited track() function')
ns = dict(cv2=cv2, np=np, pd=pd, math=math, os=os, F0=1, F1=900, NSTRIP=4, MARGIN=.12)
exec(compile(ast.Module(body=functions, type_ignores=[]), str(src), 'exec'), ns)
DRIFT = (-.002843, .000743, -.000966)
def r2(y,yh):
 ss=((y-y.mean())**2).sum()
 return float(1-((y-yh)**2).sum()/ss) if ss>0 else 0.
results=[]
for label,vname,folder in [('Outdoor-1-default','unstab.mp4','captures6'),('Indoor','cam3_in/unstab.mp4','captures'),('Outdoor-2','cam3_c5/unstab.mp4','captures5')]:
 video=ROOT/'stab_compare'/vname;imu_path=ROOT/folder/'imu/imu_data.csv'
 cap=cv2.VideoCapture(str(video));meta=dict(width=int(cap.get(cv2.CAP_PROP_FRAME_WIDTH)),height=int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT)),fps=float(cap.get(cv2.CAP_PROP_FPS)),frames=int(cap.get(cv2.CAP_PROP_FRAME_COUNT)));cap.release()
 dx,dy,da=ns['track'](str(video));imu=pd.read_csv(imu_path)
 ts=imu.Timestamp_ms.values.astype(float)/1000;dt=np.clip(np.diff(ts,prepend=ts[0]),0,.05)
 Gcum=[np.cumsum((imu[k].values-d)*dt) for k,d in zip(['Gyro_X','Gyro_Y','Gyro_Z'],DRIFT)]
 targets={'roll_da':da,'pitch_dy_over_19.6':np.radians(dy/19.6),'yaw_dx_over_19.6':np.radians(dx/19.6)}
 rows=[];best=None
 for off in range(20,75):
  ft=(np.arange(1,900)+off)*(1000/30)/1000
  gi=[np.interp(ft,ts,g) for g in Gcum]
  G=np.column_stack([np.diff(g,prepend=g[0]) for g in gi]);total=0;axes={}
  for name,y in targets.items():
   m,_,_,_=np.linalg.lstsq(G,y,rcond=None);q=r2(y,G@m);total+=q
   axes[name]=dict(coefficients_gyro_xyz=m.tolist(),r_squared=q)
  rows.append(dict(offset_frames=off,total_r_squared=total,**{k+'_r_squared':v['r_squared'] for k,v in axes.items()}))
  if best is None or total>best['total_r_squared']:best=dict(offset_frames=off,total_r_squared=total,axes=axes)
 pd.DataFrame(dict(pair_index=np.arange(1,len(da)+1),dx_px=dx,dy_px=dy,da_rad=da)).to_csv(OUT/(folder+'_axis_track.csv'),index=False)
 pd.DataFrame(rows).to_csv(OUT/(folder+'_axis_sync_scan.csv'),index=False)
 rec=dict(label=label,video=str(video),video_sha256=digest(video),video_metadata=meta,imu=str(imu_path),imu_sha256=digest(imu_path),tracked_pairs=len(da),best=best,
     scope='Re-executes unchanged track() with F0=1,F1=900,NSTRIP=4,MARGIN=.12. Fits and selects offset on same frames; no held-out validation.')
 results.append(rec);print(label,json.dumps(best),flush=True)
(OUT/'axis_sync_results.json').write_text(json.dumps(dict(software=dict(python=platform.python_version(),opencv=cv2.__version__,numpy=np.__version__,pandas=pd.__version__),source=str(src),source_sha256=digest(src),script_sha256=digest(Path(__file__)),results=results),indent=2)+'\n')
