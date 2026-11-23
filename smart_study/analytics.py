"""analytics.py — graphiques matplotlib (thème sombre) pour SmartStudy.

Les fonctions reçoivent des fonctions de calcul (retention / stabilite) du moteur,
ce qui évite toute dépendance directe à engine.py.
"""
import math
from collections import defaultdict
from datetime import date

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

BG, GOLD, BLUE, GRID, TXT = "#0f0f12", "#f5a524", "#6f86a8", "#2a2a30", "#d8d8dc"
PALETTE = ["#f5a524", "#6f86a8", "#4ade80", "#f472b6", "#60a5fa", "#c084fc"]


def _style(fig, ax):
    fig.patch.set_facecolor(BG)
    ax.set_facecolor(BG)
    for s in ax.spines.values():
        s.set_visible(False)
    ax.tick_params(colors=TXT, labelsize=8)
    ax.grid(color=GRID, alpha=0.5, lw=0.6)
    ax.set_axisbelow(True)


def barres_retention(chapitres, ret_fn, seuil=0.7):
    """Barres de rétention actuelle par chapitre (dorées si sous le seuil)."""
    fig, ax = plt.subplots(figsize=(6, 2.6))
    _style(fig, ax)
    vals = [ret_fn(c) * 100 for c in chapitres]
    cols = [GOLD if v < seuil * 100 else BLUE for v in vals]
    ax.bar(range(len(vals)), vals, color=cols, width=0.6)
    ax.axhline(seuil * 100, ls="--", color="white", lw=1)
    ax.text(len(vals) - 0.5, seuil * 100 + 2, f"seuil {int(seuil * 100)}%",
            color="white", fontsize=8, ha="right")
    ax.set_xticks(range(len(vals)))
    ax.set_xticklabels([c["titre"][:8] for c in chapitres], rotation=35, ha="right")
    ax.set_ylim(0, 105)
    ax.grid(axis="x", visible=False)
    fig.tight_layout()
    return fig


def courbes_oubli(chapitres, stab_fn, ret_fn, jours=14, seuil=0.7):
    """Courbes R = exp(-t/S) projetées sur les prochains jours, par matière."""
    fig, ax = plt.subplots(figsize=(8, 3.8))
    _style(fig, ax)
    matieres = sorted({c["matiere"] for c in chapitres})
    couleur = {m: PALETTE[i % len(PALETTE)] for i, m in enumerate(matieres)}
    deja = set()
    for c in chapitres:
        s = stab_fn(c)
        t0 = (date.today() - date.fromisoformat(c["derniere_revision"])).days
        xs = [x / 4 for x in range(jours * 4 + 1)]
        ys = [math.exp(-(t0 + x) / s) * 100 for x in xs]
        label = c["matiere"] if c["matiere"] not in deja else None
        deja.add(c["matiere"])
        ax.plot(xs, ys, color=couleur[c["matiere"]], lw=1.6, alpha=0.85, label=label)
        ax.scatter([0], [ret_fn(c) * 100], color=couleur[c["matiere"]], s=18, zorder=3)
    ax.axhline(seuil * 100, ls="--", color="white", lw=1)
    ax.set_xlabel("jours à partir d'aujourd'hui", color=TXT, fontsize=9)
    ax.set_ylabel("rétention (%)", color=TXT, fontsize=9)
    ax.set_ylim(0, 105)
    leg = ax.legend(facecolor=BG, edgecolor=GRID, labelcolor=TXT, fontsize=8)
    leg.get_frame().set_alpha(0.8)
    fig.tight_layout()
    return fig


def repartition_temps(selection):
    """Donut du temps recommandé par matière."""
    fig, ax = plt.subplots(figsize=(4, 3.6))
    fig.patch.set_facecolor(BG)
    par_matiere = defaultdict(int)
    for c in selection:
        par_matiere[c["matiere"]] += c["duree_min"]
    if not par_matiere:
        ax.text(0.5, 0.5, "Aucune révision", color=TXT, ha="center", va="center")
        ax.axis("off")
        return fig
    labels, vals = zip(*par_matiere.items())
    ax.pie(vals, labels=[f"{l}\n{v} min" for l, v in zip(labels, vals)],
           colors=PALETTE[:len(vals)], startangle=90,
           wedgeprops=dict(width=0.38, edgecolor=BG),
           textprops=dict(color=TXT, fontsize=8))
    fig.tight_layout()
    return fig