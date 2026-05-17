"""
DOTSun — Comparateur de Stratégies de Gestion de Parc PV
Deployable on share.streamlit.io
"""

import math
import streamlit as st
import plotly.graph_objects as go

# ── Page config ───────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="DOTSun — Comparateur Stratégies PV",
    page_icon="🌞",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Presets ───────────────────────────────────────────────────────────────────
PRESETS = {
    "s1": dict(n=40000, Pm=300.0, H=1200.0, Y=10.0, d=0.4, dn=6.0,
               N=10.0, tarif=0.0818, PPA=0.03, N1=5.0, N2=10.0,
               Crep=25.0, Cdm=4.0, Cde=15.0, Cfac=0.25, Crev=0.5,
               Down_rep=1.0, Down_repow=8.0, u=10.0, alpha_pct=85.0),
    "s2": dict(n=4304, Pm=195.0, H=1180.0, Y=14.0, d=0.45, dn=6.0,
               N=6.0, tarif=0.75, PPA=0.03, N1=0.0, N2=15.0,
               Crep=30.0, Cdm=5.0, Cde=18.0, Cfac=0.30, Crev=0.70,
               Down_rep=1.0, Down_repow=8.0, u=10.0, alpha_pct=80.0),
}

PARAM_KEYS = list(PRESETS["s1"].keys())


def init_state(key: str):
    for k, v in PRESETS[key].items():
        st.session_state[f"p_{k}"] = v


if "initialized" not in st.session_state:
    init_state("s1")
    st.session_state.initialized = True


# ── Calculations ──────────────────────────────────────────────────────────────
def compute(p):
    n          = float(p["n"])
    Pm         = float(p["Pm"])
    H          = float(p["H"])
    Y          = float(p["Y"])
    d          = float(p["d"]) / 100.0
    dn         = float(p["dn"]) / 100.0
    N          = int(p["N"])
    tarif      = float(p["tarif"])
    PPA        = float(p["PPA"])
    N1         = int(p["N1"])
    N2         = int(p["N2"])
    Crep       = float(p["Crep"])
    Cdm        = float(p["Cdm"])
    Cde        = float(p["Cde"])
    Cfac       = float(p["Cfac"])
    Crev       = float(p["Crev"])
    Down_rep   = float(p["Down_rep"])
    Down_repow = float(p["Down_repow"])
    u          = float(p["u"]) / 100.0
    alpha_rep  = float(p["alpha_pct"]) / 100.0

    Pcentrale = n * Pm / 1000.0
    I2        = (1.0 - d) ** Y
    alpha_rev = 1.0 - alpha_rep
    P_res_rep = alpha_rep * n * Pm * I2 / 1000.0
    gap_kWc   = max(0.0, Pcentrale - P_res_rep)
    n_rev     = alpha_rev * n
    Pm_fac    = gap_kWc * 1000.0 / n_rev if n_rev > 0 else 0.0

    capex = {
        "defaut": 0.0,
        "rep":    n * (Crep + Cdm),
        "rev":    n * (Pm * Cfac + Cdm),
        "repow":  n * Cde + Pcentrale * 1000.0 * (1.0 + u) * Crev,
        "mix":    alpha_rep * n * (Crep + Cdm) + gap_kWc * 1000.0 * Cfac,
    }

    def power(s, k):
        if s == "defaut": return Pcentrale * I2 * (1.0 - dn) ** (k - 1)
        if s == "rep":    return Pcentrale * I2 * (1.0 - d)  ** (k - 1)
        if s == "rev":    return Pcentrale        * (1.0 - d)  ** (k - 1)
        if s == "repow":  return Pcentrale * (1.0 + u) * (1.0 - d) ** (k - 1)
        if s == "mix":    return Pcentrale        * (1.0 - d)  ** (k - 1)

    def dfactor(s, k):
        if s == "defaut": return 1.0
        if s == "repow":  return (1.0 - Down_repow / 12.0) if k == N else 1.0
        return (1.0 - Down_rep / 12.0) if k == 1 else 1.0

    ext    = {"defaut": N1, "rep": N1, "rev": N1, "repow": N2, "mix": N1}
    strats = ["defaut", "rep", "rev", "repow", "mix"]

    revOA = {}; revPost = {}; cfOA = {}; cfTotal = {}; delta = {}; pct = {}

    for s in strats:
        rOA   = sum(H * tarif * power(s, k) * dfactor(s, k) for k in range(1, N + 1))
        rPost = sum(H * PPA   * power(s, k)                  for k in range(N + 1, N + ext[s] + 1))
        revOA[s]   = rOA
        revPost[s] = rPost
        cfOA[s]    = rOA - capex[s]
        cfTotal[s] = cfOA[s] + rPost

    for s in strats:
        delta[s] = cfTotal[s] - cfTotal["defaut"]
        pct[s]   = delta[s] / cfTotal["defaut"] if cfTotal["defaut"] != 0 else 0.0

    return dict(
        Pcentrale=Pcentrale, I2=I2, alpha_rev=alpha_rev,
        gap_kWc=gap_kWc, n_rev=n_rev, Pm_fac=Pm_fac,
        capex=capex, revOA=revOA, revPost=revPost,
        cfOA=cfOA, cfTotal=cfTotal, delta=delta, pct=pct,
        ext=ext, strats=strats, N=N, u=u,
    )


