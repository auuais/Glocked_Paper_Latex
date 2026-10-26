# Frame-Coherent Gravity-Locked EO/IR Panorama Stabilization

IEEE Transactions on Circuits and Systems for Video Technology manuscript.
The revision uses the implemented DDR capture/replay architecture, exact
fixed-point camera projection, source-frame/pose association, recorded camera
and pipeline measurements, and matched reanalysis of saved stitching outputs
and physical-marker video measurements. The manuscript limit is **14 pages including references**; normal
IEEEtran journal typography and margins are retained.

## Local PDF build

Run from this directory with TeX Live (`latexmk`, `pdflatex`, `bibtex`) and
Poppler (`pdfinfo`) on PATH:

```powershell
./scripts/build_paper.ps1
```

The build writes `output/pdf/g_locked_panorama_stabilization.pdf`, mirrors a
successful build to `g_locked_panorama_stabilization.pdf` at the repository
root, and checks the page count, unresolved references, and overfull boxes. Generated output
is local and ignored by Git. The original 17-page PDF is preserved locally as
`output/baseline/manuscript_before_revision.pdf`; the original source remains
at commit `4d2b5a7`. No Overleaf connection or synchronization is used for this
revision. `origin` remains the existing GitHub paper repository.

The October 26 revised PDF is **12 pages including references**. Its exact
hash, staged source hashes and visual/layout checks are recorded in
`evidence/pdf_validation_20261026.json`. The previous 11-page version is retained
locally as `output/baseline/manuscript_20261023.pdf`, with its earlier validation
record preserved in `evidence/pdf_validation_20261023.json`.

## Source and figures

- `g_locked_panorama_stabilization.tex`: title, abstract, introduction, related
  work, section inclusion, conclusion.
- `sections/`: geometry/timing definitions, numerical algorithm and architecture,
  verification, archived static/video evaluation, hardware evidence, discussion.
- `g_locked_panorama_stabilization.bib`: corrected references used by the paper.
- `figures/gl_*.tex`: native vector geometry, runtime flow, and hardware diagrams.
- `figures/legacy_matched_comparison.pdf`: plot derived from the archived-output
  reanalysis. Rebuild with `python scripts/render_evidence_figures.py`.
  The recorded plotting environment is Python 3.9.6, NumPy 1.25.2 and
  Matplotlib 3.4.2. The saved figure permits compiling without Python.
- `figures/archived_marker_steadiness.pdf`: paired marker-orientation traces
  from two saved indoor intervals. Rebuild with
  `python scripts/render_marker_evidence.py`; the script checks paired support,
  means and standard deviations against the audited values.
- Older raster illustrations are retained for provenance. Current video claims
  use the recovered data and explicit measurement definitions below.

## Evidence and review

- `evidence/scientific_review.md`: critical review of the original paper,
  citation corrections, comparison limitations, and TCSVT policy links.
- `evidence/algorithm_audit.md`: exact implementation paths, hashes, calibration,
  arithmetic and memory contracts.
- `evidence/hardware_audit.md` and `hardware_summary.json`: classified routed,
  historical live FPS/latency, camera synchronization, and DNR evidence.
  The original summary retains its October 16 route record; the manuscript's
  updated route table uses the fresh October 23 archive below.
- `evidence/recompute_legacy_overlap.py`, `legacy_overlap_reanalysis.json`, and
  `legacy_overlap_per_seam.csv`: 12 shared target identities, nine common
  successes, explicit SIFT failures, and 130 hashed source inputs. The script
  reads the separately stored original dataset; it does not rerun models.
- `evidence/filter_boundary/`: a reproduced zero-gradient numerical defect in
  the copied MCU filter, distinguished from physical sensor behavior. The
  original firmware is not changed by this paper task.
- `evidence/regression_20261023/`: fresh ten-suite regression on source
  `5126c37`, with all suites passing, 28,224,000 exact pixel comparisons across
  two renderer interfaces, source hashes and byte-preserved logs. Finite
  functional tests are distinguished from geometric proofs and physical tests.
- `evidence/fpga_rebuild_20261023/`: fresh full synthesis/place/route and
  bitstream completion, with `complete_verified` acceptance, source/artifact
  hashes and selected raw reports. Setup/hold/pulse-width slacks are
  +0.022/+0.010/+0.009 ns. No FPGA or MCU programming was performed in this run.
- `evidence/video_audit_20261026/`: recovered source at
  `E:/D_Folder/download/test`, exact saved-video/IMU metric reproductions,
  per-frame derived data, hashes and safe CLI reproducers. The paper uses
  paired ID-15 marker measurements (448 and 444 common frames). Synthetic
  horizon and filter diagnostics remain in the audit because they do not
  establish independent physical accuracy or causal/system latency. The
  archive uses a RealSense IMU and an older software renderer, distinct from
  the current IIM46234 MCU/FPGA pipeline. Original media were not modified or
  copied into this public repository.

Exact C/RTL and pixel agreement establish consistency with their respective
references. Routing establishes implementation timing under its constraints.
Historical camera/pipeline measurements retain their original configuration
and event boundaries. The author's report of live functionality does not
supply independent dynamic leveling statistics. Source datasets are identified
by path/hash; this repository does not claim to publish every original capture.

Authors: Muhammad Awais and Youngbae Hwang, Chungbuk National University.
