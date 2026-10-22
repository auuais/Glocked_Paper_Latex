# Algorithm and architecture audit

Recorded 2026-10-23. This audit supports `sections/algorithm_architecture.tex` and the three native TikZ figures `figures/gl_projection_geometry.tex`, `figures/gl_runtime_flow.tex`, and `figures/gl_hardware_architecture.tex`. It is a source extraction plus manuscript-layout check, not a physical stabilization experiment. No implementation source, FPGA input, optical ROM, firmware, main manuscript, or bibliography was edited for this task.

## Authoritative snapshots

- Implementation checkout: `E:/Xylinx/EO_IR_GravityLocked_Stabilization`, commit `5126c375957005e65dd000b2004fb01fbe1baaae` (one-time calibration firmware candidate).
- Preserved optical/renderer baseline: `3479cacf2e512a5bde9aa3e0243755826e071ef4`; the gravity integration deliberately preserves that geometry.
- Exact C oracle source: `C:/SVNProjects/IMU_Stabilize_v40/IMU_stabilize_GYRO/IMU_stabilize_GYRO.cpp`, SHA-256 `f4dea4cbfba60bfe686644081c7bcfb4744c9d8b14771c0d916dad6702839495`. The checked-in [provenance](E:/Xylinx/EO_IR_GravityLocked_Stabilization/reference/gravity_math/provenance.json) records original line ranges and excerpt hashes. It is the original compiled translation unit, rather than a mathematically similar rewrite.
- Selected mounting INI: [config/parameters_unified.ini](E:/Xylinx/EO_IR_GravityLocked_Stabilization/config/parameters_unified.ini), SHA-256 `7106b1f1ad56d545c6b3eef5b29f9608fdb1cfb02ce364b1ca85ca096c3eea3c`. Original selection: `C:/SVNProjects/IMU_Stabilize_v40/EO_IR_TestCases/EO_Test4C_R_0.75_P_-5/480_test/parameters_unified.ini`.
- The implemented FPGA timing candidate is the corrected independent-IR-epoch build `builds/gravity_20261016_020605`, not the superseded `012049` build. Its [record](E:/Xylinx/EO_IR_GravityLocked_Stabilization/docs/validation/full_build_20261016_020605.json) reports Vivado 2025.2, part `xcku15p-ffve1517-2-i`, WNS +0.075 ns, WHS +0.010 ns, WPWS +0.064 ns and zero failing endpoints. These are constrained implementation reports, not measured clock margin or hardware throughput.

## Numerical contract

1. Use conventional axis matrices with the **actual order** `Rsys=Rx(r)*Ry(p)`, `Rt=Rz(yaw_i)*Ry(pitch_i)`, `Roff=Rt*Rx(roll_i)`, `R=Rsys*Roff`. Four matrix multiplies each quantize/saturate; algebraic reassociation is not bit-equivalent.
2. Orientation trig uses 36,000 centidegree entries, signed 16-bit sine/cosine scaled by 32767, including matrix identity entries. Signed 32-bit angles wrap modulo 36,000 with a nonnegative result, including INT_MIN/INT_MAX. IR mounting yaw 39,000 must not be reinterpreted as signed 16-bit before normalization.
3. Each matrix sum is quantized by `(sum+16384) arithmetic>>15`, then saturated to [-32768,32767]. The positive bias is applied to negative sums too. RTL uses signed 32-bit products and a signed 36-bit accumulator.
4. `atan2` uses a 4,097-entry atan(i/4096) table. Ratio index is `(min_abs*4096 + floor(max_abs/2))/max_abs`, integer division, then octant/quadrant reconstruction; atan2(0,0)=0. `asin` clamps input to [-32767,32767], takes floor integer sqrt of `2^30-v*v`, then atan2. Euler gimbal threshold is absolute table-cosine >8; otherwise roll=0 and yaw=atan2(-R01,R11). Computed camera yaw is unused downstream.
5. Original C `lround` conversions use ties away from zero, with float parameters first represented as float32. `div_round_i64(n,d)` adds/subtracts d/2 according to numerator sign before C truncation-toward-zero division (d>0 on these paths). The original signed shifts are matched to the observed MSVC behavior; the reference README explicitly does not promise identical behavior from every C++ compiler.
6. Frame pose performs one global live-R/P rescale at max camera |R|/|P| >1000 cd only when either live angle is nonzero; denominator is the first-pass maximum. Static trims remain unchanged. A second projection pass is performed once, not iterated to convergence. An out-of-range flag is retained. The pixel renderer separately clamps each final angle to ±1000 cd.
7. Disabled/missing/stale/revision-mismatched correction returns static R/P **exactly**. Enabled zero executes the quantized C projection. These must not be conflated in a zero-baseline test.
8. The preserved pixel path uses unity32768 and a 1001-entry absolute-angle ROM; this is distinct from orientation unity32767. EO/IR pitch coefficients are Q16 -642253/-571474; translation is signed round-nearest-away of coefficient*centidegrees/(100*65536), followed by negative-roll trig rotation around source center (960,540)/(320,256). Translation is applied before rotation. The 8-bit row shift covers EO ±98 and IR ±87.
9. Base coordinates are signed32/Q16. Stored segment slopes are signed16 with 5 EO /4 IR fractional bits; promote by <<11/<<12. Centered coordinate stages use signed27, transformed slopes signed24/Q16, accumulated coordinates signed32/Q16. Coordinate product shifts are arithmetic15 without a rounding addend.
10. Sampling is **not general bilinear**: EO x is phase-locked to panorama chroma parity and Y/C use rounded vertical interpolation; IR x=floor(x), luma uses truncating signed vertical interpolation, chroma=0x80. Valid range is [0,W-2]×[0,H-2]; invalid output is black. EO seam alpha lengths are17 luma/8 chroma. IR ordinary overlap29; special camera2/3 fold uses tail48/head90 and `cam23_fold_alpha_pos(j)=0` for j≤17, otherwise min(28,((j-17)*25+32)>>6). The archive ROM bytes are the alpha-weight authority.

