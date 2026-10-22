# Scientific evidence review

Reviewed 2026-10-22/23. This report concerns the **original manuscript at commit
`4d2b5a7`**, not the replacement manuscript being edited concurrently. Its TeX
blob SHA-256 is `90d620d0bdf86fb60970cae85c8e4f2094d7b3c573f9954a503e3c21d47d06a2`;
its bibliography blob SHA-256 is
`61a019fd59bb317b8c8ef17a3a51bf9220b6d5a68383093c129d9b081f661add`.
Original manuscript line numbers below refer to that committed TeX. This is a
scientific and provenance audit, not a certification of the physical system.

## Recommendation

Retain the calibrated rig motivation, the exact fixed-point implementation and
its independently documented regression/build evidence, and a narrowly scoped
reanalysis of archived static stitching outputs. Remove unsupported universal
claims about post-stitch correction, IR superiority, temporal accuracy, memory
advantages, and statistical significance. Do not present the untraced video,
fiducial, or filter tables as established measurements. A successful numerical
regression proves consistency with its reference, not physical leveling
accuracy; a routed implementation proves feasibility under its constraints,
not measured exposure synchronization or sustained throughput.

## Critical mathematical and experimental issues

| Issue in original paper | Finding and recommended action |
|---|---|
| “IHR is invariant to any single global warp” (line 739), hence only per-camera correction can remove it | False. Least-squares detrending removes additions `a*x+b` on fixed support. It does not create invariance to arbitrary affine/projective/nonlinear warps. Remove the universal theorem and the word *irreducible*. |
| Synthetic “true” horizon generated from accelerometer attitude and corrected using inertial attitude (lines 726–745) | This is an internal model-consistency diagnostic with correlated reference/input errors. It cannot independently establish absolute gravity accuracy. Preserve only with the full generator and explicit assumptions, otherwise omit its numbers. |
| Optical flow “cannot” remove the measured defect (lines 818, 845) | A particular tested stabilizer may not remove it, but mesh, dense-flow, spherical, and deformable methods are not all a single planar transform. Compare named implementations and objectives. |
| “Statistically identical” raw/flow values (line 818) | Means alone do not establish equivalence. No confidence intervals, equivalence bounds, paired uncertainty analysis, or independent repeat counts were located. Use descriptive wording only if raw data becomes available. |
| ArUco angle standard deviation validates leveling (lines 747, 836, 845) | Standard deviation measures orientation steadiness, not absolute bias or accuracy relative to gravity. Need marker mounting reference, corner residuals, frame identities, distortion handling, and detection/exclusion logs. |
| Every stitching method has the same sample count; StabStitch++ 12/30 indicates failures | Its wrapper intentionally uses only cameras 0–2 and two pairs per case. Reanalyse common target identities and retain actual failures separately. |
| All pretrained deep baselines run without fine-tuning | The archived UDIS++ wrapper requests 30 adaptation iterations; its code performs optimizer updates. Describe this budget accurately. |
| Only G-locked generalizes to IR (line 871) | IR baselines were not run. An anticipated out-of-domain failure is not an observed failure. Remove comparative IR generalization claims. |
| Two-line streaming/memory comparison | The implemented architecture must be described from actual source/routed evidence, including DDR, source rings, output buffering, ROMs and interfaces. Do not treat an earlier proposal as measured implementation. |

For the detrending claim, write `r=(I-P)y`, where `P` projects onto the columns
`[1,x]`. Then `(I-P)(y+a*x+b)=r`. In contrast, a global vertical scale gives
`(I-P)(c*y)=c*r`, changing the norm unless `|c|=1`. Rotation changes abscissae
and sampling; a projective or spherical warp is still less restricted. In an
ideal central panorama, a global 3-D rotation followed by reprojection can
level a tilted horizon. Blending and occlusion may destroy recoverable source
information, but that does not establish the claimed general impossibility.
Pixel-to-angle conversion must also use the actual local projection scale,
not an unexplained universal constant.

An acceleration-magnitude gate is a useful heuristic, not a guarantee of a
gravity-only direction: non-gravitational acceleration can alter direction
while leaving the norm near `g`. Agreement between filters is not ground
truth. Delay times angular velocity is a local first-order estimate, not an
end-to-end error bound without actual exposure and transport timing.

