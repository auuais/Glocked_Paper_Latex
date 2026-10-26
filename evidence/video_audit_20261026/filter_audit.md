# Archived video/IMU filter and alignment audit

Recorded 2026-10-26. Source archive: `E:/D_Folder/download/test`. No `AGENTS.md` was found in the source directory, its searched ancestors, or its subdirectories. This audit read the archive and re-executed pure filter/tracking calculations; it did not change the archive, run hardware, edit manuscript TeX, or commit files. Derived traces, scan curves, and reproduction scripts are under the paper's ignored `output/video_audit_20261026/`. `filter_audit.json` records the exact numeric results, software versions, absolute input paths, SHA-256 hashes, and scratch-artifact hashes.

## What the three historical claims mean

| Historical claim | Reproduction | Defensible interpretation |
|---|---|---|
| Madgwick 22 ms versus complementary 42 ms | Exact original computation gives 11 and 21 index shifts, labeled 22 and 42 ms by a median-timestamp-derived 500 Hz rate | A selected-window, positive-lag correlation statistic against the same sensor's accelerometer angle; not calibrated causal filter latency or sensor-to-display delay |
| Filter accuracy 0.14–0.31° | Static roll mean absolute differences reproduce as 0.139858°, 0.309478°, and 0.197947° | Agreement with an accelerometer-derived angle from the same IMU on low-gyro samples; not independent absolute attitude or image-leveling accuracy |
| Approximately 48-frame synchronization | Offset scans reproduce 47 frames indoors and 48 for both outdoor inputs | Offline image/gyro alignment fitted and assessed on the same frame pairs, using an assumed 30 FPS index timeline; not a measured physical pipeline latency |

The sensor and software differ from the current hardware implementation. The capture logs identify an Intel RealSense D435i, with accelerometer/gyroscope streams configured at 250/400 Hz. These results must not be attributed to the current IIM-46234 MCU firmware, its 125 Hz fusion path, or the gravity FPGA's latency. The Python Madgwick routine also guards the zero correction-gradient norm, unlike the separately documented copied-MCU boundary defect.

## Input provenance and timebase

| Label used by the archived scripts | Input | Rows | CSV timestamp span (s) | Rows per timestamp second | Duplicate successive millisecond stamps |
|---|---|---:|---:|---:|---:|
| Indoor | `captures/imu/imu_data.csv` | 23,183 | 58.830 | 394.051 | 5,645 |
| Outdoor-1 | `captures6/imu/imu_data.csv` | 23,444 | 58.828 | 398.501 | 5,909 |
| Outdoor-2 | `captures5/imu/imu_data.csv` | 23,941 | 58.823 | 406.984 | 5,955 |

All three files begin about 1.17 s after the process-relative timestamp origin and end near 60 s. Timestamp differences are nonnegative, with a median of 2 ms; they are not uniform 2 ms sampling. The filter scripts ignore the CSV's more precise `Delta_Time_ms` column and replace every nonpositive difference with 2.5 ms. Consequently, their accumulated integration intervals, excluding the first initialization step, are 72.9425, 73.6005, and 73.7105 s rather than the approximately 58.83 s timestamp spans. This is part of the reproduced historical computation, not a correction introduced by this audit.

The logs are appended across many sessions; their first May 6 entry does not date these CSV files. A unique matching row count identifies candidate June 15, 2025 sessions: Indoor 07:49:35 start / 07:50:35 CSV write; Outdoor-2 19:18:27 / 19:19:27; Outdoor-1 19:26:03 / 19:27:03. Outdoor records have those matches in their own copied log, while Indoor has no per-folder log and is matched through the shared appended history in `captures6/logs/capture_log.txt`. This is consistent acquisition lineage based on sample count, not a contemporaneous cryptographic binding of each CSV to a session. The source logs report elapsed capture frequencies of 367.98, 380.02, and 372.13 Hz over a 63 s process interval; those are different denominators from the timestamp-span rates above. Device serial numbers and full multi-megabyte logs are not copied into the paper evidence.

Input CSV SHA-256 values:

| Input | SHA-256 |
|---|---|
| Indoor | `e9458471213fb158a439e2bb43dd206a52c4214f0883d1c004acca6ad65a3079` |
| Outdoor-1 | `309e986a5f34f86ff05091e33f03f4c3bb6256f7a86d8903e079e126bb90a4ed` |
| Outdoor-2 | `35e86040f7d5a961cc33bb42b61b8afddcba34bbde3b790cbeaeb7e3009e5557` |

## Same-sensor filter agreement