The manuscript's small-angle relation `r_i≈r cosψ_i+p sinψ_i`, `p_i≈p cosψ_i-r sinψ_i` is derived from the stated matrix chain for zero mounting trims. It is explanatory and not the implemented numeric engine. A general calibrated ray-domain rotation can induce a global cylindrical warp; the restricted affine approximation here does not justify an impossibility theorem for all global correction.

## Calibration and configuration completeness

The section table records both preserved optical profiles and the selected INI: source dimensions, intrinsic focal/principal-point values, distortion coefficients, resize, cylindrical FOV, crop scales, map overlap, feather, logical output widths, strip widths/starts, and source pitch factors. Focal values for distortion equal the listed `(fx,fy)`. Source snapshots are [EO 20260806](E:/Xylinx/EO_IR_GravityLocked_Stabilization/assets/packages/eo_20260806/source_parameters_unified.ini) and [IR 20260806](E:/Xylinx/EO_IR_GravityLocked_Stabilization/assets/packages/ir_20260806/source_parameters_unified.ini), with installed ROM/model cross-checks. IR camera2's 640-pixel effective strip includes its inherited fold treatment; the old header's uniform621 description does not describe that renderer detail.

Additional persisted or inactive fields that should not be confused with active optical regeneration:

| Field | Value / behavior |
|---|---|
| Initial EO mount yaw cd | 0,6000,12000,18000,24000,30000 |
| Initial IR mount yaw cd | 9000,15000,21000,27000,33000,39000 |
| Initial mount R/P | all zero; later UI R/P retained |
| Firmware blank-storage optical defaults | overlap EO100/IR30, feather Q16=65536; not the installed EO map's overlap50 |
| Firmware R/P validation | ±500 cd |
| Firmware yaw validation | unsigned16, 0..65535; yaw does not drive current FPGA runtime geometry |
| Firmware overlap / feather validation | overlap≤1920; feather Q16 6554..655360 (about0.1..10) |
| Mounting-profile revision | 0x7106B1F1, once-only migration; valid legacy unrelated/reserved bytes retained |
| Journal | two2048-byte pages, legacy112-byte v3 payload, v4 32-byte header +112-byte payload +8-byte last commit marker; preserve one valid survivor |
| Runtime startup mode | EO panorama0x15; stored mode is preserved during migration |
| Active panorama mode IDs | EO0x15, IR0x14; INI model IDs are not FPGA mode IDs |
| Selected INI example orientations | EO75/-500cd, IR125/650cd; test data, not startup attitude |
| Inactive yaw-to-translation factors | EO17.84, IR-8.70 pixels/degree; no live-yaw path here |
| Individual-view crop metadata | EO(50,20,1820,1040); IR(20,15,600,450); not the panorama capture envelope |
| Current C optical normalization | EO effective factor Q16=-1140855 (about-17.408), IR=-571474; differs from retained EO factor |

## MCU estimator configuration and boundaries

- Actual copied path: IIM-46234 packet parser, six-axis Madgwick (accel+gyro), no magnetometer. Requested divider1 (nominal1000 packets/s), output0x07, BW_CONFIG0x44 (BW4 accel and gyro). The code contains identifiers for other rates but those are not selected by startup. No hardware bandwidth in Hz is inferred from BW4.
- Eight accepted packets are arithmetically averaged per fusion step, nominal125 updates/s; beta0.12; identity initial quaternion. Configured gyro biases `(0.421587,-0.133538,0.064359)` degrees/s are subtracted before conversion to radians/s. No rig-axis swap or hand-eye calibration matrix is applied here. Comments about a previous stationary bias measurement are not a new measurement in this candidate.
- Packet timestamp and8-bit sample-counter differences estimate packet rate over32 accepted intervals, then fusion rate is set to packet-rate/8. Timestamps remain inside the MCU; the FPGA receives no source timestamp. Missing/irregular packets mean nominal rate is not a demonstrated update cadence.
- Output clamps R/P to±90degrees; computes float quaternion Euler angles; applies EMA with `alpha=clip((1000/fs)/(10+1000/fs),0.02,1)`; rounds centidegrees then quantizes to10cd, ties away fromzero. Shadow update occurs every10 packets or pendingVSYNC. Because alpha uses packet dt but is not applied on every packet, **10ms is not an established effective time constant or measured latency**. Nearby comments saying5ms or below10ms are stale/unsupported.
- PB9 DRDY increments a counter; PC4 VSYNC sets a flag; the main loop drains DRDY then marks VSYNC pending, and the orientation service sends current shadow R/P. Source gating allows modes0x14/0x15. A separate250ms no-DRDY status monitor is not a guarantee of usable physical attitude, nor the FPGA's100ms age policy.

