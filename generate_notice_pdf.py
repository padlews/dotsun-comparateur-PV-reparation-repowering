"""
DOTSun — Générateur de la Notice d'Utilisation
Comparateur Financier PV — Scénarios de Rénovation

Usage : python generate_notice_pdf.py
Sortie : DOTSun_Notice_Utilisation.pdf
"""
import os
from datetime import date
from fpdf import FPDF

# ── Fonts ─────────────────────────────────────────────────────────────────────
def _find_font(name):
    candidates = [
        f"/usr/share/fonts/truetype/dejavu/{name}",
        f"/usr/share/fonts/dejavu/{name}",
        os.path.join(os.path.dirname(__import__("fpdf").__file__), "fonts", name),
    ]
    for path in candidates:
        if os.path.exists(path):
            return path
    return None

# DejaVu (Streamlit Cloud / Linux) — fall back to Arial on Windows
REG  = _find_font("DejaVuSans.ttf")
BOLD = _find_font("DejaVuSans-Bold.ttf") or _find_font("DejaVuSansCondensed-Bold.ttf")

if not REG:
    WIN_FONTS = "C:/Windows/Fonts"
    REG  = os.path.join(WIN_FONTS, "arial.ttf")
    BOLD = os.path.join(WIN_FONTS, "arialbd.ttf")
    if not os.path.exists(REG):
        raise FileNotFoundError(
            "Aucune police trouvée. Installez fonts-dejavu-core ou vérifiez C:/Windows/Fonts."
        )
    FONT_NAME = "ar"
else:
    FONT_NAME = "dv"

DISCLAIMER = (
    "Ce document est fourni à titre informatif. Les projections reposent sur des hypothèses "
    "de modélisation et ne garantissent pas les résultats futurs. "
    "DOTSun SAS décline toute responsabilité quant à leur utilisation décisionnelle."
)

# ── PDF class ─────────────────────────────────────────────────────────────────
class NoticePDF(FPDF):
    def __init__(self):
        super().__init__(unit="mm", format="A4")
        self.add_font(FONT_NAME, "",  REG)
        self.add_font(FONT_NAME, "B", BOLD)

    def _f(self, style="", size=9):
        self.set_font(FONT_NAME, style, size)

    def header(self):
        self._f("B", 12); self.set_text_color(30, 41, 59)
        self.cell(self.get_string_width("DOT"), 7, "DOT")
        self.set_text_color(245, 158, 11)
        self.cell(self.get_string_width("Sun"), 7, "Sun")
        self._f("", 7); self.set_text_color(100, 116, 139)
        self.cell(0, 7, "   Notice d'Utilisation — Comparateur Financier PV", ln=True)
        self.set_draw_color(203, 213, 225)
        self.line(8, self.get_y(), self.w - 8, self.get_y()); self.ln(2)

    def footer(self):
        self.set_y(-16)
        self.set_draw_color(203, 213, 225)
        self.line(8, self.get_y(), self.w - 8, self.get_y()); self.ln(1)
        self._f("B", 7); self.set_text_color(30, 41, 59)
        self.cell(self.get_string_width("DOT"), 4, "DOT")
        self.set_text_color(245, 158, 11)
        self.cell(self.get_string_width("Sun"), 4, "Sun")
        self._f("", 6); self.set_text_color(100, 116, 139)
        self.cell(0, 4, f"   DOTSun — Notice d'utilisation  |  Page {self.page_no()}")
        self.set_y(-11)
        self._f("", 5); self.set_text_color(148, 163, 184)
        self.set_x(self.l_margin)
        self.multi_cell(0, 3, DISCLAIMER)


pdf = NoticePDF()
pdf.set_auto_page_break(auto=True, margin=22)
M = pdf.l_margin  # left margin ≈ 10 mm
W = 210 - 2 * M   # usable width ≈ 190 mm

# ── Helpers ───────────────────────────────────────────────────────────────────
def section(title, color=(15, 23, 42)):
    pdf._f("B", 11); pdf.set_text_color(*color)
    pdf.cell(0, 7, title, ln=True)
    pdf.set_draw_color(203, 213, 225)
    pdf.line(M, pdf.get_y(), M + W, pdf.get_y()); pdf.ln(3)