# ── Formatters ────────────────────────────────────────────────────────────────
def fe(n):
    return f"{round(n):,} €".replace(",", " ")

def fes(n):
    a, s = abs(n), ("−" if n < 0 else "")
    if a >= 1e6: return f"{s}{a/1e6:.2f} M€"
    if a >= 1e3: return f"{s}{a/1e3:.1f} k€"
    return f"{s}{a:.0f} €"

def fp(n):
    return f"{'+'if n >= 0 else ''}{n*100:.1f} %"


# ── Header ────────────────────────────────────────────────────────────────────
st.markdown(
    """
    <div style="background:#1e293b;padding:14px 24px;border-radius:10px;
                margin-bottom:20px;display:flex;align-items:center;gap:16px">
      <span style="font-size:24px;font-weight:900;color:#f59e0b;letter-spacing:-0.5px">
        <span style="color:#fff">DOT</span>Sun
      </span>
      <span style="font-size:15px;color:#94a3b8">
        Comparateur de Stratégies de Gestion de Parc PV
      </span>
      <span style="font-size:11px;color:#475569;margin-left:auto">
        Défaut · Réparation · Revamping · Repowering
      </span>
    </div>
    """,
    unsafe_allow_html=True,
)

# ── Sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("### ⚙️ Paramètres")

    c1, c2 = st.columns(2)
    if c1.button("📋 Scénario 1", use_container_width=True, help="Grande centrale — 40 000 panneaux"):
        init_state("s1")
        st.rerun()
    if c2.button("📋 Scénario 2", use_container_width=True, help="Petite centrale — 4 304 panneaux"):
        init_state("s2")
        st.rerun()

    # ── Centrale
    st.markdown("#### Centrale solaire")
    n   = st.number_input("n — Nombre de panneaux",     min_value=1.0,   step=100.0, key="p_n")
    Pm  = st.number_input("Pm — Puissance/panneau (Wc)",min_value=1.0,   step=5.0,   key="p_Pm")
    Pcentrale_disp = n * Pm / 1000.0
    I2_preview     = (1.0 - st.session_state.get("p_d", 0.4) / 100.0) ** st.session_state.get("p_Y", 10.0)
    st.info(f"**Pcentrale** = {Pcentrale_disp:,.0f} kWc  ·  **I₂** = {I2_preview*100:.2f} %")
    H   = st.number_input("H — Productible (kWh/kWc/an)", min_value=500.0, max_value=2500.0, step=10.0, key="p_H")
    Y   = st.number_input("Y — Âge de la centrale (ans)", min_value=0.0,   max_value=30.0,  step=1.0,  key="p_Y")

    # ── Dégradation
    st.markdown("#### Dégradation")
    d   = st.number_input("d — Dégradation normale (%/an)",           min_value=0.0, max_value=5.0,  step=0.05, format="%.2f", key="p_d")
    dn  = st.number_input("dn — Dégradation accélérée Défaut (%/an)", min_value=0.0, max_value=30.0, step=0.5,  format="%.1f", key="p_dn")

    # ── Contrat
    st.markdown("#### Contrat & Revenus")
    N     = st.number_input("N — Années restantes OA",         min_value=1.0, max_value=20.0, step=1.0,  key="p_N")
    tarif = st.number_input("p — Tarif EDF OA (€/kWh)",        min_value=0.0, max_value=1.5,  step=0.001, format="%.4f", key="p_tarif")
    N1    = st.number_input("N1 — Extension Rép/Rev (ans)",    min_value=0.0, max_value=20.0, step=1.0,  key="p_N1")
    N2    = st.number_input("N2 — Extension Repowering (ans)", min_value=0.0, max_value=30.0, step=1.0,  key="p_N2")
    PPA   = st.number_input("PPA — Tarif post-OA (€/kWh)",    min_value=0.0, max_value=0.5,  step=0.005, format="%.3f", key="p_PPA")

    # ── Coûts
    st.markdown("#### Coûts des interventions")
    Crep  = st.number_input("Crep — Réparation (€/panneau)",         min_value=0.0, step=1.0,   key="p_Crep")
    Cdm   = st.number_input("Cdm — Démontage/Remontage (€/p.)",     min_value=0.0, step=1.0,   key="p_Cdm")
    Cde   = st.number_input("Cde — Démantèlement+recyclage (€/p.)", min_value=0.0, step=1.0,   key="p_Cde")
    Cfac  = st.number_input("Cfac — Panneau à façon (€/Wc)",        min_value=0.0, max_value=2.0, step=0.01, format="%.2f", key="p_Cfac")
    Crev  = st.number_input("Crev — EPC Repowering (€/Wc)",         min_value=0.0, max_value=3.0, step=0.01, format="%.2f", key="p_Crev")

    # ── Opérationnel
    st.markdown("#### Paramètres opérationnels")
    Down_rep   = st.number_input("Down_rep — Arrêt Rép/Rev (mois)",  min_value=0.0, max_value=12.0, step=0.5, format="%.1f", key="p_Down_rep")
    Down_repow = st.number_input("Down_repow — Arrêt Repow (mois)",  min_value=0.0, max_value=24.0, step=1.0, key="p_Down_repow")
    u_pct      = st.number_input("u — Uplift repowering (%)",        min_value=0.0, max_value=50.0, step=1.0, key="p_u")

    # ── Mix
    st.markdown("#### Mix Réparation + Revamping")
    alpha_pct = st.slider("α_rep — Part de panneaux réparables (%)", 0, 100, key="p_alpha_pct")
    st.caption(f"Réparation : **{alpha_pct} %** — Revamping : **{100 - alpha_pct} %**")