### Reproduced zero-gradient boundary (new isolated host check)

The reviewable harness, actual log, source hashes, and reproduction instructions are also archived in [evidence/filter_boundary](filter_boundary/REPRODUCTION.md), without executables, objects, or copied production source.

The exact current [imu_madgwick.c](E:/Xylinx/EO_IR_GravityLocked_Stabilization/firmware/eo_osd_remote/Core/Src/imu_madgwick.c) normalizes its acceleration gradient without testing for zero norm. This was reproduced with an isolated host harness, with no firmware edit:

- [Harness](E:/Xylinx/EO_IR_GravityLocked_Stabilization/builds/paper_algorithm_preview/madgwick_boundary.c), [command file](E:/Xylinx/EO_IR_GravityLocked_Stabilization/builds/paper_algorithm_preview/test_madgwick_boundary.cmd), [actual log](E:/Xylinx/EO_IR_GravityLocked_Stabilization/builds/paper_algorithm_preview/madgwick_boundary.log).
- MSVC x64: `/std:c11 /O2 /W4 /WX /fp:precise`; compile exact copied source, force-include only `stddef.h` for its NULL definition. Initialize frequency125Hz, beta0.12 and identity quaternion.
- One update with gyro(0,0,0), acceleration(0,0,1) produces all-NaN quaternion (`finite=0`). At that orientation the correction gradient is identicallyzero, leading to 1/sqrt(0) and zero-times-infinity.
- Controls: acceleration(0.01,0,1) and zero acceleration(0,0,0), both with zero gyro, remain finite. The zero-acceleration path skips the gradient correction.
- Scope: a host numerical boundary reproduction, not an observed physical sensor failure, comprehensive estimator validation, firmware correction, or latency measurement. The paper must not describe the upstream filter as fully validated.

## Runtime coherency and storage contract

- I2C7-bit0x36; reg0x10 exact four acknowledged bytes Rlo,Rhi,Plo,Phi, STOP commit; signed16 centidegrees. Partial/excess/restarted/misordered transactions rejected. Local receipt sequence32bits counts accepted FPGA transactions. Control reg0x04 exact1byte A1/A0, enabled only by MCU On+Attitude Sensor; reset disabled.
- Both family histories capture continuously: 16 full16-bit epoch tags each, signed16R/P, sequence32, age32, overflow/valid, enable, calibration revision32. EO captures on EO strobe; IR on independent synchronized existing IR genlock; all six writers of each family use its own Gray epoch. No same-number cross-family lookup.
- Default freshness23,340,000UI cycles, inclusive at capture, nominal100ms at233.4MHz. Same-edge pose beats capture (age0); capture beats lookup. Saturation overflow is unusable. No request means response fields hold; response-valid alone pulses.
- Calibration settle path requires2^25UI cycles unchanged, nominal143.76ms at233.4MHz, clamp±1000cd; two16-bit bank counters form revision. This is a settling CDC strategy, not a per-byte transaction commit.
- Panorama lease snapshots selected family+epoch and current trims/revision. Missing/stale/disabled/revision mismatch causes exact static fallback. Lease/mode changes outside active render cancel work; accepted pass freezes outputs. Table build uses the accepted snapshot and replay waits for valid new requirements. Identical R/P/sensor reuse tables even if metadata revision changes.
- Source map records: EO31680×144 bits, IR28800×96 bits, maximum64 pixels/segment. PARAMS32768×144; active queue4096×144; bucket/counter RAM each2048×16; output-row-ready512×11.
- Line ring physical18×512×64 bits, six cameras×three slots. RowWindow2^18×72bits (64 URAM blocks for this array),256 EO rows×1024words×4 pixels or512 IR rows×512words×8 pixels. Include all other tables/ROMs and DDR in resource statements. It is not two lines and not1.93MB total system memory.
- EO camera source banks: four/camera; frame stride1,036,800 and camera stride4,147,208 DDR application addresses, row stride960. IR: frame stride81,920 and camera stride327,688, row stride160. These are app-address units, not byte offsets. INI DDR byte offsets are not used as this layout.
- EO capture fixed rows0..1079, beats8..111, columns128..1791,112320 useful256-bit beats per camera/frame. IR full640×512,10240 beats/camera/frame. EO single's selected camera adopts a full120-beat row and requires an actually full-window descriptor; a later narrow descriptor invalidates cached coverage.
- Scanout uses separate build/pending/display output banks. EO pano/IR padded output115200beats/frame (1920×960×2/32); EO single129600beats/frame (1920×1080×2/32). Scanning can repeat images.

## Bandwidth and validation evidence