def subsection(title):
    pdf._f("B", 9); pdf.set_text_color(30, 58, 95)
    pdf.cell(0, 6, title, ln=True)

def body(text, indent=0):
    pdf._f("", 8.5); pdf.set_text_color(30, 41, 59)
    pdf.set_x(M + indent)
    pdf.multi_cell(W - indent, 5, text)
    pdf.ln(1)

def bullet(text, indent=4):
    pdf._f("", 8.5); pdf.set_text_color(30, 41, 59)
    pdf.set_x(M + indent)
    pdf.multi_cell(W - indent, 5, f"•  {text}")

def param_header(cols, widths, bg=(15, 23, 42)):
    pdf.set_fill_color(*bg); pdf.set_text_color(255, 255, 255)
    pdf._f("B", 7.5)
    for label, w in zip(cols, widths):
        pdf.cell(w, 6, label, fill=True, border=0)
    pdf.ln()

def param_row(cells, widths, i, bold_first=True):
    bg = (248, 250, 252) if i % 2 == 0 else (255, 255, 255)
    pdf.set_fill_color(*bg)
    pdf.set_x(M)
    for j, (val, w) in enumerate(zip(cells, widths)):
        pdf._f("B" if j == 0 and bold_first else "", 7.5)
        pdf.set_text_color(30, 41, 59 if j == 0 else 71)
        pdf.cell(w, 5, val, fill=True, border=0)
    pdf.ln()

def group_header(label, width=W):
    pdf.set_fill_color(30, 41, 59); pdf.set_text_color(255, 255, 255)
    pdf._f("B", 8)
    pdf.cell(width, 6, f"  {label}", fill=True, border=0, ln=True)

# ── PAGE 1 — Couverture + Introduction ───────────────────────────────────────
pdf.add_page()

# Title block
pdf.ln(4)
pdf._f("B", 20); pdf.set_text_color(15, 23, 42)
pdf.cell(0, 10, "Comparateur Financier PV", ln=True)
pdf._f("B", 14); pdf.set_text_color(245, 158, 11)
pdf.cell(0, 8, "Scénarios de Rénovation — Notice d'Utilisation", ln=True)
pdf._f("", 8); pdf.set_text_color(100, 116, 139)
pdf.cell(0, 6, f"DOTSun SAS  |  Édition du {date.today().strftime('%d %B %Y')}", ln=True)
pdf.ln(4)
pdf.set_draw_color(245, 158, 11); pdf.set_line_width(0.8)
pdf.line(M, pdf.get_y(), M + W, pdf.get_y())
pdf.set_line_width(0.2); pdf.ln(6)

# Section 1 — Objet
section("1.  Objet de l'Application")

body(
    "Le Comparateur Financier PV est un outil de modélisation développé par DOTSun pour aider "
    "les exploitants de centrales solaires photovoltaïques à évaluer l'impact financier des "
    "différentes stratégies de rénovation en fin de contrat d'Obligation d'Achat (OA)."
)
body(
    "À l'approche ou à la fin du contrat OA, le producteur doit décider de l'avenir de son "
    "installation : la laisser dégrader naturellement, intervenir pour la réparer, la revamper "
    "ou procéder à un repowering. Chacun de ces choix implique un investissement (CAPEX) et des "
    "revenus futurs différents. L'application calcule et compare ces flux sur la durée totale "
    "d'exploitation post-intervention."
)
body(
    "L'outil modélise cinq stratégies et produit, pour chacune, un compte de résultat annuel "
    "complet (CA, EBITDA, EBIT, résultat net), un plan de trésorerie et des indicateurs "
    "synthétiques (ROE incrémental, DSCR) permettant une comparaison directe. "
    "Un rapport PDF exportable regroupe l'ensemble des résultats."
)
pdf.ln(2)

# Section 2 — Architecture
section("2.  Architecture de la Modélisation")

body(
    "Le moteur de calcul est organisé en trois couches :"
)
bullet("Paramètres d'entrée — saisis dans la barre latérale de l'interface : caractéristiques "
       "de la centrale, hypothèses de dégradation, contrat OA, coûts d'intervention et "
       "hypothèses financières (taux, fiscalité, financement).")
