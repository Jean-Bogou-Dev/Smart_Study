"""app.py — interface Streamlit de SmartStudy (thème sombre / doré).

Lancer :  streamlit run app.py

Contrat attendu du binôme 1 (chapitre = dict) :
  chapitre = {"id", "matiere", "titre", "coef", "difficulte", "maitrise",
              "duree_min", "derniere_revision" (ISO), "date_examen" (ISO)}
  engine  : stabilite(c), retention(c), urgence(c), selectionner(chapitres, minutes)
  storage : charger() -> list[dict],  sauvegarder(list[dict])
Si engine.py / storage.py n'existent pas encore, un moteur de secours est utilisé.
"""
import json
import math
from datetime import date, timedelta
from pathlib import Path

import streamlit as st

import analytics

SEUIL = 0.70

# ───────────────────────── Moteur (réel ou de secours) ─────────────────────────
try:
    from engine import retention, selectionner, stabilite, urgence
    from storage import charger, sauvegarder
except ImportError:
    DATA = Path("data/demo_plan.json")

    def stabilite(c):
        return 1.5 * c["maitrise"] ** 1.5  # jours

    def retention(c):
        t = (date.today() - date.fromisoformat(c["derniere_revision"])).days
        return math.exp(-t / stabilite(c))

    def urgence(c):
        j = max((date.fromisoformat(c["date_examen"]) - date.today()).days, 1)
        return (1 - retention(c)) * c["coef"] * (1 + 10 / j)

    def selectionner(chapitres, minutes):
        res, reste = [], minutes
        for c in sorted(chapitres, key=lambda c: urgence(c) / c["duree_min"], reverse=True):
            if c["duree_min"] <= reste:
                res.append(c)
                reste -= c["duree_min"]
        return res

    def _demo():
        d = lambda n: (date.today() - timedelta(days=n)).isoformat()
        ex = lambda n: (date.today() + timedelta(days=n)).isoformat()
        rows = [
            ("Maths", "Algèbre linéaire", 4, 4, 2, 45, 9, 12),
            ("Maths", "Probabilités", 4, 3, 3, 40, 6, 12),
            ("Maths", "Analyse num.", 4, 5, 2, 50, 12, 12),
            ("Réseaux", "Modèle OSI", 3, 2, 4, 30, 3, 20),
            ("Réseaux", "Routage", 3, 4, 2, 45, 8, 20),
            ("Réseaux", "TCP/UDP", 3, 3, 3, 35, 5, 20),
            ("Systèmes", "Processus", 3, 3, 3, 40, 7, 15),
            ("Systèmes", "Mémoire virtuelle", 3, 5, 1, 50, 10, 15),
            ("Algo", "Graphes", 5, 4, 2, 60, 6, 9),
            ("Algo", "Programmation dyn.", 5, 5, 1, 60, 11, 9),
            ("Algo", "Tris", 5, 2, 4, 25, 2, 9),
        ]
        return [dict(id=i, matiere=m, titre=t, coef=co, difficulte=di, maitrise=ma,
                     duree_min=du, derniere_revision=d(r), date_examen=ex(e))
                for i, (m, t, co, di, ma, du, r, e) in enumerate(rows)]

    def charger():
        if DATA.exists():
            return json.loads(DATA.read_text(encoding="utf-8"))
        return _demo()

    def sauvegarder(plan):
        DATA.parent.mkdir(exist_ok=True)
        DATA.write_text(json.dumps(plan, ensure_ascii=False, indent=2), encoding="utf-8")


# ───────────────────────────────── Style ──────────────────────────────────────
st.set_page_config(page_title="SmartStudy", page_icon="🧠", layout="wide")