The [capture-envelope report](E:/Xylinx/EO_IR_GravityLocked_Stabilization/docs/validation/gravity_capture_envelope.json) proves a geometric coverage envelope, not DDR service capacity. It enumerates2001 roll values and both±98-row pitch extremes over all segment endpoints (253,566,720 evaluations), using affine-pixel and fixed-roll pitch-monotonicity bounds. New exhaustive numerical work was not rerun for this manuscript extraction.

At assumed30capture/output frames/s, aggregate useful256-bit **write** beats/s are: EO panorama23.6736M =20.2176M capture+3.456M output; EO single24.624M =20.736M+3.888M; IR panorama5.2992M =1.8432M+3.456M; IR single23.6736M (EO background capture remains active while IR single uses its BRAM source). The families do not continuously write EO+IR sourceDDR simultaneously. All totals exclude DDR reads, stalls, protocol overhead, and transitions. Historical measured aggregate22.3M is below the EO requirements; it must not be relabeled capture-only capacity or used to promise30unique fps. Row-specific capture masks alone do not help the present global rectangular replay requests. Arbitrary rapid mode churn and inherited single-view bank ownership under long stalls remain bench concerns.

Existing evidence, inspected rather than rerun here:

- [Camera projection](E:/Xylinx/EO_IR_GravityLocked_Stabilization/docs/validation/camera_projection_20261015.json):1342 exact compiled-C vectors,531..601cycles; [ROM/vector provenance](E:/Xylinx/EO_IR_GravityLocked_Stabilization/reference/gravity_math/rtl_assets_manifest.json).
- [Frame pose](E:/Xylinx/EO_IR_GravityLocked_Stabilization/docs/validation/frame_pose_20261016.json):266cases,3556..7319enabledcycles and1bypasscycle. Pose delay is not camera exposure-to-output latency.
- [Renderer integration](E:/Xylinx/EO_IR_GravityLocked_Stabilization/docs/validation/renderer_integration_20261016.json): table and pixel tests, frozen build/pass checks, coverage and selector checks;14,112,000 retained EO/IR raster pixels compared per eight-case suite. A repeated IR case overwrote a same-name file; do not inflate retained-pixel count to nine distinct golden rasters.
- [Corrected full build](E:/Xylinx/EO_IR_GravityLocked_Stabilization/docs/validation/full_build_20261016_020605.json):143118 routable nets, no unresolved routes, positive timing as above. Scoped gravity/mailbox checks do not imply whole-design CDC cleanliness; inherited CDC findings remain recorded.
- Physical image stabilization, axis/sign alignment, exposure latency, unique-content rate, current writer capacity, mode churn, and resets have not been demonstrated by these source/simulation/build records.

## Manuscript integration and layout

The section is self-contained with amsmath/amssymb/graphicx/booktabs/TikZ and libraries arrows.meta/positioning/calc, already present in the main preamble. Compile from the manuscript root for figure inputs. Labels `sec:algorithm` and `sec:fpga` are aliases for `sec:gl_algorithm` and `sec:gl_architecture`; replace the old sections before inclusion to avoid duplicate labels. All figure styles are locally prefixed and no new bibliography keys are required. External algorithm attribution belongs in the parent's bibliography integration; this audit supplies implementation evidence rather than substituting for literature citations.

The temporary [IEEEtran preview source](E:/Xylinx/EO_IR_GravityLocked_Stabilization/builds/paper_algorithm_preview/algorithm_preview.tex) and [PDF](E:/Xylinx/EO_IR_GravityLocked_Stabilization/builds/paper_algorithm_preview/out/algorithm_preview.pdf) were built with TeX Live2026 via the LaTeX compile skill. The final section+three figures compiles to5pages including a temporary preview title, with no overfull boxes or LaTeX errors. Native figure labels were inspected at rendered-page scale. A small number of justified-paragraph underfull warnings remain; no content clipping was seen. Preview artifacts are ignored implementation-build files, not manuscript inputs.

Parent manuscript passages outside this assignment still require reconciliation: strict two-line claims; direct-ingress IR claims inherited from old header comments; total-memory figures omitting RowWindow/DDR;500Hz/22ms estimator claims; generic hand-eye calibration claims; end-to-end equivalence with the selected newer C optical pipeline; absolute impossibility of global cylindrical correction; and any physical stabilization/30fps assertion supported only by simulation or timing. Main TeX, bibliography, and README were deliberately left untouched.

## Exact source anchors and file hashes

The following index was generated from the current files for this audit. Line numbers refer to the frozen implementation checkout above; hashes use raw file bytes. The source anchors identify implementation evidence, not citations for general scientific claims.

### `reference/gravity_math/source_functions.inc`

SHA-256 `ca009916c55a0cdb0d84b717185c154c0c6a160b00ad6da710e4aa8e25605a73`.

- [div_round_i64](E:/Xylinx/EO_IR_GravityLocked_Stabilization/reference/gravity_math/source_functions.inc:8) (line 8).
- [build_angle_lut](E:/Xylinx/EO_IR_GravityLocked_Stabilization/reference/gravity_math/source_functions.inc:21) (line 21).
- [clamp_q15_from_q30](E:/Xylinx/EO_IR_GravityLocked_Stabilization/reference/gravity_math/source_functions.inc:78) (line 78).
- [atan2_centi_q15](E:/Xylinx/EO_IR_GravityLocked_Stabilization/reference/gravity_math/source_functions.inc:116) (line 116).
- [asin_centi_q15](E:/Xylinx/EO_IR_GravityLocked_Stabilization/reference/gravity_math/source_functions.inc:141) (line 141).
- [convert_rpy_sensor_to_cam_centi](E:/Xylinx/EO_IR_GravityLocked_Stabilization/reference/gravity_math/source_functions.inc:152) (line 152).