bullet("Calcul des revenus — pour chaque scénario et chaque année, la puissance active est "
       "calculée à partir de la puissance nominale et du taux de dégradation applicable. "
       "Le revenu annuel découle de la production (kWh = puissance × H) multipliée par le "
       "tarif en vigueur (OA pendant N ans, puis PPA pendant N1 ou N2 ans).")
bullet("Calcul financier — un plan de financement (fonds propres + emprunt amorti) est "
       "appliqué à chaque CAPEX. Le compte de résultat intègre les charges d'exploitation "
       "(O&M, OPEX, assurance, loyer) et la fiscalité. La trésorerie cumulée est comparée "
       "au scénario Défaut pour calculer les indicateurs incrémentaux.")
pdf.ln(3)

body(
    "Chronologie de la modélisation (par scénario) :"
)

# Timeline table
tl_cols = ["Phase", "Durée", "Tarification", "Puissance modélisée"]
tl_w    = [42, 28, 40, W - 42 - 28 - 40]
param_header(tl_cols, tl_w)
tl_rows = [
    ("Avant projet",       "Y ans",  "OA (historique)", "Pc × (1-d)^k, de 100% à I2"),
    ("OA restantes",       "N ans",  "Tarif OA",        "Continue depuis I2 selon scénario"),
    ("Post-OA — Rép/Rev",  "N1 ans", "PPA / agrég.",    "Depuis I2 (Rép.) ou Pc (Rev./Mix)"),
    ("Post-OA — Repow.",   "N2 ans", "PPA / agrég.",    "Depuis Pc × (1+u)"),
]
for i, row in enumerate(tl_rows):
    param_row(row, tl_w, i, bold_first=False)
pdf.ln(4)

# ── PAGE 2 — Les 5 Stratégies ─────────────────────────────────────────────────
pdf.add_page()
section("3.  Les Cinq Stratégies Modélisées")

body(
    "Chaque stratégie est caractérisée par son CAPEX, son point de départ en puissance après "
    "l'intervention et son taux de dégradation post-décision. Toutes partagent la même courbe "
    "\"avant projet\" (dégradation normale d jusqu'à la prise de décision)."
)
pdf.ln(1)

strats = [
    (
        "Défaut  (aucune intervention)",
        (55, 65, 81),
        "CAPEX = 0 €",
        "Aucune intervention réalisée. La centrale continue à fonctionner mais sa dégradation "
        "s'accélère (taux dn, typiquement 5–10 %/an). La puissance de départ est Pc × I2 "
        "(efficacité actuelle). C'est le scénario de référence auquel tous les autres sont comparés. "
        "Durée post-OA : N1 ans.",
    ),
    (
        "Réparation  (remplacement des panneaux défaillants)",
        (22, 101, 52),
        "CAPEX = alpha × n × (Crep + Cdm)",
        "Seuls les panneaux défaillants sont remplacés (fraction alpha). La puissance repart "
        "de Pc × I2 (même niveau qu'avant intervention) mais retrouve une dégradation normale d. "
        "L'investissement est limité. Durée post-OA : N1 ans.",
    ),
    (
        "Revamping  (remplacement total des panneaux)",
        (30, 58, 95),
        "CAPEX = n × (Pm × Cfac + Cdm)",
        "Tous les panneaux sont remplacés par des modules de puissance identique (fabrication "
        "façon). La centrale retrouve sa puissance nominale Pc (I2 = 100 %). "
        "Dégradation normale d appliquée ensuite. Durée post-OA : N1 ans.",
    ),
    (
        "Repowering  (remplacement et augmentation de puissance)",
        (185, 28, 28),
        "CAPEX = n × Cde + Pc × (1+u) × 1000 × Crev",
        "Remplacement complet des panneaux par des modules de puissance supérieure. "
        "La puissance installée passe à Pc × (1+u), avec u = gain de puissance en %. "
        "Cela nécessite le dépose des anciens modules (Cde) et la pose des nouveaux (Crev). "
        "Dégradation normale d. Durée post-OA : N2 ans (généralement plus longue).",
    ),
    (
        "Mix Réparation + Revamping",
        (120, 60, 20),
        "CAPEX = alpha × n × (Crep + Cdm) + gap_kWc × 1000 × Cfac",
        "Combinaison optimisée : une fraction alpha des panneaux est réparée (les défaillants), "
        "et la fraction complémentaire (1-alpha) est revampée avec des modules façon pour "
        "combler l'écart de puissance. La puissance repart à Pc (nominale). "
        "Dégradation normale d. Durée post-OA : N1 ans.",
    ),
]

