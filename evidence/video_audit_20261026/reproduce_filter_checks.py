"""Reproduce the audited offline filter numbers without writing to the archive.

Requires Python 3.9+, numpy and pandas. Verified versions are in filter_audit.json.
Input hashes are checked before executing the reviewed filters.py definitions.
No original generator, figure-save operation, or acquisition script is executed.
"""
import argparse
import hashlib
import importlib.util
import json
import math
from pathlib import Path
import platform
import sys
sys.dont_write_bytecode = True
import numpy as np
import pandas as pd

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

EXPECTED_SHA256 = {'captures/imu/imu_data.csv': 'e9458471213fb158a439e2bb43dd206a52c4214f0883d1c004acca6ad65a3079', 'captures6/imu/imu_data.csv': '309e986a5f34f86ff05091e33f03f4c3bb6256f7a86d8903e079e126bb90a4ed', 'captures5/imu/imu_data.csv': '35e86040f7d5a961cc33bb42b61b8afddcba34bbde3b790cbeaeb7e3009e5557', 'stab_compare/filters.py': 'd32fce1773a7e7b50f452ecea8ffdeb7ed70f21a2de9e261d4c8f5f7f6ca04ca', 'stab_compare/gen_imu_filter_fig.py': 'e57fb28bb5122f59c439feb66e7e822d0268459015276c1e82f79ff21d7915fc', 'stab_compare/grav_eval.py': '5d8295c104625dcdc46b37687db2a41d8491119715afd3440bf77640443c5d7d', 'stab_compare/diag_sync.py': '09a2f1f43cc25845f30e6f269b9a2e5d094471aded88dbb10455f5b0abc5a5ed', 'stab_compare/diag_axis.py': '5891777497341ca906c58e2ea095b2f205ff88a0c593966e1d94c115feb3e613', 'stab_compare/calib_axis.py': '7573c68436502d42d7247ab4cbd8747070e5d4e9775081de16d1225c00129056', 'stab_compare/verify_madgwick.py': 'fd86ca942fbfc4ba5f629cb70385d7b7134ba436b2d20bac11ff5a0b4ebf15ee', 'stab_compare/verify_axis.py': '8d789b2ccc5a40e4acc6337550949c165e7a4edd65f311f469b5a7e5119ceab9', 'stab_compare/compile_stab_excel.py': '948a5c68740a019bbcafeceda13d070a9b6910e2a4794ac0b96347c71a368859', 'stab_compare/gen_our_videos.py': 'f7a1841ceb4c92d02665b6e9d1917976fad0fb244fcf95bc72368ed6fe5de2fb'}
SOURCE, OUT = checked_paths(EXPECTED_SHA256)
spec = importlib.util.spec_from_file_location('audited_filters', SOURCE/'stab_compare/filters.py')
filters = importlib.util.module_from_spec(spec)
spec.loader.exec_module(filters)

def stats(a):
    a=np.asarray(a)
    return dict(n=int(len(a)),mean=float(np.mean(a)),median=float(np.median(a)),
                p95=float(np.percentile(a,95)),max=float(np.max(a)),min=float(np.min(a))) if len(a) else dict(n=0)

result=dict(audit_date='2026-10-26',software=dict(python=platform.python_version(),numpy=np.__version__,pandas=pd.__version__),
            datasets={},sources={})
