# Archived horizon audit — 2026-10-26

## Verdict

The original outdoor numbers are reproducible from the supplied encoded videos.
They can support a **synthetic-reference consistency experiment for the archived
three-view Python pipeline**, reported in pixels. They do not independently
measure physical gravity leveling, validate the present FPGA, or establish that
all global image warps are incapable of leveling a panorama.

**Recommended manuscript treatment:** retain all numerical results in this
audit and omit the synthetic horizon-error table from the main article. The
current `sections/video_archive_evaluation.tex` explanation accurately states
the shared-input limitation and demonstrated indoor contamination. The two
outdoor rows could be reported only as a qualified synthetic diagnostic; they
are not necessary to support the paper's independently defined marker-angle
steadiness experiment.

The indoor numbers also reproduce numerically, but the detector demonstrably
mixes the painted line with red scene objects. **Do not restore the indoor
synthetic-horizon row as a horizon-error result.** Preserve it in this audit as
a reproduced but contaminated statistic. The separately evaluated physical
fiducial experiment has a different measurement basis.

No source archive file was modified. No original renderer, stabilizer, figure
generator, spreadsheet writer, or archive-writing `main()` was executed. No
`AGENTS.md` was found in the archive inventory or its checked ancestors.

## Reproduced results

All nine files report 1900-by-540 pixels, 1800 frames and 30 FPS. The audit
decodes frame indices **900 through 1349**, stride 1: 450 frames, corresponding
to nominal video times [30,45) seconds. Every requested frame was decoded and
passed both original support thresholds. Frame indices are common across
methods; their valid column masks are not intersected.

The primary statistic is the arithmetic mean over frames of the spatial RMS
after fitting and subtracting a line on that frame's valid columns:

`D = mean_t sqrt(mean_{x in Omega_t} (y_t[x] - (a_t*x+b_t))^2)`.

| Dataset | Method | Mean detrended RMS (px) | Mean mean-subtracted RMS (px) | Original scaled value (not calibrated degrees) |
|---|---|---:|---:|---:|
| Outdoor-1 | Raw | 8.792814 | 27.337656 | 0.830432 |
| Outdoor-1 | G-locked | 0.827163 | 1.650271 | 0.078121 |
| Outdoor-1 | Optical flow | 8.756265 | 23.331033 | 0.826981 |
| Outdoor-2 | Raw | 7.557927 | 28.957048 | 0.713804 |
| Outdoor-2 | G-locked | 0.791876 | 1.821538 | 0.074788 |
| Outdoor-2 | Optical flow | 7.542087 | 24.380564 | 0.712308 |
| Indoor — contaminated | Raw | 19.496587 | 41.794732 | 1.841344 |
| Indoor — contaminated | G-locked | 11.890456 | 12.125627 | 1.122987 |
| Indoor — contaminated | Optical flow | 17.682822 | 38.154268 | 1.670044 |

The last column is exactly `D/(540/51)`, the original evaluator's conversion.
It reproduces the old rounded 0.830/0.078/0.827 and 0.714/0.075/0.712 values.
It should remain in the audit, not be relabeled as independently calibrated
angular accuracy. The actual cylindrical map uses a tangent-based vertical
focal parameter: at its central ray and half scale, the local linear scale
is about 9.879729 pixels/degree, whereas 540/51 is 10.588235. Moreover the
painted line uses a separate empirical pitch factor. There is no demonstrated
single global pixels-per-degree calibration for the residual statistic.

For the raw videos, the original FFT procedure places **97.859187%** of
Outdoor-1 residual energy and **96.831283%** of Outdoor-2 residual energy in
bins 1–3. The old rounded 98% and 97% are therefore reproducible. These are
FFT bins across the resampled partial-panorama image support, not verified
harmonics of a full 360-degree gravity horizon. Indoor gives 61.623117%, but
its scene-color contamination makes a horizon interpretation unreliable.