colors_strat = [(55,65,81),(22,101,52),(30,58,95),(185,28,28),(120,60,20)]
for i, (title, col, capex, desc) in enumerate(strats):
    # Colored title bar
    pdf.set_fill_color(*col); pdf.set_text_color(255, 255, 255)
    pdf._f("B", 9)
    pdf.cell(W, 6, f"  {title}", fill=True, border=0, ln=True)
    # Content
    bg = (248, 250, 252) if i % 2 == 0 else (255, 255, 255)
    pdf.set_fill_color(*bg)
    pdf._f("B", 8); pdf.set_text_color(71, 85, 105)
    pdf.set_x(M); pdf.cell(W, 5, f"  {capex}", fill=True, border=0, ln=True)
    pdf._f("", 8); pdf.set_text_color(30, 41, 59)
    pdf.set_x(M + 4)
    pdf.multi_cell(W - 4, 5, desc, fill=False, border=0)
    pdf.ln(2)

# ── PAGE 3 — Paramètres de contrôle ──────────────────────────────────────────
pdf.add_page()
section("4.  Paramètres de Contrôle")

body(
    "Tous les paramètres sont ajustables dans la barre latérale de l'application. "
    "Les colonnes ci-dessous indiquent le symbole utilisé dans les formules, "
    "l'unité, une description et une valeur de référence indicative."
)
pdf.ln(1)

# Column widths: Symbole | Unité | Description | Valeur type
sw = [18, 16, W - 18 - 16 - 22, 22]
param_header(["Symbole", "Unité", "Description", "Val. type"], sw)

groups = [
    ("Centrale solaire", [
        ("n",          "panneaux",    "Nombre total de panneaux installés",             "4 000"),
        ("Pm",         "Wc",          "Puissance-crête nominale par panneau",           "300"),
        ("Pcentrale",  "kWc",         "Puissance totale installée = n × Pm / 1000",    "1 200"),
        ("H",          "kWh/kWc/an",  "Productible solaire annuel du site",             "1 200"),
        ("Y",          "ans",         "Âge actuel de la centrale",                      "10"),
    ]),
    ("Dégradation", [
        ("d",          "%/an",        "Dégradation annuelle normale des panneaux",      "0,40"),
        ("dn",         "%/an",        "Dégradation accélérée — scénario Défaut",        "6,0"),
        ("Eff-IV",     "%",           "Efficacité réelle mesurée sur site (courbe IV). 0 = calculée", "0 (opt.)"),
        ("I2",         "—",           "Efficacité à date = (1-d)^Y ou Eff-IV/100 (auto)", "0,96"),
    ]),
    ("Contrat & Revenus", [
        ("N",          "ans",         "Années restantes au contrat OA",                 "10"),
        ("tarif",      "€/kWh",       "Tarif de rachat EDF OA",                         "0,0818"),
        ("PPA",        "€/kWh",       "Tarif post-OA (agrégateur / PPA)",               "0,030"),
        ("N1",         "ans",         "Durée post-OA — Défaut, Réparation, Rev., Mix",  "5"),
        ("N2",         "ans",         "Durée post-OA — Repowering",                     "15"),
    ]),
    ("Coûts d'intervention", [
        ("Crep",       "€/panneau",   "Réparation DOTSun des panneaux (M.O. et matériel)", "25"),
        ("Cdm",        "€/panneau",   "Démontage & Remontage des panneaux",             "4"),
        ("Cde",        "€/panneau",   "Démontage complet de la centrale — avant Repowering", "15"),
        ("Cfac",       "€/Wc",        "Module à façon livré sur site (Rev. / Mix)",     "0,25"),
        ("Crev",       "€/Wc",        "Coût EPC projet Repowering",                    "0,50"),
    ]),
    ("Répartition Mix & Repowering", [
        ("alpha",      "%",           "Part des panneaux réparés dans le Mix",          "85"),
        ("u",          "%",           "Gain de puissance en Repowering (Pc -> Pc×(1+u))", "10"),
        ("Down_rep",   "mois",        "Immobilisation estimée Réparation / Revamping",  "1"),
        ("Down_repow", "mois",        "Immobilisation estimée Repowering",              "8"),
    ]),
    ("Hypothèses financières", [
        ("equity_pct", "% CAPEX",     "Part des fonds propres dans le financement",     "20"),
        ("loan_dur",   "ans",         "Durée de l'emprunt bancaire",                    "10"),
        ("int_rate",   "%",           "Taux d'intérêt annuel de l'emprunt",             "4,0"),
        ("infl_rate",  "%",           "Inflation annuelle sur les charges",             "2,0"),
        ("tax_rate",   "%",           "Taux d'imposition sur le résultat (IS)",         "25"),
        ("maint_pct",  "% CA",        "Maintenance annuelle",                           "5"),
        ("opex_pct",   "% CA",        "Autres charges d'exploitation (OPEX)",           "2"),
        ("ins_pct",    "% CA",        "Prime d'assurance annuelle",                     "1,5"),
        ("rent",       "€/an",        "Loyer annuel du site",                           "10 000"),
        ("amort_dur",  "ans",         "Durée d'amortissement linéaire du CAPEX",        "10"),
        ("treas_rate", "%/an",        "Rémunération de la trésorerie positive",         "1,0"),
    ]),
]