### `reference/gravity_math/source_clamp.inc`

SHA-256 `bf2fdcf1b272e3a0e9543378fad8248291b5a8fa1b0f97710aa630f87e3286e8`.


### `src/GlCameraProjection.v`

SHA-256 `32453f0c422d0cc89c18cf0f564899fc74c0cb920b2651bd8d1808f04298f5f2`.

- [module GlCameraProjection](E:/Xylinx/EO_IR_GravityLocked_Stabilization/src/GlCameraProjection.v:24) (line 24).
- [32767](E:/Xylinx/EO_IR_GravityLocked_Stabilization/src/GlCameraProjection.v:13) (line 13).

### `src/GlFramePose.v`

SHA-256 `bb7dffeb156fda9a75b3372018a75e5bdcf5f7beda2b652af43023135a67e19b`.

- [module GlFramePose](E:/Xylinx/EO_IR_GravityLocked_Stabilization/src/GlFramePose.v:22) (line 22).
- [function signed](E:/Xylinx/EO_IR_GravityLocked_Stabilization/src/GlFramePose.v:57) (line 57).
- [rounded_numerator](E:/Xylinx/EO_IR_GravityLocked_Stabilization/src/GlFramePose.v:116) (line 116).
- [maximum_angle >](E:/Xylinx/EO_IR_GravityLocked_Stabilization/src/GlFramePose.v:168) (line 168).

### `src/GlLeasePose.v`

SHA-256 `b98d8016f529d77ddd44610f598f94fdbe29836a14ac3c8a31da75c5f61651f4`.

- [MAX_POSE_AGE](E:/Xylinx/EO_IR_GravityLocked_Stabilization/src/GlLeasePose.v:10) (line 10).
- [u_eo_history](E:/Xylinx/EO_IR_GravityLocked_Stabilization/src/GlLeasePose.v:83) (line 83).
- [u_ir_history](E:/Xylinx/EO_IR_GravityLocked_Stabilization/src/GlLeasePose.v:100) (line 100).
- [HISTORY:](E:/Xylinx/EO_IR_GravityLocked_Stabilization/src/GlLeasePose.v:158) (line 158).
- [MATH:](E:/Xylinx/EO_IR_GravityLocked_Stabilization/src/GlLeasePose.v:169) (line 169).
- [module GlTriggerEpoch](E:/Xylinx/EO_IR_GravityLocked_Stabilization/src/GlLeasePose.v:191) (line 191).

### `src/GlPoseEpochHistory.v`

SHA-256 `472e82d751b323a0b4f325c818353e1a41bcd507cc4af06b1b1f25d9e3aa64d7`.

- [HISTORY_DEPTH](E:/Xylinx/EO_IR_GravityLocked_Stabilization/src/GlPoseEpochHistory.v:8) (line 8).
- [if (pose_update)](E:/Xylinx/EO_IR_GravityLocked_Stabilization/src/GlPoseEpochHistory.v:126) (line 126).
- [if (epoch_capture)](E:/Xylinx/EO_IR_GravityLocked_Stabilization/src/GlPoseEpochHistory.v:132) (line 132).
- [if (lookup_req)](E:/Xylinx/EO_IR_GravityLocked_Stabilization/src/GlPoseEpochHistory.v:138) (line 138).

### `src/GlPoseReceiver.v`

SHA-256 `b50b3eca8377ca49b0181ebae40a4694ed0dad588685414cf2c2de73552a26a5`.

- [module](E:/Xylinx/EO_IR_GravityLocked_Stabilization/src/GlPoseReceiver.v:21) (line 21).
- [transaction_stop](E:/Xylinx/EO_IR_GravityLocked_Stabilization/src/GlPoseReceiver.v:8) (line 8).
- [sample_sequence](E:/Xylinx/EO_IR_GravityLocked_Stabilization/src/GlPoseReceiver.v:17) (line 17).

### `src/GlPoseCdc.v`

SHA-256 `0be146accc1eb76056e2e60eaf2e7f19804e2373108874678fedc4b308b4e63a`.

- [module](E:/Xylinx/EO_IR_GravityLocked_Stabilization/src/GlPoseCdc.v:20) (line 20).
- [ASYNC_REG](E:/Xylinx/EO_IR_GravityLocked_Stabilization/src/GlPoseCdc.v:34) (line 34).

### `src/PanoramaBase_DdrBlackFrame.v`

SHA-256 `bc02dc489e1df82efb6ddf747dd764ca03e79d78ed7e87f4fd129310e8ce66ea`.