## Located evidence and reproducibility boundaries

The bounded search examined file inventories and relevant text/scripts under
`C:/SVNProjects/IMU_Stabilize_v40`, especially `DL_Comparison`,
`IMU_stabilize_GYRO`, `Research_article`, and the paper folders. It looked for
evaluation Python/CSV/XLSX files and text terms including `irreducible`,
`horizon_ripple`, `IHR`, `Outdoor-1`, `filter_calibration`, and `lag_ms`, while
avoiding broad binary reads and irrelevant driver/vendor trees. Figures alone
were not accepted as measurement provenance. “Not located” below means not
found in this bounded search, not proof that another archive does not exist.

The supporting static archive is `C:/SVNProjects/IMU_Stabilize_v40/DL_Comparison`:

| Evidence | What it supports |
|---|---|
| `scripts/compile_excel.py`, `results/stitching_comparison_v2.xlsx` | Original summary formulas and unequal sample counts. `load_stab_eo` at lines 140–149 selects only pairs 0–1 and 1–2. IR handling at line 353 explicitly says deep baselines were not evaluated. |
| `scripts/prep_inputs.py:14,52–54` | StabStitch++ receives 16 duplicates of each static image from cameras 0,1,2; this is not a dynamic-video comparison. |
| `scripts/run_udis.py:14–23`; `methods/UDIS2/Warp/Codes/test_other.py:67,99–113` | Configured adaptation budget 30; Adam, training mode, backward pass and optimizer step. Saved outputs remain the evidence of results; the wrapper suppresses process output and does not enforce subprocess success. |
| `results/eo_manifest.json` | Named cases, source paths and calibration configuration. These are configuration identities, not proof of independent scenes or physical-angle ground truth. |
| `data/glock_runs/strips_*_stab` | Saved pre-blend calibrated per-camera strips. |
| `data/udis_pairs/<case>/pair_*/warp*.jpg`, `mask*.jpg` | Saved UDIS warped views and masks, with JPEG encoding. |
| `results/stab_warps/<case>/warp*.png`, `mask*.png` | Saved three-view StabStitch++ outputs and masks. The local dump code maps warp0/1/2 to camera0/1/2. |
| `results/homo_metrics.json`, `scripts/run_homo.py` | SIFT statuses and metrics evaluated using original in-memory masks; retaining JSON avoids substituting reconstructed JPEG masks. |

No underlying evaluation scripts/data/logs were located for the original
0.830-to-0.078-degree horizon claim, 7.40-to-1.18-degree marker claim,
97–98% spatial spectral-energy claim, 22/42-ms filter delays, 0.14–0.31-degree
filter agreement, or 48-frame synchronization offset. Original tables and
figures are therefore unverified historical assertions. The rewrite should
omit those numerical claims until their source runs and metric pipelines can
be supplied. This conclusion does not prevent separately sourced hardware
measurements from being retained with their own configuration boundaries.

## Defensible quantitative reanalysis

`recompute_legacy_overlap.py` reads saved images/JSON, never runs a model or
renderer, and writes only derived summaries. Run from the paper repository:

```powershell
python evidence/recompute_legacy_overlap.py --source C:/SVNProjects/IMU_Stabilize_v40/DL_Comparison --output evidence
```

The completed run records Python 3.9.6, NumPy 1.25.2, OpenCV 4.8.0 and
scikit-image 0.21.0. `legacy_overlap_reanalysis.json` records input paths,
sizes and SHA-256 hashes, script hash, target identities, all statuses,
output canvas sizes, metric conventions and software versions.
`legacy_overlap_per_seam.csv` contains all 48 method/case/pair rows. The private
raw captures and implementation sources are not copied into this repository.
The summaries are reproducible when the identified archive is supplied;
they are not an independently redistributable raw benchmark.

The target set is six named EO cases times pairs 0–1 and 1–2, for 12 identities.
The formula preserves legacy grayscale PSNR and mean local SSIM, a 5-by-5
erosion, and optional Gaussian sigma 2 on each method's output grid. Means
weight seams equally. No arbitrary finite score is assigned to failures.

