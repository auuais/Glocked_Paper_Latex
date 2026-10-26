# Recovered video and inertial evidence

Audited 26 October 2026 from the user-supplied directory
`E:/D_Folder/download/test`. This directory is not a Git repository. The audit
read the original files without modifying them; it did not run an FPGA test
or regenerate the saved videos. Raw media and full acquisition logs remain
outside this public paper repository.

## Findings and manuscript treatment

| Original claim | Recovered result | Treatment |
|---|---|---|
| Marker angle STD 7.40 to 1.18 degrees | Original result reproduces. On 448 identical frame indices with marker ID 15, the values are 7.409784 raw, 1.177102 IMU, and 7.078665 rigid flow. A second interval has 444 common indices and 6.092173, 1.316880, 5.830195 degrees. | Included as **image-orientation steadiness of saved software outputs**. No independent gravity reference or current-FPGA performance is inferred. |
| Horizon ripple 0.830 to 0.078 degrees | Original scaled numbers reproduce from mean detrended residuals 8.792814 to 0.827163 pixels. The divisor 540/51 is not a calibrated angular scale; reference and correction share IMU/geometry. The indoor detector also selects red scene objects. | Full numbers, spectra and support are retained in this audit. Not used as a physical leveling-accuracy result in the paper. |
| Low spatial modes contain 97–98% of horizon residual energy | Outdoor raw profiles reproduce 97.859187% and 96.831283% in FFT bins 1–3. These bins span a resampled partial panorama. | Audit only; not a theorem about all global warps or full-360-degree harmonics. |
| Madgwick 22 ms versus complementary 42 ms delay | Reproduces as 11/21 index shifts converted using median timestamp spacing. Actual timestamp displacement medians are 27/50 ms; centered averaging and estimator choice also affect the statistic. | Not presented as causal filter delay or physical pipeline latency. |
| Filter accuracy 0.14–0.31 degrees | Low-gyro roll agreement reproduces as 0.139858/0.309478/0.197947 degrees against angles from the same accelerometer. Duplicate timestamps inflate the legacy filter's integrated time. | Audit only; not independent attitude accuracy or a measurement of current IIM46234 firmware. |
| 47/48-frame synchronization | Offline offset scans reproduce the index alignment, fitting and assessing on the same frames. | Not interpreted as 1.6 s physical latency, exposure synchronization, or held-out validation. |

The paper's archived-video section and paired-marker plot use the recovered marker
data. The static stitching comparison, C/RTL regression, fresh routing, and
historical FPS/latency/synchronization evidence retain their separate sources
and measurement boundaries. The original scientific review's “not located”
status is superseded by this recovery, not by an assumption that every old
interpretation is correct.

## Contents

- `marker_audit.md/.json`: input hashes, original and paired results, detector
  settings, detection failures, candidate upstream files, and generation gaps.
- `marker_detections.csv`: 2700 rows, including eight missed detections;
  frame/marker identity, corners, angle, frame hash, common-support flag and
  per-method centered angle. Missing/non-common samples remain explicit.
- `horizon_audit.md/.json`: exact red-pixel extraction, detrending, spectral
  definitions, hashes, support, and demonstrated contamination.
- `horizon_per_frame.csv`: all 4050 method/case/frame rows from nine videos;
  450 requested and decoded frames per video. Column support is method-specific.
- `filter_audit.md/.json`: sensor lineage, actual timebase, filter parameters,
  lag sensitivity, same-sensor agreement, and in-sample offset scans.
- `protocol_audit.json`: source/log hashes and available generator/comparator
  contracts. Defaults are not asserted to be the actual historical commands.
- `reproduce_*.py`: portable measurement runners with explicit source/output
  paths. They reject output paths inside the source archive. No renderer or
  archive-writing figure/workbook generator is invoked.

All three marker videos are 1900 by 540 pixels, 1800 encoded frames at 30 fps.
The available source uses floating-point camera projection, quarter-degree rig
angles, sequential pitch/roll warps, and strip concatenation. It differs from
the preserved fixed-point FPGA maps and blend pipeline. Exact generation
transcripts for these three-view outputs were not located: available logs
describe 2534-pixel-wide four-view outputs. Therefore reproducing metrics on
the hashed saved files is distinct from reproducing their generation.

## Reproduction

Run from the paper root. These commands write fresh results into ignored
scratch directories, retaining the reviewed evidence package unchanged:

```powershell
python evidence/video_audit_20261026/reproduce_marker_audit.py --source-root E:/D_Folder/download/test --output-dir output/recheck_marker
python evidence/video_audit_20261026/reproduce_horizon.py --source-root E:/D_Folder/download/test --output-root output/recheck_horizon
python evidence/video_audit_20261026/reproduce_filter_checks.py --source E:/D_Folder/download/test --output output/recheck_filter
python evidence/video_audit_20261026/reproduce_axis_sync.py --source E:/D_Folder/download/test --output output/recheck_sync
python scripts/render_marker_evidence.py
```

The audited environment is Python 3.9.6, NumPy 1.25.2, OpenCV 4.8.0 with
ArUco support, pandas 1.3.1, and Matplotlib 3.4.2 for the plot. OpenCV decoder
or detector changes may change recovered pixel/corner values. The marker
CLI was rerun and reproduced the reviewed CSV byte-for-byte. Horizon
vectorization was checked against the original profile on 63 sampled frames;
all per-video aggregate values matched the unchanged original measurement
function. See each audit for source checks, runner checks and retained hashes.

No metric here establishes independent current-hardware dynamic accuracy.
That requires an identified FPGA/MCU image, exposure/output identities,
independent orientation reference, and a controlled live experiment.