- [GlTriggerEpoch u_ir_epoch](E:/Xylinx/EO_IR_GravityLocked_Stabilization/src/PanoramaBase_DdrBlackFrame.v:488) (line 488).
- [GlLeasePose u_gravity_pose](E:/Xylinx/EO_IR_GravityLocked_Stabilization/src/PanoramaBase_DdrBlackFrame.v:1837) (line 1837).
- [GRAVITY_POSE_INPUTS](E:/Xylinx/EO_IR_GravityLocked_Stabilization/src/PanoramaBase_DdrBlackFrame.v:2707) (line 2707).
- [copy_start_accept](E:/Xylinx/EO_IR_GravityLocked_Stabilization/src/PanoramaBase_DdrBlackFrame.v:741) (line 741).
- [irv19_global_epoch_gray](E:/Xylinx/EO_IR_GravityLocked_Stabilization/src/PanoramaBase_DdrBlackFrame.v:487) (line 487).

### `src/RpRenderer.v`

SHA-256 `909dbab138193b811ed8a9edfacb4e999599c5b7348d37ca4ef91b8a29de03e2`.

- [GRAVITY_POSE_INPUTS](E:/Xylinx/EO_IR_GravityLocked_Stabilization/src/RpRenderer.v:28) (line 28).
- [build_req reaches](E:/Xylinx/EO_IR_GravityLocked_Stabilization/src/RpRenderer.v:128) (line 128).
- [C_PREPARE:](E:/Xylinx/EO_IR_GravityLocked_Stabilization/src/RpRenderer.v:251) (line 251).
- [C_ROWS:](E:/Xylinx/EO_IR_GravityLocked_Stabilization/src/RpRenderer.v:277) (line 277).

### `src/RpTables.v`

SHA-256 `3e000ffb367135f96f4108dbbda0e88c540e014b391cf73a4a3cd97b2504e58a`.

- [params_mem](E:/Xylinx/EO_IR_GravityLocked_Stabilization/src/RpTables.v:91) (line 91).
- [bend_mem](E:/Xylinx/EO_IR_GravityLocked_Stabilization/src/RpTables.v:104) (line 104).
- [rr_mem](E:/Xylinx/EO_IR_GravityLocked_Stabilization/src/RpTables.v:115) (line 115).
- [angle_rom](E:/Xylinx/EO_IR_GravityLocked_Stabilization/src/RpTables.v:136) (line 136).

### `src/RpSegXform.v`

SHA-256 `4175ae47121611f4568cfcdcf6cb1baf58831d46ba3b9b4aaab36da5149843a0`.

- [module](E:/Xylinx/EO_IR_GravityLocked_Stabilization/src/RpSegXform.v:26) (line 26).
- [DRUN_TO_Q16](E:/Xylinx/EO_IR_GravityLocked_Stabilization/src/RpSegXform.v:29) (line 29).
- [localparam signed](E:/Xylinx/EO_IR_GravityLocked_Stabilization/src/RpSegXform.v:62) (line 62).

### `src/RpLineRing.v`

SHA-256 `f97ec69cf6f00ec1d44b854f61d3a605f16794b760ce0a7c95255550cceac63c`.

- [three source rows](E:/Xylinx/EO_IR_GravityLocked_Stabilization/src/RpLineRing.v:4) (line 4).
- [mem [0:511]](E:/Xylinx/EO_IR_GravityLocked_Stabilization/src/RpLineRing.v:111) (line 111).

### `src/RpRowWindow.v`

SHA-256 `9133bfed4191b54c7e20fce01e8b82c33732aca8f1a688bf061ba2027be0612c`.

