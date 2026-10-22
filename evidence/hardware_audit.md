# Hardware evidence audit for the revised paper

Audit date: 2026-10-23. This audit read existing artifacts; it did not access hardware or modify any implementation repository or workbook. `hardware_summary.json` is the machine-readable companion: it records absolute source paths, SHA-256 hashes, file sizes, decoded observations, and the workbook checks. Dates and configurations below belong to the source evidence, not to this audit date.

## Evidence boundaries

| Evidence | Configuration/date | Defensible use |
|---|---|---|
| Author's report that the live gravity system works | Reported during the paper revision; tested image and run log unspecified | Qualitative functional operation; no inferred accuracy, latency, or sustained rate |
| Routed gravity implementation | Source `cbb95ad6da9cd048eb3aedfa03b7244fb5970eeb`, audit tools `c01baebe07bbb98d10227b55e67d192c6769e4a7`; completed 2026-10-16 | Whole-design resource allocation and timing under the reported constraints |
| Static source-driven renderer | Build `c83e29d`, 2026-09-04 | Historical configuration-specific distinct-output FPS and observed DDR traffic |
| V19 timing-probe captures | Build `67955bc`, 2026-08-19 | Archived last-event register snapshots with source-specific start/stop events |
| Camera raster/content studies | 2026-10-07 through 2026-10-09 | Input raster rate, qualified content-change diagnostics, and raster-phase spread |
| C/RTL and host regressions | Separate implementation validation manifests | Numerical and protocol checks; not camera, DDR, exposure, or physical CDC measurements |

A fresh build of source `5126c37` was in progress in `E:/Xylinx/EO_IR_GravityLocked_Stabilization/builds/gravity_20261022_235934` when this audit was prepared. It must have its own final manifest before replacing the October 16 numbers. Successful routing of an earlier source is not a timing result for a later source.

## Routed gravity resources and timing

Primary manifest: `E:/Xylinx/EO_IR_GravityLocked_Stabilization/docs/validation/full_build_20261016_020605.json`. Primary reports and BIT/LTX are in `E:/Xylinx/EO_IR_GravityLocked_Stabilization/builds/gravity_20261016_020605/`. The top is `KintexTop_EO_IR_HD_SDI_panorama_base`, the part is `xcku15p-ffve1517-2-i`, and the tool is Vivado 2025.2. Ten report/artifact hashes independently matched that manifest.

| Routed resource | Used / available | Utilization |
|---|---:|---:|
| CLB LUTs | 54,289 / 522,720 | 10.39% |
| CLB registers | 58,469 / 1,045,440 | 5.59% |
| BRAM tiles | 495 / 984 | 50.30% |
| URAM blocks | 92 / 128 | 71.88% |
| DSP48E2 | 30 / 1,968 | 1.52% |

The register category contains 58,468 flip-flops and one register used as AND/OR; there are no reported latches. BRAM comprises 492 RAMB36 and six RAMB18 primitives. These are **whole-top** results, including video interfaces, DDR infrastructure, tables, and debug. They are not the incremental cost of the gravity transform.

`timing_routed.rpt` reports setup WNS +0.075 ns, hold WHS +0.010 ns, pulse-width WPWS +0.064 ns, zero total negative slack, and zero failing endpoints in those three summaries. The UI clock is 233.380 MHz (4.285 ns); HD video is 74.250 MHz and the reference is 27 MHz. `route_status.rpt` reports all 143,118 routable nets fully routed and no routing errors; DRC has no Error-severity entries.

The scoped gravity/IR-epoch timing audit covers 3,524 sequential cells without missing clocks, unconstrained internal paths, or unintended internal timing cuts. The two mailbox buses retain 64 pose and eight control endpoints with a 4.000 ns maximum-delay requirement; all 80 reported bus-skew checks pass, with minimum slack +1.785 ns. These targeted checks do not establish complete system CDC signoff: the full routed report still contains 128 Critical, 265 Warning, and 710 Info CDC entries. The timing report also lists 159 ports without input delay and 37 without output delay. Thus the defensible statement is closure of the reported internal constraints, **not** complete board-I/O, exposure-timing, or full-design CDC closure. See the implementation's `docs/validation/gravity_full_cdc_review_20261016.md` for the inherited/open crossing classifications.

