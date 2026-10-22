# Frame-Coherent Gravity-Locked EO/IR Panorama Stabilization

IEEE Transactions on Circuits and Systems for Video Technology manuscript.
The revision uses the implemented DDR capture/replay architecture, exact
fixed-point camera projection, source-frame/pose association, recorded camera
and pipeline measurements, and a matched-pair reanalysis of saved stitching
outputs. The manuscript limit is **14 pages including references**; normal
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

## Source and figures

- `g_locked_panorama_stabilization.tex`: title, abstract, introduction, related
  work, section inclusion, conclusion.
- `sections/`: geometry/timing definitions, numerical algorithm and architecture,
  verification, archived software evaluation, hardware evidence, discussion.
- `g_locked_panorama_stabilization.bib`: corrected references used by the paper.
- `figures/gl_*.tex`: native vector geometry, runtime flow, and hardware diagrams.
- `figures/legacy_matched_comparison.pdf`: plot derived from the archived-output
  reanalysis. Rebuild with `python scripts/render_evidence_figures.py`.
- Older raster illustrations are retained for provenance but are not used to
  support unverified quantitative video claims in the revised manuscript.

## Evidence and review

- `evidence/scientific_review.md`: critical review of the original paper,
  citation corrections, comparison limitations, and TCSVT policy links.
- `evidence/algorithm_audit.md`: exact implementation paths, hashes, calibration,
  arithmetic and memory contracts.
- `evidence/hardware_audit.md` and `hardware_summary.json`: classified routed,
  historical live FPS/latency, camera synchronization, and DNR evidence.
- `evidence/recompute_legacy_overlap.py`, `legacy_overlap_reanalysis.json`, and
  `legacy_overlap_per_seam.csv`: 12 shared target identities, nine common
  successes, explicit SIFT failures, and 130 hashed source inputs. The script
  reads the separately stored original dataset; it does not rerun models.
- `evidence/filter_boundary/`: a reproduced zero-gradient numerical defect in
  the copied MCU filter, distinguished from physical sensor behavior. The
  original firmware is not changed by this paper task.

Exact C/RTL and pixel agreement establish consistency with their respective
references. Routing establishes implementation timing under its constraints.
Historical camera/pipeline measurements retain their original configuration
and event boundaries. The author's report of live functionality does not
supply independent dynamic leveling statistics. Source datasets are identified
by path/hash; this repository does not claim to publish every original capture.

Authors: Muhammad Awais and Youngbae Hwang, Chungbuk National University.