| Method | Available/target | Raw PSNR | Smoothed PSNR | Raw SSIM | Smoothed SSIM |
|---|---:|---:|---:|---:|---:|
| G-locked | 12/12 | 15.0545 | 22.5880 | .310705 | .752326 |
| UDIS++ | 12/12 | 13.4675 | 16.8760 | .204589 | .424334 |
| StabStitch++ | 12/12 | 12.8249 | 15.5610 | .213082 | .450373 |
| SIFT + homography | 9/12 | 13.2433 | 16.1614 | .304397 | .533805 |

The SIFT failures are `EO_Test2_R_2.15_P_0/pair_01`,
`EO_Test5_R_4.75_P_-4.5/pair_12`, and
`EO_Test6_R_1.25_P_6.5/pair_01`. Its mean above is therefore not a paired
comparison with the three 12-output means. On the **same nine successful
identities for every method**, the result is:

| Method | Raw PSNR | Smoothed PSNR | Raw SSIM | Smoothed SSIM |
|---|---:|---:|---:|---:|
| G-locked | 15.1571 | 22.5622 | .334915 | .756500 |
| UDIS++ | 13.6293 | 17.0906 | .229182 | .442320 |
| StabStitch++ | 12.9524 | 15.6041 | .234248 | .466166 |
| SIFT + homography | 13.2433 | 16.1614 | .304397 | .533805 |

These values support the descriptive statement that the calibrated output
has higher recorded photometric scores under this archived protocol. They do
not support a general method ranking or a significance claim. The common-nine
result is conditional on SIFT success, and the 12-target failure table must
remain visible. Matching identity does not equalize:

- **Masks:** G-locked uses intensity greater than 3 in both images, which can
  exclude dark content; other methods use explicit masks greater than 127.
- **Scale and sampling:** G-locked uses a 3840-by-480 grid; baseline canvases
  vary. Gaussian sigma 2 therefore has different angular support. Cropping
  before filtering, boundary handling and JPEG encoding are inherited.
- **Information:** `prep_inputs.py:16,38–39` applies calibrated undistortion
  before preparing baseline inputs. G-locked additionally receives mounting
  and inertial inputs; the methods have different priors/adaptation, but it
  would be inaccurate to imply the baselines receive no calibration benefit.
- **Scene content:** PSNR/SSIM are cross-view similarity, not reference-image
  quality or correspondence error. Exposure, parallax, blur and uniform sky
  affect scores. The legacy “distant” mask is simply the top third of the
  method-specific overlap extent, with no depth annotation.
- **Coverage:** only two seams per case are matched; even the original
  five-seam analysis omits the 5–0 wraparound seam.

The original workbook's all-seam EO values can be traced but should not be
used as equal-sample comparisons: G-locked N=30, UDIS++ N=30, StabStitch++
N=12, SIFT N=24. The IR workbook has 25 seams over five named cases, with
descriptive mean raw/smoothed PSNR approximately 15.73/16.39 dB and SSIM
.519/.719. These do **not** support the original 16.4/.67 statement, the
claim that raw and smoothed scores coincide, or any IR-baseline superiority.
IR values were inspected in the workbook, not independently recomputed by
the new EO script. Prefer omitting them from the concise comparison section.

Camera0/1/2 raw-file hashes were grouped as a duplication check; no entire
triplet was byte-identical across the six case names. This does not establish
statistical independence. In particular, matching metric rows for EO_Test4
and EO_Test4C do not justify declaring them independent captures or asserting
that their raw files are identical.

## Other provenance and fairness corrections

The archived manifest uses EO `fx=1141.83474`, `fy=1142.43496`, distortion
`k1=-.163318`, `k2=.16594`, `k3=-.064582`, `p1=.000236`, `p2=.000773`.
Original experimental-setup line 708 uses a different set, including
`k1=-.34`, `k2=.11`, `p1=-.0016`, `p2=-.0024` and cylindrical focal parameter
about 1204.5. Each dataset/configuration must be distinguished; do not reuse
one parameter set as provenance for all archived, video and FPGA results.
Likewise, a claimed five-degree range cannot silently encompass named cases
with 6.25/6.5-degree pitch or a 5.9-degree illustrated roll.