## Exact protocol and source locations

Read-only source root: `E:/D_Folder/download/test/stab_compare`.

- `measure_ripple_spectral.py:26–33`: split decoded BGR pixels; select
  `R>150`, `G<95`, `B<95`; average all selected row coordinates in each
  column, requiring at least two selected pixels. No connected-component,
  line-location, scene-object, or independent annotation check is applied.
- `measure_ripple_spectral.py:39–61`: require at least 40% valid columns;
  fit `numpy.polyfit(x,y,1)` on that method/frame's own valid columns; report
  per-frame residual RMS and its arithmetic temporal mean. The field called
  `s_global` is the explained sum-of-squares fraction of this fitted line,
  not the fraction removable by arbitrary global warping.
- `measure_ripple_spectral.py:53–58,78–83`: interpolate each residual onto
  256 equally spaced samples spanning its first and last valid column;
  subtract its resampled mean; take squared magnitudes of `rfft`; average
  powers across frames; divide bins 1–3 by all non-DC bin power. It is a
  ratio of averaged powers, not an average of per-frame power fractions.
- `measure_ripple.py:34–46`: a related undetrended statistic uses at least
  30% valid columns and reports spatial standard deviation, its temporal
  standard deviation, and the 97th-minus-3rd percentile spread. The latter
  is not a true maximum-minus-minimum peak-to-peak value despite its label.
- `measure_horizon.py:22–41`: applies the same all-red mask and PCA to each
  strip's central 76% width. Its angle is image-line tilt, not independent
  absolute gravity accuracy; it shares the synthetic-reference and
  scene-color limitations. This audit does not restore its unverified angle
  table as an independent result.
- `compile_stab_excel.py:18–36`: the old horizon table values are hardcoded
  constants. The workbook is not an independent measurement source. The
  video recomputation above supplies the previously missing traceability.

The audit executes only the `profile` and `measure` function definitions
extracted with Python AST from `measure_ripple_spectral.py`. The original
`measure()` arithmetic is unchanged. A vectorized column mean replaces its
slow profile loop and is checked for exact equality, including NaNs, against
the original function on seven frames in every file: 63 exact checks. Row
indices and their sums are integers small enough to be exactly represented
in float64; division uses the same count. The independent per-frame summary
mean also equals the original `measure()` result exactly for every file.

`horizon_audit.json` records the software versions, source/video SHA-256
hashes, sizes, stable-during-hash flags, complete spectra, support summaries,
and reproduction-script hash. `horizon_per_frame.csv` preserves all 4050
method/case/frame rows, including validity flags and column counts. The
portable read-only reproduction script is supplied alongside this file as
`reproduce_horizon.py`. Its dependency set is Python, NumPy and OpenCV.
The original complete run used the initial script in
`output/video_audit_horizon/reproduce_horizon.py`; the JSON retains that exact
hash separately from the final portable script's hash. The portable version
changes argument/output handling and adds sparse inspection, preserving the
measurement arithmetic. A 27-row smoke run (frames 900–902, all nine videos)
matches the complete-run CSV exactly, and all nine video SHA-256 hashes agree.

From this evidence directory, the following commands write only to a separate
output directory. The archive root must contain `stab_compare` and `captures*`:

```powershell
python reproduce_horizon.py --source-root 'E:/D_Folder/download/test' --output-root '../../output/horizon_reproduction'
python reproduce_horizon.py --source-root 'E:/D_Folder/download/test' --output-root '../../output/horizon_spot_checks' --inspect-only
```

The full command reproduces numerical measurements and provenance, rather
than the manually reviewed conclusions in this Markdown file. The inspection
command decodes only fixed outdoor frames and the indoor diagnostic below.
The script refuses an output root inside the source archive (tested: rejected
with exit status 1 before output creation). It verifies the archived spectral
measurement script's SHA-256 before executing its two function definitions;
changed source requires a new review. It does not execute module-level code
or import any original generator.