st.markdown("""
<style>
.stApp {background: radial-gradient(circle at 20% 0%, #1a1a20 0%, #0b0b0d 55%);}
header[data-testid="stHeader"] {background: transparent;}
section[data-testid="stSidebar"] {background: #101013; border-right: 1px solid #202026;}
h1,h2,h3,p,span,label,div {color:#e8e8ec;}
.muted {color:#8a8a94 !important; font-size:.85rem;}
.big {font-size:2.2rem; font-weight:600; line-height:1.1; margin:0;}
.card {border-radius:24px; padding:22px 24px; height:200px; position:relative; overflow:hidden;
       border:1px solid #26262d;
       background: radial-gradient(circle at 85% 10%, rgba(245,165,36,.55), transparent 35%),
                   linear-gradient(160deg,#16161b,#08080a);}
.card.gold {background: linear-gradient(160deg,#f5a524 0%, #b45309 60%, #3b1d04 100%); border:none;}
.card.gold *, .card.gold .muted {color:#fff !important;}
.card .val {position:absolute; bottom:18px; left:24px; font-size:2.8rem; font-weight:600;}
.card .tag {position:absolute; bottom:24px; right:24px; font-size:.8rem;}
.tl {background:#121215; border:1px solid #1f1f25; border-radius:24px; padding:20px 24px;}
.tl .hours {display:flex; justify-content:space-between; color:#8a8a94; font-size:.8rem; margin-bottom:14px;}
.tl .row {position:relative; height:46px;}
.pill {position:absolute; height:38px; border-radius:20px; padding:0 14px; display:flex;
       align-items:center; gap:8px; background:#1d1d22; border:1px solid #2a2a31;
       font-size:.8rem; white-space:nowrap; overflow:hidden;}
.badge {border-radius:14px; padding:3px 10px; background:#26262c; font-size:.72rem;}
.dot {display:inline-block; width:7px; height:7px; border-radius:50%; margin-right:5px;}
.stButton>button {border-radius:20px; background:linear-gradient(90deg,#6f86a8,#93a7c6);
                  color:#0b0b0d; border:none; font-weight:600;}
.stTabs [data-baseweb="tab"] {color:#8a8a94;}
.stTabs [aria-selected="true"] {color:#fff;}
</style>
""", unsafe_allow_html=True)


# ──────────────────────────────── État ────────────────────────────────────────
if "plan" not in st.session_state:
    st.session_state.plan = charger()
if "valides" not in st.session_state:
    st.session_state.valides = set()
plan = st.session_state.plan


def maj_sauvegarde():
    sauvegarder(plan)


# ─────────────────────────────── Sidebar ──────────────────────────────────────
with st.sidebar:
    st.markdown("### 🧠 SmartStudy")
    minutes = st.slider("Temps dispo aujourd'hui (min)", 15, 300, 90, step=15)
    debut = st.slider("Heure de début", 6, 20, 9)

    with st.expander("➕ Ajouter un chapitre"):
        with st.form("add", clear_on_submit=True):
            matiere = st.text_input("Matière")
            titre = st.text_input("Chapitre")
            coef = st.number_input("Coefficient", 1, 10, 3)
            diff = st.slider("Difficulté ressentie", 1, 5, 3)
            maitrise = st.slider("Maîtrise", 1, 5, 2)
            duree = st.number_input("Durée de révision (min)", 10, 180, 40, step=5)
            exam = st.date_input("Date d'examen", date.today() + timedelta(days=14))
            if st.form_submit_button("Ajouter") and matiere and titre:
                plan.append(dict(id=max([c["id"] for c in plan], default=-1) + 1,
                                 matiere=matiere, titre=titre, coef=coef, difficulte=diff,
                                 maitrise=maitrise, duree_min=duree,
                                 derniere_revision=date.today().isoformat(),
                                 date_examen=exam.isoformat()))
                maj_sauvegarde()
                st.rerun()


# ─────────────────────────────── Calculs ──────────────────────────────────────
selection = selectionner(plan, minutes)
selection = sorted(selection, key=urgence, reverse=True)
ret_moy = sum(retention(c) for c in plan) / len(plan) if plan else 0
critiques = [c for c in plan if retention(c) < SEUIL]
faits = len([c for c in selection if c["id"] in st.session_state.valides])
total_min = sum(c["duree_min"] for c in selection)

# ─────────────────────────────── En-tête ──────────────────────────────────────
h1, h2 = st.columns([3, 1])
with h1:
    st.markdown('<p class="muted">Votre plan du jour</p>'
                '<p class="big">Restez dans le rythme aujourd\'hui</p>', unsafe_allow_html=True)
with h2:
    st.markdown(f'<p class="muted" style="text-align:right">{date.today():%d/%m/%Y}</p>'
                f'<p style="text-align:right">{len(critiques)} chapitre(s) sous {int(SEUIL*100)}%</p>',
                unsafe_allow_html=True)

