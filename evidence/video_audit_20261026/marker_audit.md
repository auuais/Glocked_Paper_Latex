# Marker audit, 26 October 2026

The old **7.40° → 1.18°** claim reproduces from the saved offline three-camera panorama videos using the original ArUco function. It measures **marker image-orientation steadiness**, not absolute gravity accuracy. A fair comparison uses the same detected marker on the same encoded frame indices. No video or source file was modified.

## Primary comparison: common detected frames

| Nominal interval | Common frames / requested | Raw angle STD | Stabilized angle STD | Optical-flow angle STD |
|---|---:|---:|---:|---:|
| 30–45 s; indices 900–1349 | 448 / 450 | 7.409784° | 1.177102° | 7.078665° |
| 5–20 s; indices 150–599 | 444 / 450 | 6.092173° | 1.316880° | 5.830195° |

The population STD uses `ddof=0` and each method’s own sample mean. For 30–45 s, the means are −3.776508°, −3.911836°, and −3.767822° for raw, stabilized, and optical flow. For 5–20 s they are −2.387248°, −3.384881°, and −2.430766°. These offsets are retained in the audit; none is interpreted as a calibrated roll error.

Common support excludes indices **1030 and 1098** in 30–45 s, and **171, 172, 190, 203, 327, 346** in 5–20 s. This is a correspondence by encoded frame index and marker ID, not a proof of matched exposure timestamps or unique source images.

## Original unmatched result and detection accounting

| Interval | Method | Detections / decoded | Angle STD (degrees) | Missing indices |
|---|---|---:|---:|---|
| 900:1350 | unstab | 449 / 450 | 7.403418410 | 1098 |
| 900:1350 | our_stab | 449 / 450 | 1.175847075 | 1030 |
| 900:1350 | of_stab | 450 / 450 | 7.071112738 | none |
| 150:600 | unstab | 445 / 450 | 6.105150812 | 171, 172, 190, 203, 346 |
| 150:600 | our_stab | 450 / 450 | 1.318111007 | none |
| 150:600 | of_stab | 449 / 450 | 5.821561623 | 327 |

These values round to all six published angle numbers: 7.40/1.18/7.07° and 6.11/1.32/5.82°. The 30–45 s rates for raw and stabilized are 99.777…%, which the original print format rounds to `100%`. Therefore the compiler’s claim of complete detection is inaccurate. All detected markers were ID 15, with no multi-marker frame in either interval.

## Exact measurement and source chain

The direct inputs are `E:/D_Folder/download/test/stab_compare/cam3_in/{unstab,our_stab,of_stab}.mp4`. Each is 1900×540, 1800 encoded frames at 30 fps; OpenCV reports FourCC `FMP4` for these saved outputs. The candidate camera recordings report `h264`. This identifies encoding families, not historical encoder versions or quantizer settings. The audited windows are `[900,1350)` and `[150,600)`. Full SHA-256 hashes and byte lengths are recorded in `marker_audit.json`.

`measure_aruco.py` uses `DICT_6X6_250`, default OpenCV detector parameters, the first detected marker, and the arithmetic average of its top- and bottom-edge angles. It folds this angle to `[-45,45)` with modulo 90, then computes STD over detections only. `measure_fiducials.py` implements the same ArUco estimator and adds a separate 5×4 checkerboard PCA estimator; checkerboard detections were not rerun in this audit.

The original code does **not** enforce ID 15, although this audit verifies that ID 15 was selected on every successful detection. `cornerRefinementMethod=0` (`CORNER_REFINE_NONE`) in the executed OpenCV 4.8.0 configuration; the archived “sub-pixel corners” description is unsupported. Marker edge angles are affected by projection, perspective, resampling, compression, and corner quantization. No surveyed marker orientation or independent gravity reference is supplied.

The result appears as hardcoded constants in `compile_stab_excel.py:43–48`; it is not loaded from `metrics*.json`. Those JSON files contain feature-motion, path-spectrum, inter-frame PSNR, and Hough-line tilt summaries. They must not be relabeled as ArUco or gravity accuracy.

The current `gen_our_videos.py` supports a compatible pipeline: camera recordings and IMU CSV, intrinsic-only calibration read, undistortion and cylindrical remapping, quarter-degree roll/pitch quantization, per-camera pitch shift and roll rotation, strip crop, resize, and 30 fps encoding. Its hardcoded calibration path is `C:/SVNProjects/IMU_Stabilize_v40/EO_IR_TestCases/EO_Test2_R_2.15_P_0/parameters_unified.ini`. Constants include H/V FOV 77°/51°, yaw [0,60,120,180,240,300]°, and full-resolution pitch factor −19.6 px/degree. The source defaults are 4 cameras, crop 0.66, output scale 0.5, complementary filter, offset 0, and configurable Madgwick beta/smoothing. **They are not evidence of the actual `cam3_in` invocation.**

The indoor candidate recordings are `captures/cam_1/cam1_video.mp4`, `captures/cam_2/cam2_video.mp4`, `captures/cam_3/cam3_video.mp4`, and `captures/imu/imu_data.csv`; their hashes are retained as candidate upstream material. `find_segment.py` identifies the indoor source and uses 47-frame offset, beta 0.05, and five-tap smoothing. No generation command or per-output manifest was found to establish those settings for the saved `cam3_in` files. Existing `gen_log.txt` and `of_log.txt` report 2534×540 four-camera outputs, so they do not close that provenance gap.