# ── Build params dict from session state ──────────────────────────────────────
params = {k: st.session_state[f"p_{k}"] for k in PARAM_KEYS}
r = compute(params)

# ── KPI row ───────────────────────────────────────────────────────────────────
k1, k2, k3, k4 = st.columns(4)
prod_base = r["Pcentrale"] * r["I2"] * params["H"]
k1.metric("Puissance nominale",        f"{r['Pcentrale']:,.0f} kWc")
k2.metric("Efficacité actuelle (I₂)",  f"{r['I2']*100:.1f} %",   f"après {int(params['Y'])} ans")
k3.metric("Production annuelle base",  f"{prod_base/1000:.0f} MWh/an")
k4.metric("Revenu annuel base",        f"{prod_base*params['tarif']/1000:.0f} k€/an")

st.markdown("<div style='margin-bottom:10px'></div>", unsafe_allow_html=True)

# ── Comparison table ──────────────────────────────────────────────────────────
TH = {
    "defaut": ("#374151", "Défaut",     "Inaction"),
    "rep":    ("#166534", "Réparation", "100 % panneaux"),
    "rev":    ("#1e3a5f", "Revamping",  "100 % panneaux"),
    "repow":  ("#4c1d95", "Repowering", f"+{int(params['u'])} % capacité"),
    "mix":    ("#92400e", "Mix Rép+Rev",f"{alpha_pct}% + {100-alpha_pct}%"),
}