The source is `stab_compare/grav_eval.py` using `filters.py`. Fixed filtering calls `madgwick_rp_cam(beta=0.1, smooth_win=5)`. Gyroscope biases `(-0.002843, 0.000743, -0.000966)` rad/s are subtracted on the original axes; gyro and accelerometer coordinates are rearranged to `(-Y,-X,-Z)`, standard quaternion roll/pitch are extracted, and roll is negated for the renderer convention. Initialization uses the first accelerometer sample. The output smoothing is a **centered five-sample boxcar with edge padding**, requiring two future samples; it is not a causal moving average as written.

The reference angles are calculated from the same record's accelerometer. The selection condition called "static" is only bias-corrected gyroscope magnitude below 0.06 rad/s; it does not independently establish absence of linear acceleration, vibration, bias, or mounting error. No warm-up exclusion or external attitude reference is used. The counts below are IMU rows, not video frames or independent acquisitions.

| Record | Selected rows | Mean absolute roll difference (°) | Roll p95 (°) | Mean absolute pitch difference (°) |
|---|---:|---:|---:|---:|
| Indoor | 9,243 | 0.139858 | 0.501245 | 0.137605 |
| Outdoor-1 | 3,542 | 0.309478 | 1.074649 | 0.265367 |
| Outdoor-2 | 3,424 | 0.197947 | 0.605649 | 0.199393 |

These reproduce the rounded 0.14/0.31/0.20 values hardcoded in `compile_stab_excel.py`; the published range should be called **low-angular-rate agreement with accelerometer-derived roll**, not "tracks true gravity" or "near-optimal leveling."

The adaptive variant uses `beta_max=0.1`, `tol=0.08`, and `gate = exp(-((|a|/g - 1)/tol)^2)`, where `g` is the median acceleration magnitude of the **entire** record. Gate means are 0.998459, 0.995046, and 0.997876, but minima are 0.870207, 0.737978, and 0.880593. The gate therefore does change; the spreadsheet's rounded 1.00 must not be described as "never fires." Adaptive static roll means are 0.139953°, 0.311038°, and 0.198075°, close to but not identical to fixed filtering. Whole-record normalization and centered smoothing make this an offline computation.

The "post-motion" branch is uninformative on these records. It asks for low-gyro samples within the next 399 indices after a magnitude greater than 0.5 rad/s. Maximum magnitudes are only 0.315695, 0.416152, and 0.305818 rad/s, so all three post-motion subsets are empty. The original script silently substitutes the all-static subset for its post-motion output column; that column does not demonstrate recovery after a motion burst.

## Reproducing, and limiting, the 22/42 ms figure

`gen_imu_filter_fig.py` reads Outdoor-1. It compares **native-axis** `madgwick_rp(beta=0.05, smooth_win=5)` with **axis-corrected** `comp_fix_rp(alpha=0.98)`. These are not the camera-axis beta=0.1 filters used in the agreement table above. Its reference is `atan2(Accel_X,-Accel_Z)`, not independent ground truth.

The script picks the strongest smoothed accelerometer-roll slope after excluding 300 samples from each end. This selects index 2,986, elapsed time 7.461 s. The correlation window is 6.661–8.261 s, containing 629 rows. Both signals are demeaned over that full window; the script maximizes an **unnormalized dot product** over nonnegative index shifts, with changing overlap length. In this run floating-point truncation makes the nominal 80 ms search indices 0–38. The maximizing shifts are 11 and 21, which the inferred approximately 500 Hz rate converts to 22 and 42 ms.

That time conversion is not a uniform timestamp shift. For the same 11-index displacement, actual timestamp separations within the window range from 20–60 ms (median 27, mean 28.073 ms). For 21 indices they range from 42–93 ms (median 50, mean 53.538 ms). A signed search using overlap-normalized Pearson correlation peaks instead at nominal 32/46 ms, with correlations 0.6554/0.7115. These alternative results are estimator-sensitivity diagnostics, not substitute ground-truth delays. Accelerometer contamination during motion, different axis conventions, data-selected transient, nonuniform sampling, and future-sample smoothing prevent a defensible causal or system-latency interpretation.

The gyro-only endpoint differs from the fused trace by 7.096956° over the 58.828 s span, producing the source's approximately 0.12°/s caption value. This is an endpoint difference against another sensor-derived estimate, not an independently calibrated physical drift rate. The original figure script has a hardcoded output pointing at the manuscript figure; it was **not executed**. The audit reproduced its numerical steps without invoking its save operation.

The public derived files beside this audit are `selected_filter_transient.csv` (629 rows, with original row index, recorded milliseconds, elapsed seconds, and the four same-sensor angle estimates) and `filter_lag_signed_curve.csv` (signed index shifts, nominal lag labels, overlap sizes, dot scores, and Pearson correlations). The curve's `lag_ms` column is the original median-interval conversion, not measured physical latency. Full-record `legacy_filter_figure_traces.csv` and per-record `captures*_filter_traces.csv` remain in ignored output scratch; their hashes are recorded in the JSON.