The statement that the fourth camera was “slightly desynced” appears only in the workbook compiler’s scope prose (first three zero-based cameras 0–2). No quantified lag, capture-time exclusion list, or decision record was found. It should be reported as an archived rationale, not an independently verified synchronization result.

## Separate root ArUco CSV family

The root `aruco_track_*` files contain 1200 indexed rows. Raw has 1199 finite angles; stabilized has 1200. On the common finite indices, STD is 4.701207033° raw and 1.439444926° stabilized; the excluded frame is [680]. These are different artifacts and do not support the 7.40→1.18° number.

Related root `find_translation_x.py` uses `DICT_6X6_100`, selects marker ID 15, and subtracts each video’s own first-frame angle. Calling that first angle “ground truth” does not establish physical gravity. Its named files, `original_2cam_output.mp4` and `panorama_2cam_output.mp4`, currently contain 1200 frames at 20 fps with widths 1452 and 1402 respectively. A fresh default-detector probe at indices 0, 1, 300, 600, and 1199 detects no marker in either current video, although the CSVs contain finite detections at all five indices. Thus the current videos do not reproduce those CSV samples, and their exact legacy source remains unresolved. No root video file was regenerated.

Root PSNR summaries additionally include infinities for identical/reference frames and differ in finite sample support. Their per-column finite/NaN/infinite counts are retained in the JSON rather than silently treating them as matched accuracy evidence.

## Reproduction and retained data

The recomputation imports the unchanged archived function with bytecode writes disabled, wraps only its detector to record results, and checks that independent angle-STD recomputation exactly equals the returned value. Environment: Python 3.9.6, OpenCV 4.8.0, NumPy 1.25.2. The portable reproducer is `evidence/video_audit_20261026/reproduce_marker_audit.py`. Invoke it with `--source-root E:/D_Folder/download/test --output-dir <scratch-directory-outside-source>`. It rejects output paths inside the source archive and disables bytecode writes. A fresh run of this promoted script reproduced the archived detection CSV byte-for-byte and all original unmatched statistics exactly. Source, script, log, and result hashes are retained in the JSON.

`marker_detections.csv` retains **2700 method/frame rows**, including all eight missing detections: interval, method, zero-based frame index, all detected IDs, selected ID, angle, centroid, all four corner coordinates, detector refinement mode, grayscale-frame SHA-256, nominal encoded time, common-support flag, and centered angle on common support. It contains no images. Centered values subtract the corresponding method’s mean on the common support, not a physical reference angle.

This audit does not validate current FPGA motion performance, filter delay, capture/exposure association, real-time latency, the excluded camera’s synchronization, or absolute gravity accuracy. The two selected intervals are not an independent held-out dataset; `find_segment.py` explicitly supports choosing windows according to motion and IMU/image correlation. Frames are temporally correlated, so no independent-trial confidence or significance claim is made.

## Source references

- `E:/D_Folder/download/test/stab_compare/measure_aruco.py:13-25,33-52` — Hardcoded three files, defaults900:1350, default detector, first marker selected, averaged edge angle folded modulo90, population STD, detection-only samples.
- `E:/D_Folder/download/test/stab_compare/measure_aruco.py:56-64` — Printed detection percentage has zero decimals;99.777...% becomes100%.
- `E:/D_Folder/download/test/stab_compare/measure_fiducials.py:12-30,34-61` — Same ArUco estimator plus independent5x4 checkerboard PCA estimator; checkerboard was not rerun in this audit.
- `E:/D_Folder/download/test/stab_compare/compile_stab_excel.py:42-48,133-142,169-174` — Old marker numbers are hardcoded. Text asserts100%/subpixel and first3cams withcam3 slightlydesynced; no exclusion trace accompanies this source.
- `E:/D_Folder/download/test/stab_compare/gen_our_videos.py:23-29,34-42,69-96,106-170,172-202,220-244` — Current configurable generator: camera/IMU sources, intrinsic-only INI read, remapping, nominal30fps frame-to-IMU assignment, quarter-degree R/P, per-camera shift/rotation, resize and encoding.
- `E:/D_Folder/download/test/stab_compare/find_segment.py:1-11,36-51` — Indoor captures path,47frame offset, beta0.05,5tap smoothing and selection of15s windows; these are source settings, not a cam3_in generation transcript.
- `E:/D_Folder/download/test/stab_compare/of_stabilize.py:16-46,65-99` — Two-pass rigid optical-flow baseline, radius30 symmetric Gaussian trajectory smoothing, sequential frame output; no equivalent causal latency claim.
- `E:/D_Folder/download/test/stab_compare/measure_segment.py:36-75,91` — metrics_30_45s.json schema includes feature motion and Hough-derived tilt, not ArUco angle STD.
- `E:/D_Folder/download/test/find_translation_x.py:7-17,31-68` — Separate two-camera root drift source selectsID15 withDICT_6X6_100 and measures angle change from its own first frame; first frame is not independently calibrated gravity truth.