## Correcting the original storage and pipeline description

The implemented source-driven path is external DDR capture rings and frame leases, DDR replay, a source LineRing, source-driven sampling, a destination RowWindow, output DDR publication, and HD-SDI scanout. `docs/ROLLPITCH_SOURCE_DRIVEN_RENDERER.md` describes a three-row source ring: 3 rows × 6 cameras × 120 beats × 256 bits. The destination RowWindow provides 256 EO rows at four 16-bit pixels per memory word, or 512 IR rows at eight 8-bit samples per word. Vertical two-tap interpolation uses two adjacent rows, but that does not make the complete implementation a two-line pipeline.

The old 180-row × 3,840-pixel and two 32-row push-buffer budget belongs to the earlier C/reference architecture. `docs/EO_PANORAMA_V19_TCSVT_HARDWARE_EVIDENCE_REPORT_20260716.md` explicitly identifies that RowWindow/push-buffer plan as not instantiated in the then-current diagnostic design. Its approximately 1.92 MB subtotal excludes control, metadata, memory rounding, external frame storage, and debug. The paper's 1.93 MB claim therefore cannot be presented as measured current FPGA storage. The July report's 24,846 LUT, 27,965 register, 533 BRAM, zero URAM and 19 DSP figures also belong to an older diagnostic design with failing UI timing.

For scale only, the October routed BRAM/URAM allocation has nominal primitive capacity `495 × 4608 + 92 × 36864 = 5,672,448` bytes including parity. This is neither payload working memory nor a complete system-memory figure: it includes infrastructure/debug and excludes DDR and distributed memory. Report block allocation directly; do not compare this total or the old proposed pixel budget against neural-network parameter memory as though the scopes were equal.

## Recorded output FPS and DDR demand

The final section 19 of `E:/Xylinx/EO_IR_GravityLocked_Stabilization/docs/HANDOFF_EO_PANORAMA_30FPS_20260903.md` records the September 4 accepted run. Its BIT/LTX/manifest are archived under `E:/Xylinx/EO_Panorama_V19_M1_IR_DDR/builds/bit_archive/20260904_133759_wrwindow_c83e29d/`. The method uses exact image hashes on nominal 60 FPS HD-SDI/USB grabs, with an EO `frame_done` counter cross-check.

| Mode | Distinct output images/s | Black grabs / total |
|---|---:|---:|
| EO panorama | 29.97 | 0 / 598 |
| IR panorama | 29.70 | 0 / 474 |
| EO single | 29.95 | 0 / 477 |
| IR single | 29.95 | 0 / 477 |

These are useful **historical static-renderer** results. That EO capture used a narrow 88-beat × 1,008-row window; the gravity implementation uses a wider fixed 104-beat × 1,080-row envelope. No dated numerical run in this audited bundle transfers the above rates to the gravity envelope.

The same handoff records about 22.3 million aggregate DDR write beats/s, including capture and output. It is neither a capture-only rate nor a proven maximum sustainable bandwidth. The reported 29.8 to 17.9 ms improvement is a render-pass/service interval after reducing the fetch window, not a sensor-to-display latency measurement. Earlier explanations in that living handoff were subsequently corrected; use its final accepted-run section rather than its earlier amplification/trigger interpretations.

For the gravity envelope, a 30 Hz six-camera EO panorama implies `6 × 104 × 1080 × 30 = 20,217,600` capture beats/s plus `120 × 960 × 30 = 3,456,000` output write beats/s: 23,673,600 aggregate write beats/s, or 757.5552 MB/s of useful payload at 32 bytes/beat. This is an **analytical demand**, about 6.16% above the historical observed 22.3 Mbeat/s, not evidence of a bandwidth ceiling or achieved rate. Reads, refresh, command overhead and arbitration are additional. Although the MIG UI is 384 bits, this pixel datapath carries 256 useful bits per beat. Its arithmetic one-beat-per-UI-cycle ceiling is 7.46816 GB/s at 233.38 MHz, not a measured sustainable payload throughput.

