# Fresh paper regression, 2026-10-23

All ten commanded suites passed on source `5126c375957005e65dd000b2004fb01fbe1baaae`. The machine-readable record is `../paper_regression_20261023.json` in the implementation archive, or `paper_regression_20261023.json` inside the paper's evidence directory. It contains commands, per-suite results, exact source/fixture hashes, log hashes, retained renderer-raster hashes, warnings, and scope limits. The paper archive contains a byte-identical JSON record and matching logs.

| Fresh suite | Observed result |
|---|---|
| C/Python math | 79,397 requests; 245,237 integer outputs matched |
| Pose receiver | 190 state checks |
| Pose CDC | Three clock/phase configurations, including stoppage and reset |
| Camera projection | 1,342 compiled-C vectors; 531–601 cycles |
| Pose epoch history | Four depth/age-width configurations; 566 state checks |
| Six-camera frame pose | 266 cases: 230 enabled C cases, 36 exact static bypass cases; four reset phases |
| Lease pose + trigger epoch | 21 leases; independent EO/IR capture; bundled 65,536-increment trigger wrap test |
| Wire-level I2C | 109 checks |
| Capture coverage + single selection + marker | 116 coverage checks, four ordered descriptors, 19 selector checks, marker-retirement test |
| Renderer `-Suite All` | Eight table cases; legacy and gravity each compare eight retained rasters and 14,112,000 pixels exactly |

The gravity renderer simulates nine passes because `ir_mixed` is repeated to verify table reuse. That repeated pass writes the same filename, so eight retained rasters—not nine—are compared. The two interfaces together compare 28,224,000 pixels; this is not 28,224,000 distinct geometry cases.

All ten top-level logs, `progress.txt`, the fresh math results, and selected fresh internal logs are preserved byte-for-byte. Old epoch-history snapshots that remained in the build directory were deliberately excluded. Seven nonfatal unconnected-port warnings from the capture tests are retained in the JSON/logs; the record does not claim warning-free compilation.

This is finite functional/numerical regression evidence. The exhaustive capture-envelope endpoint enumeration, full-top route/timing/CDC audits, MCU journal/HAL tests, and physical stabilization/latency/throughput tests were **not** rerun by these ten commands. Fresh route evidence is recorded separately. The directed capture tests must not be presented as a new exhaustive geometric proof.