## Video/IMU alignment and axis fit

`calib_axis.py` tracks 899 consecutive frame pairs, from frame 0→1 through 898→899. It crops the first `width//4` strip with a 12% horizontal margin, detects up to 300 corners, applies pyramidal Lucas–Kanade flow, and fits a partial affine transform. Failed tracks contribute zeros. It compares rotation and image translations converted using 19.6 pixels/degree with integrated bias-corrected gyroscope axes. For each offset 20–74, it samples integrated gyro on a `(frame_index + offset)/30` timeline and solves three no-intercept least-squares fits; the selected offset maximizes the sum of the three in-sample R² values. There is no held-out validation or exposure timestamp comparison.

| Reproduction input | Best offset (frames) | Roll R² | Pitch R² | Horizontal/yaw-equivalent R² |
|---|---:|---:|---:|---:|
| `stab_compare/unstab.mp4` + Outdoor-1 IMU | 48 | 0.994366 | 0.998039 | 0.989873 |
| `stab_compare/cam3_in/unstab.mp4` + Indoor IMU | 47 | 0.970778 | 0.993368 | 0.906068 |
| `stab_compare/cam3_c5/unstab.mp4` + Outdoor-2 IMU | 48 | 0.994627 | 0.995915 | 0.983879 |

All three videos report 1,800 frames at 30 FPS. Outdoor-1's default video is 2,534×540; the other two are 1,900×540. The reproduction deliberately retains the source's hardcoded `NSTRIP=4`, even for those narrower three-camera outputs; it does not silently change the analysis crop. These routes reproduce the rounded table's offsets, but no archived command log establishes that these exact invocations produced the original hardcoded table. Full coefficient matrices, scans, video hashes, and tracking outputs are recorded in the companion JSON/scratch files. Dominant fitted axes are broadly consistent with negative gyro-Y roll and negative gyro-X pitch, but cross-axis terms are nonzero; "all axes/all datasets R²≈0.99" overstates the indoor horizontal fit.

The nominal 48/30 = 1.6 s quantity is an offline index alignment between separately logged streams, not a measured acquisition, filter, FPGA, or display latency. `diag_sync.py` searches only ±20 frames and cannot itself establish a 48-frame optimum. `diag_axis.py` allows ±90. `verify_madgwick.py` currently imports a nonexistent `madgwick_rpy` symbol from `filters.py`, so that script cannot be treated as a reproducible current path without modification.

## Reproduction record and recommended paper scope

The public safe runners beside this audit are `reproduce_filter_checks.py` and `reproduce_axis_sync.py`. Each requires explicit `--source` and `--output` arguments. They resolve paths, reject output inside the source archive or a nonempty output directory, verify the audited source/input SHA-256 values before evaluation, and disable bytecode writing. The filter runner loads the hash-verified module containing only imports, constants, and function definitions; the alignment runner AST-selects only `calib_axis.track()` and supplies the stated constants. Neither executes original generators or their output operations. The original archive must be supplied separately; listing paths and hashes is not a claim that its raw videos, CSVs, or logs are publicly distributed.

From the paper repository root, for example:

```powershell
python -B evidence/video_audit_20261026/reproduce_filter_checks.py --source "E:/D_Folder/download/test" --output output/filter_reproduction
python -B evidence/video_audit_20261026/reproduce_axis_sync.py --source "E:/D_Folder/download/test" --output output/axis_reproduction
```

The verified runtime is Python 3.9.6, NumPy 1.25.2, pandas 1.3.1, and OpenCV 4.8.0. Other versions are not promised bit-identical tracking or fitting. Both public runners reproduced every original dataset statistic, selected correlation result, and offset/axis fit exactly in this runtime. Actual timestamp-separation diagnostics agree within 1e-9 ms of the separately calculated values. A deliberate attempt to target an output subdirectory of the source archive was rejected before creation. The `effective_filter_dt_sum_s` diagnostic excludes the first Madgwick step and sums modified inter-row intervals only. No original figures, workbooks, raw videos, source CSVs, or acquisition logs were overwritten. Input/script/derived-artifact hashes are in `filter_audit.json`; larger rerun traces and results are under ignored `output/video_audit_20261026/public_*_reproduction/`.

The defensible paper addition is a compact table of same-sensor, low-angular-rate agreement and a statement that video alignment was fitted offline. The old causal 22/42 ms latency and independent 0.14–0.31° accuracy claims should not be restored. An independent dynamic orientation reference, causal timestamp-aware filtering, source/exposure identities, and held-out alignment validation would be needed to support those stronger conclusions.
