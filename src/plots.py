#!/usr/bin/env python3
"""Generate methodology figures from derived/*.csv into docs/figures/.

    .venv/bin/python src/plots.py
"""
import csv, json, os, pathlib
os.environ["MPLBACKEND"] = "Agg"
import matplotlib
matplotlib.use("Agg", force=True)
import matplotlib.pyplot as plt

ROOT = pathlib.Path(__file__).resolve().parents[1]
DERIVED = ROOT / "derived"
FIGS = ROOT / "docs" / "figures"
FIGS.mkdir(parents=True, exist_ok=True)


def read_curve(path):
    xs, ys = [], []
    with open(path) as fh:
        for row in csv.DictReader(fh):
            xs.append(int(row["rank"]))
            ys.append(float(row["cum_share_pct"]))
    return xs, ys


tx, ty = read_curve(DERIVED / "top_forms.csv")
sx, sy = read_curve(DERIVED / "subtitles_curve.csv")

# ---- Figure 1: coverage curves -------------------------------------------
fig, ax = plt.subplots(figsize=(8, 4.8), dpi=150)
ax.axhline(95, ls=":", c="gray", lw=1.2,
           label="95% comprehension threshold (Laufer 1989)")
ax.plot(tx, ty, lw=2, label="Tatoeba deu corpus (this repo, 6.06M tokens)")
ax.plot(sx, sy, "o--", lw=2, ms=5,
        label="OpenSubtitles-2016 DE (independent measurement, 95.9M tokens)")
for x, lbl, c in [(2000, "core\n2,000", "tab:green"), (4000, "complete\n4,000", "tab:red")]:
    ax.axvline(x, ls="--", lw=1, alpha=0.6, c=c)
    ax.annotate(lbl, xy=(x, 55), xytext=(x * 1.3, 60), fontsize=8, color=c,
                arrowprops=dict(arrowstyle="-", color=c, alpha=0.5))
ax.set_xscale("log")
ax.set_xlim(80, 40000)
ax.set_ylim(40, 100)
ax.set_xlabel("top-k word forms (log scale)")
ax.set_ylabel("% of running tokens covered")
ax.set_title("Coverage of everyday German by vocabulary size")
ax.grid(alpha=0.25)
ax.legend(loc="upper left", fontsize=8, framealpha=0.95)
fig.tight_layout()
fig.savefig(FIGS / "fig1_coverage_curves.png")
plt.close(fig)

# ---- Figure 2: marginal gains --------------------------------------------
at = dict(zip(tx, ty))
ranks = list(range(500, 10001, 500))
gains = [at[b] - at[a] for a, b in zip(ranks[:-1], ranks[1:])]
labels = [f"{b:,}" for b in ranks[1:]]
fig, ax = plt.subplots(figsize=(8, 4.2), dpi=150)
ax.bar(range(len(gains)), gains, color="#4878CF")
ax.set_xticks(range(len(gains)))
ax.set_xticklabels(labels, rotation=60, fontsize=7)
ax.set_xlabel("cumulative word forms")
ax.set_ylabel("coverage gained per additional 500 forms")
ax.set_title("Pareto shape of German vocabulary: diminishing returns")
ax.grid(axis="y", alpha=0.25)
fig.tight_layout()
fig.savefig(FIGS / "fig2_marginal_gains.png")
plt.close(fig)

# ---- Figure 3: final deck pattern mix ----
sel_summary = DERIVED / "selection_summary.json"
if sel_summary.exists():
    s = json.load(open(sel_summary))
    labels, vals = [], []
    for g in ["routine", "perfekt_modal", "separable", "funkverb",
              "particle_connector", "bundle"]:
        for c, k in s["groups"][g]["classes"].items():
            labels.append(f"{c}  ({g})")
            vals.append(k)
    order = sorted(range(len(vals)), key=lambda i: vals[i])
    labels = [labels[i] for i in order]
    vals = [vals[i] for i in order]
    fig, ax = plt.subplots(figsize=(8, 4.6), dpi=150)
    ax.barh(labels, vals, color="#4878CF")
    for i, v in enumerate(vals):
        ax.text(v + 1, i, str(v), va="center", fontsize=8)
    ax.set_xlabel("cards in deck")
    ax.set_title("Deck composition: 500 pattern cards (D3/D4/D8)")
    ax.grid(axis="x", alpha=0.25)
    fig.tight_layout()
    fig.savefig(FIGS / "fig3_deck_pattern_mix.png")
    plt.close(fig)

print("figures written:", *[f.name for f in sorted(FIGS.glob('*.png'))])
