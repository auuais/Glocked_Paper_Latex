"""Render the matched archived-output comparison; no network or model inference."""
from pathlib import Path
import csv
import json

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
record = json.loads((ROOT / "evidence/legacy_overlap_reanalysis.json").read_text(encoding="utf-8"))
with (ROOT / "evidence/legacy_overlap_per_seam.csv").open(encoding="utf-8", newline="") as handle:
    rows = list(csv.DictReader(handle))
targets = {(row["case"], row["pair"]) for row in record["common_success_targets"]}
methods = ["G-locked", "UDIS++", "StabStitch++", "SIFT+homography"]
labels = ["G-locked", "UDIS++", "StabStitch++", "SIFT+H"]
colors = ["#1b617a", "#7b8f9d", "#b38a50", "#8b779e"]
plt.rcParams.update({"font.family": "serif", "font.serif": ["Times New Roman", "DejaVu Serif"],
                     "font.size": 8, "axes.labelsize": 8, "xtick.labelsize": 7,
                     "ytick.labelsize": 7, "pdf.fonttype": 42, "ps.fonttype": 42})
fig, axes = plt.subplots(2, 1, figsize=(3.45, 3.05), sharex=True)
for ax, field, title, bounds in zip(axes, ["strP", "strS"],
                                  ["Smoothed overlap PSNR (dB)", "Smoothed overlap SSIM"],
                                  [(0, 32), (0, 1)]):
    for i, method in enumerate(methods):
        selected = sorted((r for r in rows if r["method"] == method and (r["case"], r["pair"]) in targets),
                          key=lambda r: (r["case"], r["pair"]))
        assert len(selected) == 9 and all(r["status"] == "ok" for r in selected)
        values = np.array([float(r["overlap_" + field]) for r in selected])
        expected = record["common_success_summary"][method]["overlap"]["mean"][field]
        assert abs(values.mean() - expected) < 1e-9
        ax.bar(i, values.mean(), color=colors[i], alpha=.35, width=.65, edgecolor=colors[i], linewidth=.7)
        ax.scatter(i + np.linspace(-.20, .20, len(values)), values, s=10, color=colors[i],
                   edgecolor="white", linewidth=.2, zorder=3)
        ax.plot([i-.26, i+.26], [values.mean()]*2, color="black", linewidth=1.1, zorder=4)
    ax.set_ylim(*bounds)
    ax.set_ylabel(title)
    ax.grid(axis="y", color=".88", linewidth=.5)
    ax.set_axisbelow(True)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
axes[-1].set_xticks(range(4))
axes[-1].set_xticklabels(labels)
fig.subplots_adjust(left=.16, right=.98, top=.98, bottom=.09, hspace=.12)
out = ROOT / "figures/legacy_matched_comparison"
fig.savefig(out.with_suffix(".pdf"), metadata={"CreationDate": None, "ModDate": None})
fig.savefig(out.with_suffix(".png"), dpi=200)
print("Rendered common-success nine pairs; dots are individual pairs, lines are means.")