def th_cell(s):
    c, title, sub = TH[s]
    return (f'<th style="background:{c};color:#fff;padding:10px 14px;'
            f'text-align:center;font-size:12px;font-weight:600;white-space:nowrap">'
            f'{title}<br><small style="font-weight:400;opacity:.85">{sub}</small></th>')

def td_c(content, bg=""):
    sty = f"padding:8px 14px;text-align:center;font-size:13px;color:#1e293b;border-bottom:1px solid #f1f5f9;{('background:'+bg+';') if bg else ''}"
    return f'<td style="{sty}">{content}</td>'

def td_l(label, bold=False):
    sty = "padding:8px 14px;text-align:left;font-size:12px;font-weight:500;color:#64748b;border-bottom:1px solid #f1f5f9"
    return f'<td style="{sty}">{"<strong>" if bold else ""}{label}{"</strong>" if bold else ""}</td>'

def delta_html(v, s):
    col = TH[s][0] if v > 0 else ("#dc2626" if v < 0 else "#64748b")
    return f'<span style="color:{col};font-weight:700">{fe(v)}</span>'

def pct_html(v):
    col = "#16a34a" if v > 0 else ("#dc2626" if v < 0 else "#64748b")
    return f'<span style="color:{col};font-weight:700">{fp(v)}</span>'

strats = r["strats"]
ext    = r["ext"]

rows = []

# Power after intervention
row = f'<tr>{td_l("Puissance après intervention")}'
row += td_c("—")
row += td_c(f"{round(r['Pcentrale'] * r['I2'])} kWc")
row += td_c(f"{round(r['Pcentrale'])} kWc")
row += td_c(f"{round(r['Pcentrale'] * (1+r['u']))} kWc")
row += td_c(f"{round(r['Pcentrale'])} kWc")
rows.append(row + "</tr>")

# Extension
row = f'<tr>{td_l("Extension post-OA")}'
for s in strats:
    row += td_c("—" if ext[s] == 0 else f"+{int(ext[s])} ans PPA")
rows.append(row + "</tr>")

# CAPEX
row = f'<tr>{td_l("CAPEX (€)")}'
for s in strats:
    row += td_c(fe(r["capex"][s]))
rows.append(row + "</tr>")

# Revenus OA
row = f'<tr>{td_l("Revenus cumulés EDF OA (€)")}'
for s in strats:
    row += td_c(fe(r["revOA"][s]))
rows.append(row + "</tr>")

# CF OA
row = f'<tr>{td_l("Cash Flow EDF OA (€)")}'
for s in strats:
    row += td_c(fe(r["cfOA"][s]))
rows.append(row + "</tr>")

# Revenus post-OA
row = f'<tr>{td_l("Revenus cumulés post-OA (€)")}'
for s in strats:
    row += td_c(fe(r["revPost"][s]))
rows.append(row + "</tr>")

# CF Total — highlighted
row = f'<tr style="background:#fefce8">{td_l("<strong>Cash Flow Total (€)</strong>")}'
best_s = max(["rep","rev","repow","mix"], key=lambda s: r["cfTotal"][s])
for s in strats:
    badge = ' <span style="background:#dcfce7;color:#15803d;font-size:10px;padding:2px 6px;border-radius:99px;font-weight:700">★</span>' if s == best_s else ""
    row += td_c(f'<strong>{fe(r["cfTotal"][s])}</strong>{badge}')