for grp_name, rows in groups:
    group_header(grp_name)
    for i, row in enumerate(rows):
        param_row(row, sw, i)
    pdf.ln(1)

# ── PAGE 4 — Résultats & Indicateurs ─────────────────────────────────────────
pdf.add_page()
section("5.  Résultats Produits par l'Application")

body(
    "L'interface est organisée en onglets. Voici ce que chacun contient :"
)
pdf.ln(1)

tabs = [
    ("Stratégie Rénovation",
     "Tableau comparatif des Cash Flows nets de CAPEX pour les 5 scénarios sur toute la durée "
     "modélisée. Affiche, pour chaque année et chaque scénario : le cash flow net de CAPEX, "
     "le delta cumulé vs Défaut et l'écart en pourcentage. "
     "La meilleure stratégie est identifiée automatiquement."),
    ("Synthèse Financière",
     "Vue d'ensemble sur une seule ligne par scénario : CAPEX, fonds propres, dette, "
     "CA cumulé, EBITDA cumulé, résultat net cumulé, trésorerie finale, "
     "delta trésorerie vs Défaut, ROE incrémental et DSCR moyen."),
    ("Défaut / Repowering / Réparation / Revamping / Mix",
     "Pour chaque scénario, un tableau financier annuel détaillé comprenant : "
     "la puissance active (kWc), le productible (MWh), le chiffre d'affaires, l'EBITDA, "
     "l'amortissement, l'EBIT, les intérêts d'emprunt, l'EBT, l'impôt, le résultat net, "
     "le remboursement de la dette, le cash flow net, la trésorerie cumulée et "
     "le DSCR annuel."),
]

for t_name, t_desc in tabs:
    subsection(f"Onglet : {t_name}")
    body(t_desc, indent=2)
    pdf.ln(1)

pdf.ln(2)
section("6.  Indicateurs Financiers Calculés")
pdf.ln(1)

ind_cols = ["Indicateur", "Formule / Définition"]
ind_w    = [52, W - 52]
param_header(ind_cols, ind_w)