## Dataset and reference construction

The archive's own `compile_stab_excel.py:141–142` identifies Indoor with
`captures`, Outdoor-1 with `captures6`, and Outdoor-2 with `captures5` and
states that the first three cameras are used. The corresponding horizon
files are in `cam3_horizon`, `cam3_out_h`, and `cam3_c5_h`. The observed 1900
pixel widths and three strip boundaries are consistent with this description.
This is not a six-camera 360-degree experiment. The source's `NCAM=4` default
cannot be treated as the invocation used for these three-view files.

`gen_our_videos.py:161–170` computes the drawing reference directly from the
same recorded IMU stream used by the orientation filter:

`r_acc = atan2(Accel_X,-Accel_Z)`,
`p_acc = atan2(Accel_Y,hypot(Accel_X,Accel_Z))`.

It assigns nominal frame times `(frame+offset)*1000/30`, uses `searchsorted`
to select the first IMU timestamp at or above that time, and clips out-of-range
indices. The drawing reference and correction therefore share both the IMU
data and frame-association convention. There is no independent optical or
orientation-instrument reference in this experiment.

After cylindrical remapping, the code draws a red line in each camera's
image (`gen_our_videos.py:179–190`). Both line construction and correction
use `convert_rpy` with the same camera yaw list; the drawing uses line angle
`-r_acc,camera` and vertical center `H/2 + int(-PITCH_FACTOR*p_acc,camera)`.
The correction shifts by `int(PITCH_FACTOR*p_filtered,camera)` and applies
the corresponding image rotation (`:192–196`). `PITCH_FACTOR=-19.6` at full
resolution (`:29`), and the default output scale is one half. Filtered rig
angles are rounded in quarter-degree steps before camera conversion
(`:174–175`). The cropped strips are concatenated with `np.hstack` (`:198`);
they are not seam-blended into a physically continuous all-azimuth panorama.

Consequently a low residual primarily demonstrates agreement of the filtered
angles, quantization, and sampled warps with this deliberately matched
synthetic construction. Acceleration artifacts, axis or timing errors shared
by the reference and correction can cancel. A lower score does not prove
better actual scene leveling. The archived Python renderer and filter are
also distinct from the present fixed-point C/RTL implementation; comments
claiming C-like geometry do not establish numerical equivalence.

The figure script `gen_outdoor_ripple_fig.py:10–31` identifies Outdoor-1,
uses an offset of 48 nominal frames, and selects the maximum absolute
filtered-roll frame in [900,1350). Its figure is deliberately a selected
maximum-tilt example, not a typical frame. The current generator supports
multiple filters and gains; retained files and wrapper defaults alone do not
prove every original command-line argument. Do not infer undocumented
arguments from filenames.

## Demonstrated indoor scene-color contamination

The largest G-locked detrended residual in the indoor window occurs at frame
1276: **18.630755 px**. Direct inspection of that decoded frame shows a nearly
straight painted line around rows 270–273, plus red labels/objects elsewhere
in the room. The original mask includes 426 red pixels outside rows 250–290
in 170 columns, at row coordinates from 124 through 525. Since it averages
all red rows in a column, unrelated scene pixels pull the inferred profile
away from the painted line.

As a **single-frame diagnostic only**, restricting that mask to rows 250–290
retains all 1900 columns and changes the fitted residual to **0.355100 px**.
This restriction was selected after inspecting that frame; it is not a new
validated segmentation rule and must not be substituted into the results
table. It demonstrates why the original indoor result is not a clean
horizon-error measurement. Extracted diagnostic frames remain in ignored
paper output scratch, not copied into the public evidence directory.

The outdoor sample inspected at the largest Outdoor-1 G-locked residual
(frame 1032, 4.473932 px) visibly contains curved/segmented painted-line
residual. This limited visual check is not an exhaustive proof that no
outdoor scene-red contamination occurs; the detector's definition and
limitations must remain explicit.