## Latency: trace-backed event snapshots

Sources are `E:/Xylinx/EO_Panorama_V19_M1/docs/latency/MEASURED_20260819.md`, `MEASURED_20260820_3BANK.md`, and raw captures in `E:/Xylinx/EO_Panorama_V19_M1/captures/timing_20260819_185558/`. The decoder was reconstructed from **commit `67955bc`** of `src/V19TimingProbe.v` and `src/PanoramaBase_DdrBlackFrame.v`; the later working-tree decoder has a changed field meaning and must not be applied retrospectively.

The timing word with tag B packs commit-period ticks in bits 59:36, event-to-commit ticks in bits 35:12, and only the upper 12 bits of event-to-copy-done ticks in bits 11:0. Ticks are nominally 64 UI cycles at 233.4 MHz, or 0.274207 microseconds. This is clock-derived resolution, not a calibrated absolute timing accuracy. A start-event timestamp is latched at copy start, and commit means output-frame publication, not display scanout.

| Raw capture | Actual start event | Held event-to-commit value (ms) | B-word |
|---|---|---:|---|
| `eo_single.csv` | Selected EO camera descriptor-valid | 16.294 | `b03b56e00e81d009` |
| `eo_panorama.csv` | Newest camera-0 descriptor-valid | 63.505 | `b03b56f0388ac023` |
| `ir_single.csv` | Selected IR camera frame pulse | 58.916 | `b01dab703474c01f` / `b01dab703474d01f` |

Each EO capture holds one B-word for all 2,048 ILA samples. The IR capture holds the first value for 1,536 samples and the second for 512; they differ by one timer tick (58.916195 and 58.916470 ms). They are last-event register observations, **not thousands of independent frame latencies**. No empirical latency p95 or distribution can be derived from repeated reads of these held registers. The IR panorama CSV in that snapshot set contains no sample data, so no raw IR panorama number is reported.

EO panorama associates the newest camera-0 completion timestamp with the copy, not an identity-matched timestamp from the leased source frameset. If a newer descriptor arrives while the selected source is older, this interval understates the age of the leased content. It is therefore not a validated source-frame latency. IR uses a frame pulse rather than a completion descriptor, so its start boundary differs from EO even when the numerical values look comparable.

Copy-done values have a 4,096-tick bin width of 1.123153 ms. The lower bin edges for the three rows are 10.108380, 39.310368, and 34.817755 ms respectively; values lie within those bins, not at sub-0.1 ms precision. The narrative's other observed commit values (16.4/41.1/50.1/45.0 ms for EO single/EO panorama/IR single/IR panorama) do not describe this exact raw snapshot set and are not an aggregate. Its estimated totals (49.8/74.5/83.5/78.3 ms) add assumed mean row-age and scanout terms of 16.7 ms each. They exclude sensor/ISP delay and are **analytical illustrations, not measured end-to-end latency**. None is a latency measurement of the gravity implementation.

## Camera raster rate, content rate, synchronization and DNR

The October 9 all-five study is in `E:/Xylinx/EO_Panorama_V19_RollPitch/docs/eo_sync_evidence/dnr_all5_20261009/` (`README.md`, `study.json`, `raster_cohorts.csv`, and ten raw `events_*.csv`). The workbook is `EO_Camera_Synchronization_Comparison_20261009_Exposure60.xlsx`, sheet `Comparison`, cells A178:I182. The audit independently recomputed all 14,051 raster-cohort circular spans from stored integer timestamps and period values, with zero difference from the processed CSV; twenty summary cells D179:H182 matched those statistics, including their formula/cached-value relationships. All ten raw capture hashes matched the study record. The workbook was opened read-only and not recalculated or saved.

