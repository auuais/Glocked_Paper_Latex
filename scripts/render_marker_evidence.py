"""Plot paired, saved-video marker measurements; never opens original media."""
from pathlib import Path
import csv

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
with (ROOT / "evidence/video_audit_20261026/marker_detections.csv").open(
        encoding="utf-8", newline="") as handle:
    rows = list(csv.DictReader(handle))

plt.rcParams.update({"font.family": "serif", "font.serif": ["Times New Roman", "DejaVu Serif"],
                     "font.size": 8, "axes.labelsize": 8, "xtick.labelsize": 7,
                     "ytick.labelsize": 7, "pdf.fonttype": 42, "ps.fonttype": 42})
methods = [("unstab", "Raw", "#555555", "--"),
           ("of_stab", "Rigid flow", "#ad6821", ":"),
           ("our_stab", "IMU", "#006b83", "-")]
segments = [("150:600", "(a) 5-20 s", 444), ("900:1350", "(b) 30-45 s", 448)]
expected_std = {"150:600": {"unstab": 6.0921730883, "our_stab": 1.3168796801, "of_stab": 5.8301954061},
                "900:1350": {"unstab": 7.4097844718, "our_stab": 1.1771020585, "of_stab": 7.0786653130}}
fig, axes = plt.subplots(2, 1, figsize=(3.45, 3.05), sharey=True)
for ax, (segment, label, expected_n) in zip(axes, segments):
    common_sets = []
    for method, name, color, style in methods:
        selected = sorted((row for row in rows if row["segment"] == segment and row["method"] == method),
                          key=lambda row: int(row["frame_index"]))
        assert len(selected) == 450
        mask = np.array([row["paired_common_id15"] == "1" for row in selected])
        assert int(mask.sum()) == expected_n
        assert all(row["selected_id"] == "15" for row, keep in zip(selected, mask) if keep)
        common_sets.append({int(row["frame_index"]) for row, keep in zip(selected, mask) if keep})
        time = np.array([float(row["nominal_encoded_time_s"]) for row in selected])
        values = np.array([float(row["paired_centered_angle_deg"]) if keep else np.nan
                           for row, keep in zip(selected, mask)])
        assert abs(np.nanmean(values)) < 1e-10
        assert abs(np.nanstd(values) - expected_std[segment][method]) < 1e-9
        ax.plot(time, values, label=name, color=color, linestyle=style,
                linewidth=.85 if method != "our_stab" else 1.0)
    assert common_sets[0] == common_sets[1] == common_sets[2]
    start, stop = (int(index) / 30 for index in segment.split(":"))
    ax.set_xlim(start, stop)
    ax.set_ylim(-19, 19)
    ax.set_yticks([-15, 0, 15])
    ax.set_xticks(np.arange(start, stop + .1, 5))
    ax.text(.02, .94, label + "; N=" + str(expected_n), transform=ax.transAxes,
            va="top", fontsize=7, bbox={"facecolor": "white", "edgecolor": "none", "alpha": .9, "pad": 1})
    ax.set_ylabel("Centered angle (deg)")
    ax.set_xlabel("Encoded time (s)")
    ax.grid(color=".88", linewidth=.5)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
axes[0].legend(loc="lower center", bbox_to_anchor=(.5, 1.02), ncol=3,
               frameon=False, handlelength=2.4, columnspacing=1.1, borderaxespad=0)
fig.subplots_adjust(left=.15, right=.985, bottom=.12, top=.90, hspace=.49)
out = ROOT / "figures/archived_marker_steadiness"
fig.savefig(out.with_suffix(".pdf"), metadata={"CreationDate": None, "ModDate": None})
fig.savefig(out.with_suffix(".png"), dpi=200)
print("Rendered paired ID15 traces: N=444 and N=448; means removed separately; excluded frames left as gaps.")