## Fixed outdoor spot checks

To inspect detector validity without rerunning the complete videos, the audit
decoded frames **900, 1125 and 1349** from each of the three methods in both
outdoor cases: 18 fixed images, all inspected at original size. No obvious
unrelated red scene object appears in these samples. Each mask has one dominant
connected painted-line component; only 0–29 selected red pixels lie outside
that largest component. Small disconnected pixels are not automatically
classified as scene objects, and the component rule is not substituted into
the reported scores.

The image hashes, component bounding boxes, red-pixel counts, frame indices
and original scores are retained in `horizon_audit.json`. PNGs remain in local
scratch under `output/video_audit_horizon/outdoor_sparse`, not in the public
evidence dataset. The portable script can recreate them with `--inspect-only`.

These samples make the outdoor scores more defensible as measurements of the
painted profile than the contaminated indoor scores. They do **not** establish
detector purity over all 450 frames, a calibrated angular scale, an independent
physical reference, or equivalence to the current FPGA. Keeping their exact
numbers in this audit while omitting them from the manuscript is therefore a
reasonable and conservative scientific choice.

## Support and baseline limitations

| Dataset | Raw mean/min support | G-locked mean/min support | Optical-flow mean/min support |
|---|---:|---:|---:|
| Outdoor-1 | 99.9989% / 99.9474% | 99.9998% / 99.9474% | 97.2338% / 93.8947% |
| Outdoor-2 | 99.9987% / 99.9474% | 100% / 100% | 97.6487% / 93.6842% |
| Indoor | 99.8682% / 98.7368% | 99.9676% / 99.0000% | 98.4864% / 95.0000% |

All frames pass, but cropping/warping changes support, particularly for the
optical-flow baseline. Per-frame masks were not retained after extraction;
the videos were not reread solely to calculate a shared column intersection.
The table therefore matches temporal indices, not pixel support.

`of_stabilize.py` implements a specific offline baseline: Shi–Tomasi
features, Lucas–Kanade tracking, partial-affine estimation with scale
discarded, cumulative parameter trajectories, and a centered 61-frame
Gaussian window of radius 30. It is not all optical-flow stabilization and
not causal zero-lookahead processing. Its implemented warp uses
`transforms + (smoothed_trajectory - trajectory)` (`:74`) about the panorama
center (`:89–92`), whereas the header describes only the latter correction.
Thus even its code/header convention must not be generalized into a claim
about the best possible planar baseline.

Mathematically, subtracting a fitted line only makes the residual invariant
to adding `a*x+b` on fixed support. A global vertical scale multiplies the
residual, and a rotation changes coordinates/support. A nonlinear
cylindrical/spherical warp can level a gravity horizon. The original
“irreducible”, “G-locked only”, “any global warp”, and “spatial dual of Liu”
claims are not established by this experiment. The quantity `1-D/D_raw`
is an observed relative reduction, not intrinsically bounded to [0,1] for
arbitrary outputs.

## Optional wording if outdoor diagnostics are reported

“We remeasured two archived outdoor three-view sequences using an
accelerometer-derived line painted into the images before correction. Over
the same 450 frame indices (30–45 s), mean line-detrended red-profile RMS was
8.79/0.83/8.76 pixels for Raw/G-locked/the tested rigid optical-flow baseline
on Outdoor-1 and 7.56/0.79/7.54 pixels on Outdoor-2. These measurements assess
the archived renderer's consistency with a synthetic reference sharing its
IMU input and geometry. They do not provide independent physical leveling
accuracy. Column supports remain method-specific. An indoor color-detector
contamination was identified, so its synthetic-line scores are excluded.”

The 97–98% low-bin energy can be added as a descriptive statement about
these image-coordinate residuals if useful, but it is not needed to support
the implementation contribution and does not rescue the original theorem.