Configuration: physical cameras 2–6, 1080p60, manual shutter setting 1/60 s, gain 0 dB, external-trigger delay zero, 30 Hz FPGA trigger with 2 ms high time, common nominal 27 MHz timestamping, and rising-edge taps 336:280:308:280:322. The configured shutter value is not an independently measured integration time. DNR means 2D and 3D noise reduction changed together. Conditions occurred sequentially, with no Freeze between the four live conditions; separate frozen controls bracketed the live study.

| Sequential DNR condition | Observation (s) | Matched raster sets | Median spread (ms) | p95 (ms) | Maximum (ms) |
|---|---:|---:|---:|---:|---:|
| ON initial | 58.617 | 3,515 | 10.855 | 10.874 | 10.876 |
| OFF | 58.751 | 3,523 | 10.670 | 10.690 | 10.692 |
| ON return | 58.001 | 3,478 | 10.478 | 10.505 | 10.507 |
| OFF repeat | 58.951 | 3,535 | 10.252 | 10.272 | 10.274 |

Spread is the shortest circular arc containing the five matched raster phases within the raster period. It measures the observed output-raster timing, not sensor exposures. The monotonic change continues across ON return, so the sequence does not isolate a causal DNR synchronization improvement; independent camera drift remains. Microsecond residuals after fitting drift (for example −0.263, +2.429, +3.782 and +7.370 microseconds in the OFF comparison) are fit residuals, not the actual roughly 10 ms five-camera spread. Periodic nearest matching also cannot detect an unknown whole-frame latency offset. The FPGA trigger timestamp verifies the FPGA output event, not camera arrival/acceptance or an exposure strobe.

`docs/eo_fps_evidence/verification_results.json` and the October 7 consolidated workbook distinguish approximately 60 incoming rasters/s from content changes. A previous claim of 60 fresh full frames/s was withdrawn after a Freeze control showed continued full-frame signature changes. In the later all-five study, matched full-frame/ROI controls qualify cameras 2–4, whose content changes occur predominantly every two rasters, approximately 30/s. Cameras 5 and 6 retain full-frame changes even when frozen (ON: 981/1,268; OFF: 625/1,847), while all frozen ROI signatures remain stable. Their live ROI records also contain extra transitions. Consequently, neither those full-frame signatures nor an occasional near-60 change count certify 60 independent clean images/s across all five cameras. DNR OFF does not remove that diagnostic limitation. The cause is not isolated by this evidence.

## Reproducibility and paper wording

`hardware_summary.json` contains the exact source inventory and SHA-256 hashes; salient anchors are:

| Artifact | SHA-256 |
|---|---|
| Oct16 gravity BIT | `432946f610e8d358f65aeff0bcd01edef85d6a99bf948ace99b255d1c4663a36` |
| Oct16 routed utilization | `b6f0a1517cfae3c5f7cad2f391861620854caba4b1b79e33fe8ee3e141c72170` |
| Oct16 routed timing | `7504a68019b9523a41a5c3c26545ea0ade0e41a91cd42ec48256cdbfee451ea3` |
| Oct9 synchronization workbook | `0deead01a8332fce0377078939ff2c0d6fb5240265acf7974c9556d4a31f6ea5` |
| Sept4 static-renderer BIT | `b6bfaeb898f16270195a092b94372aa0ec3bc24697d9c2b4ec2c3c95fa9d96e4` |

The paper may report the authors' qualitative live success, the scoped routed results, the historical output-FPS observations, the exact latency snapshots, and the input raster/DNR statistics. It must retain their separate configurations. Exposure-to-display delay, source-matched current gravity latency, sustained current-envelope rate, calibrated attitude error under motion, and complete physical CDC/board-I/O qualification remain unmeasured in the cited numerical evidence. A local pose receipt sequence or trigger epoch is an association identifier, not a sensor exposure timestamp.