rows.append(row + "</tr>")

# Delta
row = f'<tr style="background:#f8fafc">{td_l("ΔCCF vs Défaut (€)")}{td_c("—")}'
for s in ["rep","rev","repow","mix"]:
    row += td_c(delta_html(r["delta"][s], s))
rows.append(row + "</tr>")

# Pct
row = f'<tr style="background:#f8fafc">{td_l("% vs Défaut")}{td_c("—")}'
for s in ["rep","rev","repow","mix"]:
    row += td_c(pct_html(r["pct"][s]))
rows.append(row + "</tr>")

table_html = f"""
<div style="overflow-x:auto;background:#fff;border-radius:12px;
            box-shadow:0 1px 3px rgba(0,0,0,.08);margin-bottom:16px">
  <table style="width:100%;border-collapse:collapse">
    <thead>
      <tr>
        <th style="background:#0f172a;color:#fff;padding:10px 14px;
                   text-align:left;width:200px;font-size:12px">Indicateur</th>
        {''.join(th_cell(s) for s in strats)}
      </tr>
    </thead>
    <tbody>{''.join(rows)}</tbody>
  </table>
</div>
"""
st.markdown(table_html, unsafe_allow_html=True)

# ── Bar chart ─────────────────────────────────────────────────────────────────
non_def = ["rep", "rev", "repow", "mix"]
bar_labels  = ["Réparation", "Revamping", "Repowering", "Mix Rép+Rev"]
bar_values  = [r["delta"][s] for s in non_def]
bar_colors  = [TH[s][0] if r["delta"][s] >= 0 else "#e5e7eb" for s in non_def]
bar_texts   = [fes(v) for v in bar_values]

fig = go.Figure(go.Bar(
    x=bar_labels,
    y=bar_values,
    marker_color=bar_colors,
    marker_line_width=0,
    text=bar_texts,
    textposition="outside",
    textfont=dict(size=12),
))
fig.update_layout(
    title=dict(text="Gain brut vs Défaut — ΔCCF", font=dict(size=14, color="#374151")),
    yaxis=dict(tickformat=",.0f", gridcolor="#f1f5f9"),
    xaxis=dict(showgrid=False),
    showlegend=False,
    plot_bgcolor="white",
    paper_bgcolor="white",
    height=280,
    margin=dict(t=45, b=10, l=70, r=20),
)
fig.add_hline(y=0, line_color="#94a3b8", line_width=1)
st.plotly_chart(fig, use_container_width=True)

# ── Notes ─────────────────────────────────────────────────────────────────────
with st.expander("📋 Hypothèses & Définitions"):
    st.markdown("""
    | Stratégie | Définition |
    |---|---|
    | **Réparation** | Restitution de l'intégrité électrique du panneau — ne remet pas à zéro la dégradation naturelle des cellules. |
    | **Revamping** | Remplacement par des panneaux «à façon» (format & caractéristiques similaires) — panneaux neufs. |
    | **Repowering** | Remplacement complet (panneaux, structure, onduleur…) avec uplift de capacité. Arrêt plus long. |
    | **Mix Rép+Rev** | Panneaux réparables → réparés ; non réparables → remplacés à façon pour revenir à la puissance nominale. |
    | **Défaut** | Aucune intervention — dégradation accélérée (dn) appliquée chaque année. |

    - O&M annuel (nettoyage, inspection…) exclu — considéré identique pour toutes les stratégies.
    - Post-OA : valorisation au tarif PPA / agrégateur. Réparation & Revamping : +N1 ans. Repowering : +N2 ans.
    - Le scénario Défaut bénéficie également de N1 années post-OA (à dégradation accélérée).
    """)