- [module](E:/Xylinx/EO_IR_GravityLocked_Stabilization/src/RpRowWindow.v:21) (line 21).
- [mem [0:](E:/Xylinx/EO_IR_GravityLocked_Stabilization/src/RpRowWindow.v:32) (line 32).

### `src/RpWalker.v`

SHA-256 `44e7a99a76ee1e7184f69a2c9819eb8a4edb59d5c993d04c08d7a76851a0cb74`.

- [parameter integer SLOTS](E:/Xylinx/EO_IR_GravityLocked_Stabilization/src/RpWalker.v:29) (line 29).
- [QDEPTH_LOG2](E:/Xylinx/EO_IR_GravityLocked_Stabilization/src/RpWalker.v:31) (line 31).
- [alias_ok](E:/Xylinx/EO_IR_GravityLocked_Stabilization/src/RpWalker.v:119) (line 119).
- [queue_overflow](E:/Xylinx/EO_IR_GravityLocked_Stabilization/src/RpWalker.v:59) (line 59).

### `src/RpSampler.v`

SHA-256 `2a2cc8bc263a8d6accec99948fb062ce29529607a2170ed46a3d63fa610f51ba`.

- [function [10:0] qx_phase](E:/Xylinx/EO_IR_GravityLocked_Stabilization/src/RpSampler.v:100) (line 100).
- [function [32:0] wacc](E:/Xylinx/EO_IR_GravityLocked_Stabilization/src/RpSampler.v:167) (line 167).
- [function [7:0] vlerp](E:/Xylinx/EO_IR_GravityLocked_Stabilization/src/RpSampler.v:174) (line 174).

### `src/RpEmitter.v`

SHA-256 `a4162839135d1b42ff78691c4238e4177ba328bf1cf7df9720f0af8f01f62cc0`.

- [row_bad](E:/Xylinx/EO_IR_GravityLocked_Stabilization/src/RpEmitter.v:129) (line 129).
- [ready_now](E:/Xylinx/EO_IR_GravityLocked_Stabilization/src/RpEmitter.v:134) (line 134).

### `src/RpOffsetSync.v`

SHA-256 `2418f8c3c8d7bfeb58edf1a8322a5ac4b9e4bcb29107b3d4ef4eb967f70eea8f`.

- [STABLE_LOG2](E:/Xylinx/EO_IR_GravityLocked_Stabilization/src/RpOffsetSync.v:18) (line 18).
- [ANGLE_MAX](E:/Xylinx/EO_IR_GravityLocked_Stabilization/src/RpOffsetSync.v:13) (line 13).
- [update_count](E:/Xylinx/EO_IR_GravityLocked_Stabilization/src/RpOffsetSync.v:27) (line 27).

### `model/rpcore.py`

SHA-256 `2b6f074b790195751cd814da1c32aa3c8a83016155c0340a2f03b30b53f51545`.

- [EO = Sensor](E:/Xylinx/EO_IR_GravityLocked_Stabilization/model/rpcore.py:81) (line 81).
- [IR = Sensor](E:/Xylinx/EO_IR_GravityLocked_Stabilization/model/rpcore.py:90) (line 90).
- [y_shift_rows](E:/Xylinx/EO_IR_GravityLocked_Stabilization/model/rpcore.py:145) (line 145).
- [cam23_fold_alpha_pos](E:/Xylinx/EO_IR_GravityLocked_Stabilization/model/rpcore.py:16) (line 16).

### `firmware/eo_osd_remote/Core/Src/imu_handler.c`

SHA-256 `3f852ce7894be15a8e849703c7e7f2751b940a5bccb5079089b173f03d5f25d8`.

- [IMU_FUSION_DECIM](E:/Xylinx/EO_IR_GravityLocked_Stabilization/firmware/eo_osd_remote/Core/Src/imu_handler.c:20) (line 20).
- [s_gyro_bias_x](E:/Xylinx/EO_IR_GravityLocked_Stabilization/firmware/eo_osd_remote/Core/Src/imu_handler.c:39) (line 39).
- [Madgwick_Update](E:/Xylinx/EO_IR_GravityLocked_Stabilization/firmware/eo_osd_remote/Core/Src/imu_handler.c:169) (line 169).
- [IMU_Handler_Init](E:/Xylinx/EO_IR_GravityLocked_Stabilization/firmware/eo_osd_remote/Core/Src/imu_handler.c:194) (line 194).

### `firmware/eo_osd_remote/Core/Src/imu_config.h`

SHA-256 `5a1f97b90028ef7bd73ef7b1560f25a24e43f48fd31b48dc7340d6a776000564`.

- [IMU_SELECT_OUT_ACC_GYRO_TEMP](E:/Xylinx/EO_IR_GravityLocked_Stabilization/firmware/eo_osd_remote/Core/Src/imu_config.h:78) (line 78).
- [IMU_ODR_DIV_1000HZ](E:/Xylinx/EO_IR_GravityLocked_Stabilization/firmware/eo_osd_remote/Core/Src/imu_config.h:91) (line 91).
- [IMU_BW_DEFAULT](E:/Xylinx/EO_IR_GravityLocked_Stabilization/firmware/eo_osd_remote/Core/Src/imu_config.h:111) (line 111).

### `firmware/eo_osd_remote/Core/Src/imu_config.c`

SHA-256 `89637e9cf4e78fd6899abbbe6ff972076fc2b5294654ca62d5384d19dcf4f0f0`.

- [need_restore](E:/Xylinx/EO_IR_GravityLocked_Stabilization/firmware/eo_osd_remote/Core/Src/imu_config.c:276) (line 276).

### `firmware/eo_osd_remote/Core/Src/imu_madgwick.c`

SHA-256 `9f7040ff256606c7425e9c1bdfc872bb2e225d3473a7bf269424d8ad9c54dad7`.

- [Madgwick_Init](E:/Xylinx/EO_IR_GravityLocked_Stabilization/firmware/eo_osd_remote/Core/Src/imu_madgwick.c:27) (line 27).
- [Normalise gradient](E:/Xylinx/EO_IR_GravityLocked_Stabilization/firmware/eo_osd_remote/Core/Src/imu_madgwick.c:94) (line 94).
- [float dt](E:/Xylinx/EO_IR_GravityLocked_Stabilization/firmware/eo_osd_remote/Core/Src/imu_madgwick.c:109) (line 109).

### `firmware/eo_osd_remote/Core/Src/mcu_fsm.c`

SHA-256 `b59d024de4b00ab02ccadc1bc4317ac1d255585f43f56a2c556c22350a09fbd6`.

- [ORIENT_CLAMP_DEG](E:/Xylinx/EO_IR_GravityLocked_Stabilization/firmware/eo_osd_remote/Core/Src/mcu_fsm.c:282) (line 282).
- [UI_ORIENT_DECIM](E:/Xylinx/EO_IR_GravityLocked_Stabilization/firmware/eo_osd_remote/Core/Src/mcu_fsm.c:284) (line 284).
- [QUANT_STEP_CD](E:/Xylinx/EO_IR_GravityLocked_Stabilization/firmware/eo_osd_remote/Core/Src/mcu_fsm.c:362) (line 362).
- [ORIENT_SMOOTH_TAU_MS](E:/Xylinx/EO_IR_GravityLocked_Stabilization/firmware/eo_osd_remote/Core/Src/mcu_fsm.c:363) (line 363).
- [orient_output_alpha](E:/Xylinx/EO_IR_GravityLocked_Stabilization/firmware/eo_osd_remote/Core/Src/mcu_fsm.c:796) (line 796).
- [IMU_Handler_Init(imu_odr_hz](E:/Xylinx/EO_IR_GravityLocked_Stabilization/firmware/eo_osd_remote/Core/Src/mcu_fsm.c:1080) (line 1080).
- [quat_to_roll_pitch_deg](E:/Xylinx/EO_IR_GravityLocked_Stabilization/firmware/eo_osd_remote/Core/Src/mcu_fsm.c:1297) (line 1297).
- [s_odr_samples >= 32](E:/Xylinx/EO_IR_GravityLocked_Stabilization/firmware/eo_osd_remote/Core/Src/mcu_fsm.c:1415) (line 1415).
- [void mcu_on_vsync](E:/Xylinx/EO_IR_GravityLocked_Stabilization/firmware/eo_osd_remote/Core/Src/mcu_fsm.c:1538) (line 1538).
- [static void fpga_service_orient](E:/Xylinx/EO_IR_GravityLocked_Stabilization/firmware/eo_osd_remote/Core/Src/mcu_fsm.c:29) (line 29).

### `firmware/eo_osd_remote/Core/Src/main.c`

SHA-256 `1975f04812eb70509914e9c26cd56ef359877b0c3231c4722644b27a449d254a`.

- [GPIO_Pin == GPIO_PIN_4](E:/Xylinx/EO_IR_GravityLocked_Stabilization/firmware/eo_osd_remote/Core/Src/main.c:3013) (line 3013).
- [if (g_vsync_flag)](E:/Xylinx/EO_IR_GravityLocked_Stabilization/firmware/eo_osd_remote/Core/Src/main.c:3313) (line 3313).

### `firmware/eo_osd_remote/Core/Src/param_store.c`

SHA-256 `6d2e6f6f7779200bbea739312bcd4710187fd35648785ebabcab9c497b655d93`.

- [param_store_bank_valid](E:/Xylinx/EO_IR_GravityLocked_Stabilization/firmware/eo_osd_remote/Core/Src/param_store.c:62) (line 62).
- [param_store_defaults](E:/Xylinx/EO_IR_GravityLocked_Stabilization/firmware/eo_osd_remote/Core/Src/param_store.c:96) (line 96).
- [param_store_boot](E:/Xylinx/EO_IR_GravityLocked_Stabilization/firmware/eo_osd_remote/Core/Src/param_store.c:263) (line 263).

### `firmware/eo_osd_remote/Core/Src/param_store.h`

SHA-256 `9b996bbb83723234f2663aab6f552e2527dce4ccb5fd0add915f8651d6513faa`.

- [PARAM_STORE_PROFILE_REVISION](E:/Xylinx/EO_IR_GravityLocked_Stabilization/firmware/eo_osd_remote/Core/Src/param_store.h:12) (line 12).

### `config/parameters_unified.ini`

SHA-256 `7106b1f1ad56d545c6b3eef5b29f9608fdb1cfb02ce364b1ca85ca096c3eea3c`.

- [[eo_offset]](E:/Xylinx/EO_IR_GravityLocked_Stabilization/config/parameters_unified.ini:72) (line 72).
- [[ir_offset]](E:/Xylinx/EO_IR_GravityLocked_Stabilization/config/parameters_unified.ini:147) (line 147).

### `assets/packages/eo_20260806/source_parameters_unified.ini`

SHA-256 `d93191c869cb86d737a51f4dbfcb4b6f011b454b957605f21d645f48f6754c11`.

- [[eo_camera]](E:/Xylinx/EO_IR_GravityLocked_Stabilization/assets/packages/eo_20260806/source_parameters_unified.ini:24) (line 24).

### `assets/packages/ir_20260806/source_parameters_unified.ini`

SHA-256 `3877462b780ecb67819bc1e3411c36dbe1e0946b4d45b1f1736f048709900f74`.

- [[ir_camera]](E:/Xylinx/EO_IR_GravityLocked_Stabilization/assets/packages/ir_20260806/source_parameters_unified.ini:99) (line 99).

- Host check `madgwick_boundary.c` SHA-256 `168e17378c32abd1e491fc25afce4f9b407209617275524d509060a75a400be3`.
- Host check `test_madgwick_boundary.cmd` SHA-256 `53d98c6c608b8d3bdf972175f014afc0e83ccdffea62f538344d43a8a1b9066b`.
- Host check `madgwick_boundary.log` SHA-256 `990c7cf6af9e3acf726fa9cdce975b5d5a1acdfad25929bd5a9fe54e6de03574`.