`compile_excel.py:400–403` hardcodes 1.84 MB on-chip memory, 459 ms PC time,
892+99 MB UDIS and 210 MB Stab. The UDIS checkpoint files are 936291857 and
103613961 bytes, approximately 892.9 and 98.8 **MiB**. The loader restores
optimizer state, so checkpoint file size is neither pure network-weight
storage nor peak GPU memory. These values cannot be compared with a selected
on-chip buffer budget excluding DDR and maps to claim orders-of-magnitude
memory superiority. Use measured hardware resources, declared external
storage, and separately measured model runtime/peak memory if available.

## Prior work and bibliography corrections

The geometry novelty should be narrow. Calibrated rotational panorama mapping
is established; a shared map core assumes compatible intrinsics/distortion or
a preceding rectification. New value can lie in a fully specified fixed-point
algorithm, a source/pose association contract, and an implemented scheduling
architecture with tested limits. The reference-matching tests do not by
themselves establish a new estimator or geometric theorem.

Primary sources below were checked on 2026-10-22/23. A corrected subset is in
`sections/verified_references.bib`; merge by key rather than loading it beside
duplicate keys from the old bibliography. Bibliographic omissions are
preferable to invented volume/page metadata.

| Original key | Correction and primary source |
|---|---|
| `liu2016meshflow` | Ping Tan, not Peng Tan; include Bing Zeng. MeshFlow is spatially varying, not restricted to one global affine warp. [Microsoft Research](https://www.microsoft.com/en-us/research/publication/meshflow-minimum-latency-online-video-stabilization/) |
| `karpenko2011gyro` | Alexandre Karpenko and Jongmin Baek, not Andrey/Jonathan. Stanford technical report 2011-03. [Author project](https://graphics.stanford.edu/papers/stabilization/) |
| `shi2022deepfvs` | Zhenmei Shi, Fuhao Shi, Wei-Sheng Lai, Chia-Kai Liang, Yingyu Liang. Original author list is wrong. [CVF](https://openaccess.thecvf.com/content/WACV2022/html/Shi_Deep_Online_Fused_Video_Stabilization_WACV_2022_paper.html), [author preprint](https://arxiv.org/abs/2102.01279) |
| `nie2023parallax` | Parallax-Tolerant Unsupervised Deep Image Stitching; local warping and iterative adaptation are part of the method. [CVF](https://openaccess.thecvf.com/content/ICCV2023/html/Nie_Parallax-Tolerant_Unsupervised_Deep_Image_Stitching_ICCV_2023_paper.html), [official code](https://github.com/nie-lang/UDIS2) |
| `nie2025stabstitch2` | Journal title is **StabStitch++: Unsupervised Online Video Stitching with Spatiotemporal Bidirectional Warps**, not the ECCV title. Six authors; DOI 10.1109/TPAMI.2025.3568829. [Official code](https://github.com/nie-lang/StabStitch2), [author paper](https://arxiv.org/abs/2505.05001) |
| `yu2025sensorflow` | Jiyang Yu, Tianhao Zhang, Fuhao Shi, Lei He, Chia-Kai Liang. Dense warps should not be described as a single planar transform. [CVF paper](https://openaccess.thecvf.com/content/WACV2025/papers/Yu_SensorFlow_Sensor_and_Image_Fused_Video_Stabilization_WACV_2025_paper.pdf) |
| `james2023globalflow` | Jerin Geo James, Devansh Jain, Ajit Rajwade. [CVF paper](https://openaccess.thecvf.com/content/WACV2023/papers/James_GlobalFlowNet_Video_Stabilization_Using_Deep_Distilled_Global_Motion_Estimates_WACV_2023_paper.pdf) |
| `zhang2023minimum` | Zhuofan Zhang, Zhen Liu, Ping Tan, Bing Zeng, Shuaicheng Liu; CVF pages 23030–23039. [CVF](https://openaccess.thecvf.com/content/ICCV2023/html/Zhang_Minimum_Latency_Deep_Online_Video_Stabilization_ICCV_2023_paper.html) |
| `rao2023sim2realvs` | First author Qi Rao, not Qianyi Rao. [CVF](https://openaccess.thecvf.com/content/WACV2023/html/Rao_Sim2RealVS_A_New_Benchmark_for_Video_Stabilization_With_a_Strong_WACV_2023_paper.html) |
| `hamza2015panovideo` | Ameer Hamza, Rehan Hafiz, Muhammad M. Khan, Yongju Cho, Jihun Cha. This close multi-camera prior work already combines global and local correction. [Author institution](https://ksp.etri.re.kr/ksp/article/read?id=2960) |
| `kopf2016omnistab` | Spherical/3-D and deformable motion cannot be dismissed as global planar warping. [Author paper](https://johanneskopf.de/publications/omnistab/360_video_stabilization.pdf) |
| `tang2018joint360` | Chengzhou Tang, Oliver Wang, Feng Liu, Ping Tan; not Chi-Keung Tang. Author preprint has placeholder metadata, so use the verified 2019 arXiv record if publisher metadata cannot be checked. [Author preprint](https://arxiv.org/abs/1901.04161) |
| `lee2021deep3d` | Correct CVF pages 10621–10630, not 14117–14126. [CVF](https://openaccess.thecvf.com/content/CVPR2021/html/Lee_3D_Video_Stabilization_With_Depth_Estimation_by_CNN-Based_Optimization_CVPR_2021_paper.html) |
| `yu2021selfie` | Include Keli Cheng, Michel Sarkis and Ning Bi. [CVF paper](https://openaccess.thecvf.com/content/CVPR2021/papers/Yu_Real-Time_Selfie_Video_Stabilization_CVPR_2021_paper.pdf) |
| `han2021tmc` | Original page range is unsupported; omit until publisher-confirmed. Authors/title confirmed in [author PDF](https://yafengnju.github.io/YinPaper/TMC2020Han.pdf). |
| `suk2015hwstitch` | Prior fixed-homography hardware engine is directly relevant; DOI 10.4218/etrij.15.0113.1120. [Author institution paper](https://ksp.etri.re.kr/ksp/article/file/3840.pdf) |
| `jia2024fpga` | Metadata confirmed: Yu Jia, Ruibo Wang, Xianyang Jiang; Electronics 13(2):271, 2024. It studies seam search/fusion of already registered inputs. Its 142-fps figure is derived from simulation timing, not transferable to measured end-to-end panorama stabilization. Its device description combines incompatible vendor/family and part-name labels; do not reproduce that inconsistency. [Publisher](https://www.mdpi.com/2079-9292/13/2/271) |

Do not conflate CVF open-access pagination with different IEEE proceedings
pagination for some WACV papers. The supplied subset omits such ranges where
the two records were not reconciled. Brown and Lowe's [author paper](https://www.cs.ubc.ca/~lowe/papers/07brown.pdf)
supports calibrated rotational homography background; [Wang et al.'s author page](https://ece.uwaterloo.ca/~z70wang/publications/ssim.html)
supports SSIM attribution, not the inference that cross-view SSIM is physical
registration ground truth.

## TCSVT preparation constraints

The [official TCSVT submission policy](https://ieee-cas.org/tcsvt-submission-manuscript),
checked 2026-10-23, limits a Transactions Paper submission to 14 total pages
in IEEE two-column format, with PDF submission; it does not state a reference
exemption. The requested manuscript should therefore fit **14 pages including
references**, without shrinking fonts/margins. The abstract should be one
self-contained paragraph of 150–200 words. Supplemental datasets and
multimedia are permitted, so detailed manifests and validation logs can remain
outside the main text. Figures adapted from other publications require source
attribution and applicable permissions. Overlength charges begin at page 12.

For the revision, prioritize the mathematical contract, architecture and
evidence boundaries, one compact matched-output comparison, and sourced
hardware measurements. Remove unsupported old appendices rather than compress
them into unreadable tables. An independently referenced dynamic experiment
with identifiable FPGA/MCU images, exposure timing, pose reference and
source/output frame identities remains the central missing scientific
qualification for a strong claim of real-time gravity-leveling accuracy.