st.markdown(f'<p class="muted">Objectifs du jour &nbsp; <b style="color:#fff">{faits}/{len(selection)}</b> '
            f'complétés</p>', unsafe_allow_html=True)

tab_apercu, tab_plan, tab_chap = st.tabs(["Aperçu", "Planning", "Chapitres"])

# ─────────────────────────────── Aperçu ───────────────────────────────────────
with tab_apercu:
    c1, c2, c3 = st.columns([1, 1, 1.7])
    with c1:
        h, m = divmod(total_min, 60)
        st.markdown(f'<div class="card"><span>Temps de révision</span>'
                    f'<div class="val">{h}h {m:02d}m</div></div>', unsafe_allow_html=True)
    with c2:
        st.markdown(f'<div class="card gold"><span>Rétention moyenne</span>'
                    f'<div class="val">{ret_moy*100:.0f}%</div>'
                    f'<div class="tag">tous chapitres</div></div>', unsafe_allow_html=True)
    with c3:
        st.markdown('<div class="card" style="padding:14px 18px"><span>Rétention par chapitre</span></div>',
                    unsafe_allow_html=True)
        # graphique placé sous la carte pour rester simple et lisible
    st.pyplot(analytics.barres_retention(plan, retention, SEUIL), use_container_width=True)

    # ── Timeline du jour ──
    st.markdown("#### Timeline du jour")
    H0, H1 = 8, 20
    span = (H1 - H0) * 60
    couleurs = ["#f472b6", "#4ade80", "#60a5fa"]
    noms = ["Haute priorité", "Important", "Faible"]
    n = max(len(selection), 1)
    rows, t = [], (debut - H0) * 60
    for i, c in enumerate(selection):
        left = max(t, 0) / span * 100
        width = min(c["duree_min"] / span * 100, 100 - left)
        k = min(i * 3 // n, 2)
        rows.append(f'<div class="row"><div class="pill" style="left:{left:.1f}%;width:{max(width,14):.1f}%">'
                    f'{c["titre"]} <span class="badge"><span class="dot" style="background:{couleurs[k]}">'
                    f'</span>{noms[k]}</span></div></div>')
        t += c["duree_min"]
    hours = "".join(f"<span>{h}h</span>" for h in range(H0, H1 + 1))
    st.markdown(f'<div class="tl"><div class="hours">{hours}</div>{"".join(rows)}</div>',
                unsafe_allow_html=True)

    st.markdown("#### Courbes d'oubli par matière")
    g1, g2 = st.columns([2, 1])
    g1.pyplot(analytics.courbes_oubli(plan, stabilite, retention, seuil=SEUIL))
    g2.pyplot(analytics.repartition_temps(selection))

# Planning 
with tab_plan:
    st.markdown(f"#### À réviser aujourd'hui — {total_min} / {minutes} min")
    if not selection:
        st.info("Rien à planifier : augmente le temps disponible.")
    for c in selection:
        a, b, d, e = st.columns([3, 1, 1, 1])
        a.markdown(f"**{c['titre']}** · <span class='muted'>{c['matiere']}</span>", unsafe_allow_html=True)
        b.markdown(f"{retention(c)*100:.0f}% retenu")
        d.markdown(f"{c['duree_min']} min")
        if c["id"] in st.session_state.valides:
            e.success("Fait ✓")
        elif e.button("Valider", key=f"v{c['id']}"):
            c["derniere_revision"] = date.today().isoformat()
            c["maitrise"] = min(5, c["maitrise"] + 1)
            st.session_state.valides.add(c["id"])
            maj_sauvegarde()
            st.rerun()

# ─────────────────────────────── Chapitres ────────────────────────────────────
with tab_chap:
    st.dataframe(
        [{"Matière": c["matiere"], "Chapitre": c["titre"], "Coef": c["coef"],
          "Maîtrise": c["maitrise"], "Rétention %": round(retention(c) * 100),
          "Urgence": round(urgence(c), 2), "Examen": c["date_examen"]}
         for c in sorted(plan, key=urgence, reverse=True)],
        use_container_width=True, hide_index=True)