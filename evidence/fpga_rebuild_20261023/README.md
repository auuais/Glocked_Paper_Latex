# Fresh routed FPGA evidence, 2026-10-23

Source `5126c375957005e65dd000b2004fb01fbe1baaae`; Vivado 2025.2;
XCKU15P-FFVE1517-2-I. The complete guarded build reports `complete_verified`.
The JSON preserves full report/checkpoint/bitstream/probe hashes and parsed
timing, utilization, routing, CDC and scoped-audit outcomes. The source manifest
also records post-build verification of 137 registered inputs, 14 staged ROMs
and three build/audit scripts. Documentation commits made during the run do
not change those source bytes.

The selected raw reports and progress/inputs records are copied byte-for-byte.
`timing_summary_excerpt.rpt` is exactly lines 1–218 of the full timing report,
including check-timing counts, design timing, clocks and intra-clock summaries;
it is explicitly an excerpt. `archive_manifest.json` records each copy's hash
and origin. Full detailed timing, CDC and skew reports remain in the identified
local build directory; their hashes and parsed outcomes are in the main JSON.
Large bitstreams/checkpoints are not copied into the paper repository.

Setup/hold/pulse-width worst slacks are +0.022/+0.010/+0.009 ns; all 143,180
routable nets are routed and the 80 bus-skew checks pass (minimum +2.525 ns).
The full CDC report retains 131 Critical and 265 Warning entries. Timing lists
159 unconstrained inputs and 37 output-delay check entries (36 outputs plus
one clock port). These limits are not waived by scoped gravity audit success.

This run generated a bitstream and matching probes. It did not program an FPGA,
capture live video, measure exposure alignment, or measure dynamic accuracy,
current-build throughput or sensor-to-display latency.
