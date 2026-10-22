# Copied MCU filter: zero-gradient host boundary

Recorded 2026-10-23. No production source was changed. This is a small deterministic numerical-boundary reproduction, not a physical sensor test or general filter validation.

The harness compiles the exact source at:

`E:/Xylinx/EO_IR_GravityLocked_Stabilization/firmware/eo_osd_remote/Core/Src/imu_madgwick.c`

Its SHA-256 is recorded in `source_hashes.json`; that file also identifies the exact header, test, and actual output log. No copied production C, executable, or object file is included in this evidence directory.

Run `test_madgwick_boundary.cmd` from this directory on the recorded Windows/MSVC workstation. It calls the installed Visual Studio 2022 Community environment, then compiles with `/std:c11 /O2 /W4 /WX /fp:precise`. The only forced include is standard `stddef.h` for the source's NULL definition. Paths to the production source are explicit; change them only after checking the source hash if reproducing elsewhere. Compilation creates local executable/object files; the archived evidence omits them.

All cases initialize the quaternion to identity, update rate125Hz, and beta0.12, then execute one update with gyro(0,0,0):

| Acceleration | Observed finite quaternion | Interpretation |
|---|---:|---|
| (0,0,1) | No; all four components NaN | Correction gradient is zero; unguarded reciprocal square root produces infinity and zero-times-infinity |
| (0.01,0,1) | Yes | Small-tilt control has a nonzero gradient |
| (0,0,0) | Yes | Zero-acceleration control skips gradient correction |

The harness exits0 when this **failure reproduction** and both finite controls match the observed behavior. Exit0 is not a filter-correctness pass. `madgwick_boundary.log` is the actual MSVC test output. This establishes a boundary defect in the copied host-compiled implementation; it does not establish how often, or whether, deployed sensor samples reach that exact condition. No MCU or FPGA was programmed.