frames={}
for label,folder in [('Indoor','captures'),('Outdoor-1','captures6'),('Outdoor-2','captures5')]:
    path=SOURCE/folder/'imu/imu_data.csv'
    imu=pd.read_csv(path);frames[label]=imu
    ts=imu.Timestamp_ms.values.astype(float);dts=np.diff(ts)
    gx=imu.Gyro_X.values-filters.GYRO_DRIFT[0]
    gy=imu.Gyro_Y.values-filters.GYRO_DRIFT[1]
    gz=imu.Gyro_Z.values-filters.GYRO_DRIFT[2]
    gm=np.sqrt(gx*gx+gy*gy+gz*gz)
    ax=-imu.Accel_Y.values;ay=-imu.Accel_X.values;az=-imu.Accel_Z.values
    r_acc=-np.degrees(np.arctan2(ay,az));p_acc=np.degrees(np.arctan2(-ax,np.hypot(ay,az)))
    static=gm<.06; recent=np.zeros(len(imu),bool);last=-10**9
    for i,v in enumerate(gm):
        if v>.5:last=i
        if 0<i-last<400:recent[i]=True
    pm=static&recent
    r,p=filters.madgwick_rp_cam(imu,beta=.1,smooth_win=5)
    ra,pa,gate=filters.madgwick_rp_cam_adaptive(imu,beta_max=.1,tol=.08,smooth_win=5,return_gate=True)
    mag=np.sqrt(ax*ax+ay*ay+az*az);amagdev=np.abs(mag/np.median(mag)-1)
    rec=dict(source=str(path),rows=len(imu),timestamp_first_ms=float(ts[0]),timestamp_last_ms=float(ts[-1]),
             timestamp_duration_s=float((ts[-1]-ts[0])/1000),median_dt_ms=float(np.median(dts)),
             median_implied_hz=float(1000/np.median(dts)),row_rate_hz=float((len(ts)-1)*1000/(ts[-1]-ts[0])),
             dt_nonpositive=int((dts<=0).sum()),dt_ge100ms=int((dts>=100).sum()),dt_ms=stats(dts),
             static_samples=int(static.sum()),post_motion_static_samples=int(pm.sum()),
             accel_magnitude_median=float(np.median(mag)),accel_relative_deviation=stats(amagdev),adaptive_gate=stats(gate),filters={})
    for name,rr,pp in [('fixed_beta_0.1',r,p),('adaptive_beta_0.1_tol_0.08',ra,pa)]:
        rec['filters'][name]=dict(roll_abs_difference_all=stats(np.abs(rr-r_acc)),
            roll_abs_difference_static=stats(np.abs(rr-r_acc)[static]),pitch_abs_difference_static=stats(np.abs(pp-p_acc)[static]),
            roll_abs_difference_post_motion_static=stats(np.abs(rr-r_acc)[pm]),
            roll_abs_difference_reported_post_motion=stats(np.abs(rr-r_acc)[pm if pm.any() else static]),
            post_motion_fallback_to_all_static=not bool(pm.any()),finite=bool(np.isfinite(rr).all() and np.isfinite(pp).all()))
    rec['timestamp_zero_deltas'] = int((dts == 0).sum())
    rec['timestamp_negative_deltas'] = int((dts < 0).sum())
    rec['effective_filter_dt_sum_s'] = float(np.where((dts > 0) & (dts < 100), dts/1000, 1/400).sum())
    rec['max_bias_corrected_gyro_magnitude_rad_s'] = float(gm.max())
    rec['reported_static_mean_rounds_to_deg'] = round(rec['filters']['fixed_beta_0.1']['roll_abs_difference_static']['mean'], 2)
    result['datasets'][label]=rec
    pd.DataFrame(dict(timestamp_ms=ts,elapsed_s=(ts-ts[0])/1000,gyro_mag_rad_s=gm,static=static,
        post_motion_static=pm,accel_roll_deg=r_acc,accel_pitch_deg=p_acc,fixed_roll_deg=r,fixed_pitch_deg=p,
        adaptive_roll_deg=ra,adaptive_pitch_deg=pa,adaptive_gate=gate)).to_csv(OUT/(folder+'_filter_traces.csv'),index=False)
    result['sources'][str(path)]=dict(bytes=path.stat().st_size,sha256=digest(path))
    print(label,'rows',len(imu),'static',int(static.sum()),'fixed roll mean',rec['filters']['fixed_beta_0.1']['roll_abs_difference_static']['mean'],flush=True)