indicators = [
    ("CAPEX",
     "Coût total d'intervention par scénario (0 pour Défaut)."),
    ("Fonds propres",
     "equity_pct % × CAPEX — apport direct de l'exploitant."),
    ("Dette",
     "(1 - equity_pct/100) × CAPEX — financement bancaire, remboursé sur loan_dur ans."),
    ("CA",
     "Puissance(s,k) × H × tarif(k)  avec tarif = OA si k ≤ N, sinon PPA."),
    ("EBITDA",
     "CA — charges d'exploitation (maint. + OPEX + assurance + loyer), indexées inflation."),
    ("Amortissement",
     "CAPEX / amort_dur (linéaire, sur amort_dur années à partir de l'an 1)."),
    ("EBIT",
     "EBITDA — Amortissement."),
    ("Intérêts",
     "Intérêts annuels de l'emprunt (amortissement constant, taux int_rate)."),
    ("EBT",
     "EBIT — Intérêts."),
    ("Résultat net",
     "EBT × (1 — tax_rate/100)  si EBT > 0, sinon EBT (pas de crédit d'impôt)."),
    ("Cash flow net",
     "Résultat net + Amortissement — Remboursement capital emprunt "
     "+ Intérêts trésorerie (treas_rate × tréso cumulée)."),
    ("Trésorerie cumulée",
     "Somme des cash flows nets depuis l'année 1 (départ = 0 ou — fonds propres)."),
    ("Δ Trésorerie vs Défaut",
     "Tréso. cumulée(scénario) — Tréso. cumulée(Défaut) — CAPEX  "
     "— mesure le gain net réel de l'investissement."),
    ("ROE incrémental",
     "Δ Trésorerie cumulée finale / Fonds propres investis  "
     "— rentabilité des capitaux propres engagés."),
    ("DSCR",
     "Debt Service Coverage Ratio = EBITDA / (Rembt. capital + Intérêts)  "
     "— ratio de couverture de la dette. Un DSCR ≥ 1,2 est considéré sain."),
]

for i, (ind, defn) in enumerate(indicators):
    param_row((ind, defn), ind_w, i)

pdf.ln(4)
section("7.  Export PDF du Rapport")

body(
    "Le bouton \"Télécharger le rapport PDF\" génère un document complet qui comprend :"
)
bullet("Page 1 — Paramètres du scénario (tableau centrales + hypothèses financières) "
       "et schéma vectoriel d'évolution de la puissance pour les 5 scénarios.")
bullet("Page 2 — Stratégie de Rénovation (comparatif Cash Flow net de CAPEX) + "
       "recommandation de la meilleure stratégie + Synthèse Financière + "
       "Hypothèses & Définitions.")
bullet("Pages 3 à 7 — Tableaux financiers annuels détaillés par scénario (format paysage).")
pdf.ln(4)

section("8.  Notes & Limites du Modèle")

notes = [
    "Le modèle ne simule pas d'indisponibilité partielle de la centrale pendant les travaux "
    "(Down_rep et Down_repow sont des paramètres d'information non encore intégrés au calcul).",
    "Les charges d'exploitation (O&M, OPEX, assurance) sont calculées en pourcentage du CA "
    "et indexées au taux d'inflation. Elles ne comprennent pas de coûts fixes supplémentaires "
    "liés à l'intervention elle-même.",
    "Le tarif PPA post-OA est supposé constant sur toute la durée N1 ou N2. "
    "Une évolution du tarif dans le temps n'est pas modélisée.",
    "La puissance active est calculée de manière déterministe (pas de variabilité météo "
    "ni de distribution de pannes). Le productible H est supposé constant chaque année.",
    "L'efficacité mesurée Eff-IV (mesure IV sur site) remplace le calcul théorique uniquement "
    "pour les scénarios Défaut et Réparation. Revamping, Mix et Repowering démarrent "
    "systématiquement depuis la puissance nominale (reset Pc ou Pc × (1+u)).",
    "La fiscalité est simplifiée : un taux d'IS unique est appliqué sur l'EBT positif. "
    "Les reports déficitaires ne sont pas modélisés.",
]
for note in notes:
    bullet(note)
    pdf.ln(1)

# ── Output ────────────────────────────────────────────────────────────────────
out = os.path.join(os.path.dirname(__file__), "DOTSun_Notice_Utilisation.pdf")
pdf.output(out)
print(f"Notice générée : {out}")