# Exact numerical operations of gen_imu_filter_fig.py, without its figure overwrite.
imu=frames['Outdoor-1'];ts=imu.Timestamp_ms.values.astype(float)/1000;ts=ts-ts[0]
dt=np.r_[np.median(np.diff(ts)),np.diff(ts)];fs=1/np.median(np.diff(ts))
acc=np.degrees(np.arctan2(imu.Accel_X.values,-imu.Accel_Z.values))
gyro=acc[0]+np.degrees(np.cumsum(-imu.Gyro_Y.values*dt))
mad,_=filters.madgwick_rp(imu,beta=.05,smooth_win=5)
comp,_=filters.comp_fix_rp(imu,alpha=.98)
sm=np.convolve(acc,np.ones(25)/25,'same')
rate=np.convolve(np.abs(np.r_[0.,np.diff(sm)])*fs,np.ones(60)/60,'same')
peak=int(np.argmax(rate[300:-300])+300);tpeak=float(ts[peak]);mask=(ts>=tpeak-.8)&(ts<=tpeak+.8)
curve=[];lagresults={}
for label,sig in [('native_axis_madgwick_beta0.05_centered5',mad),('corrected_complementary_alpha0.98',comp)]:
    s=sig[mask]-np.mean(sig[mask]);r=acc[mask]-np.mean(acc[mask]);n=len(s)
    best=(-1e99,0);signedbest=(-2.,0)
    for lag in range(-int(.08*fs),int(.08*fs)):
        if lag>=0:x,y=s[lag:],r[:n-lag]
        else:x,y=s[:n+lag],r[-lag:]
        dot=float(np.dot(x,y));pear=float(np.corrcoef(x,y)[0,1])
        curve.append(dict(filter=label,lag_samples=lag,lag_ms=1000*lag/fs,overlap_samples=len(x),demeaned_dot=dot,overlap_pearson=pear))
        if lag>=0 and dot>best[0]:best=(dot,lag)
        if pear>signedbest[0]:signedbest=(pear,lag)
    lagresults[label]=dict(original_positive_dot_lag_samples=best[1],original_positive_dot_lag_ms=1000*best[1]/fs,
        original_positive_dot_score=best[0],signed_pearson_peak_samples=signedbest[1],signed_pearson_peak_ms=1000*signedbest[1]/fs,signed_pearson_peak=signedbest[0])
    shift = best[1]
    selected_ts = ts[mask]
    separation = (selected_ts[shift:] - selected_ts[:-shift])*1000 if shift else np.zeros(len(selected_ts))
    lagresults[label]['timestamp_separation_for_same_index_shift_ms'] = stats(separation)
result['legacy_figure_reproduction']=dict(filter_source='madgwick_rp beta=0.05,smooth_win=5; comp_fix_rp alpha=0.98',
    fs_from_median_timestamp_hz=float(fs),transient_peak_index=peak,transient_peak_elapsed_s=tpeak,
    transient_window_s=[tpeak-.8,tpeak+.8],transient_samples=int(mask.sum()),lag_search_positive_samples=[0,int(.08*fs)-1],
    results=lagresults,gyro_final_difference_deg=float((gyro-mad)[-1]),gyro_difference_over_duration_deg_s=float((gyro-mad)[-1]/ts[-1]))
pd.DataFrame(curve).to_csv(OUT/'filter_lag_signed_curve.csv',index=False)
pd.DataFrame(dict(elapsed_s=ts,accel_roll_deg=acc,native_madgwick_roll_deg=mad,corrected_comp_roll_deg=comp,
                 gyro_only_roll_deg=gyro,selected_transient=mask)).to_csv(OUT/'legacy_filter_figure_traces.csv',index=False)

transient = pd.DataFrame(dict(sample_index=np.flatnonzero(mask),
    timestamp_ms=imu.Timestamp_ms.values[mask], elapsed_s=ts[mask], accel_roll_deg=acc[mask],
    native_madgwick_roll_deg=mad[mask], corrected_comp_roll_deg=comp[mask], gyro_only_roll_deg=gyro[mask]))
transient.to_csv(OUT/'selected_filter_transient.csv', index=False)

for name in ['filters.py','gen_imu_filter_fig.py','grav_eval.py','diag_sync.py','diag_axis.py','calib_axis.py','verify_madgwick.py','verify_axis.py','compile_stab_excel.py','gen_our_videos.py']:
    p=SOURCE/'stab_compare'/name;result['sources'][str(p)]=dict(bytes=p.stat().st_size,sha256=digest(p))
result['reproduction_script']=dict(path=str(Path(__file__)),sha256=digest(Path(__file__)))
(OUT/'filter_numeric_results.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
print(json.dumps(result['legacy_figure_reproduction'],indent=2),flush=True)
