#!/usr/bin/env python3
"""
Génère comparateur_solaire.html — outil interactif de comparaison des stratégies PV.
Reproduit la logique du fichier Excel:
  Comparateur Cash Flow Defaut Reparation Revamping Repowering V4.xlsx

Usage:  python generate_comparateur.py
Output: comparateur_solaire.html
"""

OUTPUT = "comparateur_solaire.html"

HTML = """<!DOCTYPE html>
<html lang="fr">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Comparateur Stratégies PV — DOTSun</title>
  <style>
    *, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }
    body { font-family: system-ui, -apple-system, sans-serif; font-size: 14px; line-height: 1.5;
           background: #f1f5f9; color: #1e293b; height: 100vh; display: flex; flex-direction: column; overflow: hidden; }

    /* ── HEADER ── */
    header { background: #1e293b; color: #fff; display: flex; align-items: center; gap: 16px;
             padding: 0 24px; height: 56px; flex-shrink: 0; }
    .logo { font-size: 22px; font-weight: 800; color: #f59e0b; letter-spacing: -0.5px; }
    .logo span { color: #fff; }
    .header-title { font-size: 15px; font-weight: 500; color: #94a3b8; }
    .header-sub { font-size: 12px; color: #64748b; margin-left: auto; }

    /* ── LAYOUT ── */
    .app { display: flex; flex: 1; overflow: hidden; }
    aside { width: 360px; min-width: 320px; background: #fff; border-right: 1px solid #e2e8f0;
            overflow-y: auto; flex-shrink: 0; padding: 16px; }
    main { flex: 1; overflow-y: auto; padding: 16px; }

    /* ── PARAMS ── */
    .presets { display: flex; gap: 8px; margin-bottom: 16px; }
    .preset-btn { flex: 1; padding: 8px 6px; border: 2px solid #e2e8f0; border-radius: 8px;
                  background: #fff; cursor: pointer; font-size: 11px; font-weight: 600; color: #475569;
                  transition: all .15s; text-align: center; }
    .preset-btn:hover { border-color: #f59e0b; color: #f59e0b; }
    .preset-btn.active { border-color: #f59e0b; background: #fffbeb; color: #b45309; }

    .section-label { font-size: 11px; font-weight: 700; text-transform: uppercase; letter-spacing: .06em;
                     color: #94a3b8; margin: 18px 0 8px; padding-bottom: 4px; border-bottom: 1px solid #f1f5f9; }
    .field { margin-bottom: 9px; }
    .field-row { display: flex; gap: 8px; }
    .field-row .field { flex: 1; }
    label { display: block; font-size: 12px; color: #64748b; margin-bottom: 3px; }
    label .sym { font-weight: 700; color: #b45309; }
    label .unit { font-size: 11px; color: #94a3b8; margin-left: 4px; }
    label .computed-tag { font-size: 10px; background: #e0f2fe; color: #0369a1; border-radius: 4px;
                          padding: 1px 5px; margin-left: 4px; }
    input[type=number], input[type=range] { width: 100%; }
    input[type=number] { border: 1px solid #e2e8f0; border-radius: 6px; padding: 6px 10px;
                         font-size: 13px; color: #1e293b; transition: border-color .15s; }
    input[type=number]:focus { outline: none; border-color: #f59e0b; box-shadow: 0 0 0 3px rgba(245,158,11,.15); }
    .computed-val { background: #f8fafc; border: 1px dashed #cbd5e1; border-radius: 6px;
                    padding: 6px 10px; font-size: 13px; color: #475569; }
    .slider-row { display: flex; align-items: center; gap: 8px; }
    .slider-row input[type=range] { flex: 1; accent-color: #f59e0b; }
    .slider-val { font-size: 13px; font-weight: 700; color: #b45309; min-width: 38px; text-align: right; }

    /* ── KPIs ── */
    .kpi-row { display: flex; gap: 10px; margin-bottom: 14px; flex-wrap: wrap; }
    .kpi { background: #fff; border-radius: 10px; padding: 10px 14px; flex: 1; min-width: 110px;
           box-shadow: 0 1px 3px rgba(0,0,0,.08); }
    .kpi .kpi-label { font-size: 10px; text-transform: uppercase; letter-spacing: .05em; color: #94a3b8; }
    .kpi .kpi-value { font-size: 18px; font-weight: 800; color: #1e293b; }
    .kpi .kpi-unit { font-size: 11px; color: #64748b; }

    /* ── TABLE ── */
    .table-wrap { overflow-x: auto; background: #fff; border-radius: 12px;
                  box-shadow: 0 1px 3px rgba(0,0,0,.08); margin-bottom: 16px; }
    table { width: 100%; border-collapse: collapse; }
    thead th { background: #1e293b; color: #fff; padding: 10px 14px; text-align: center;
               font-size: 12px; font-weight: 600; white-space: nowrap; }
    thead th:first-child { text-align: left; width: 200px; background: #0f172a; }
    thead .th-defaut  { background: #374151; }
    thead .th-rep     { background: #166534; }
    thead .th-rev     { background: #1e3a5f; }
    thead .th-repow   { background: #4c1d95; }
    thead .th-mix     { background: #92400e; }
    tbody tr { border-bottom: 1px solid #f1f5f9; }
    tbody tr:last-child { border-bottom: none; }
    tbody tr.highlight { background: #fefce8; }
    tbody tr.delta-row { background: #f8fafc; }
    td { padding: 8px 14px; text-align: center; font-size: 13px; }
    td:first-child { text-align: left; color: #64748b; font-size: 12px; font-weight: 500; }
    .pos { color: #16a34a; font-weight: 700; }
    .neg { color: #dc2626; font-weight: 700; }
    .neutral { color: #475569; }
    .best-col { background: rgba(34,197,94,.07); }
    .badge { display: inline-block; font-size: 10px; padding: 2px 6px; border-radius: 99px;
             margin-left: 4px; font-weight: 700; }
    .badge-best { background: #dcfce7; color: #15803d; }

    /* ── BAR CHART ROW ── */
    tr.chart-row td { padding: 4px 14px 10px; vertical-align: bottom; border-bottom: none; }
    tr.chart-row td:first-child { font-size: 11px; color: #94a3b8; font-weight: 600;
                                   text-transform: uppercase; letter-spacing: .04em; }
    .bar-wrap { display: flex; flex-direction: column; align-items: center; height: 90px;
                justify-content: flex-end; }
    .bar-fill { width: 55%; min-height: 3px; border-radius: 4px 4px 0 0;
                transition: height .35s ease; }
    .bar-lbl  { font-size: 11px; font-weight: 700; margin-top: 5px; text-align: center;
                white-space: nowrap; }
    .bar-sub  { font-size: 10px; color: #94a3b8; text-align: center; }

    /* ── NOTES ── */
    .notes { background: #fff; border-radius: 12px; box-shadow: 0 1px 3px rgba(0,0,0,.08);
             padding: 16px; margin-bottom: 16px; }
    .notes h3 { font-size: 12px; font-weight: 700; text-transform: uppercase; letter-spacing: .05em;
                color: #94a3b8; margin-bottom: 10px; }
    .notes ul { list-style: none; display: flex; flex-direction: column; gap: 5px; }
    .notes li { font-size: 12px; color: #475569; padding-left: 14px; position: relative; }
    .notes li::before { content: "•"; position: absolute; left: 0; color: #f59e0b; }

    /* ── MIX BREAKDOWN ── */
    .mix-info { background: #fffbeb; border: 1px solid #fde68a; border-radius: 8px; padding: 10px 12px;
                font-size: 12px; color: #78350f; margin-top: 6px; }
    .mix-info strong { display: block; margin-bottom: 4px; }

    @media (max-width: 900px) { aside { width: 100%; } }
    @media (max-width: 700px) {
      .app { flex-direction: column; }
      aside { width: 100%; border-right: none; border-bottom: 1px solid #e2e8f0; }
    }
  </style>
</head>
<body>

<header>
  <div class="logo"><span>DOT</span>Sun</div>
  <div class="header-title">Comparateur de Stratégies de Gestion de Parc PV</div>
  <div class="header-sub">Défaut · Réparation · Revamping · Repowering</div>
</header>

<div class="app">

  <!-- ═══════════════════ PARAMS PANEL ═══════════════════ -->
  <aside>
    <div class="presets">
      <button class="preset-btn active" onclick="loadPreset('s1')">Scénario 1<br>Grande centrale</button>
      <button class="preset-btn" onclick="loadPreset('s2')">Scénario 2<br>Petite centrale</button>
      <button class="preset-btn" onclick="loadPreset('custom')" id="btn-custom">Personnalisé</button>
    </div>

    <div class="section-label">Centrale solaire</div>

    <div class="field-row">
      <div class="field">
        <label><span class="sym">n</span> — Nb panneaux</label>
        <input type="number" id="n" min="1" step="100" value="40000" oninput="recalc()">
      </div>
      <div class="field">
        <label><span class="sym">Pm</span> <span class="unit">Wc/panneau</span></label>
        <input type="number" id="Pm" min="1" step="5" value="300" oninput="recalc()">
      </div>
    </div>

    <div class="field-row">
      <div class="field">
        <label>Pcentrale <span class="computed-tag">calculé</span> <span class="unit">kWc</span></label>
        <div class="computed-val" id="disp-Pcentrale">12 000</div>
      </div>
      <div class="field">
        <label><span class="sym">H</span> <span class="unit">kWh/kWc/an</span></label>
        <input type="number" id="H" min="500" max="2500" step="10" value="1200" oninput="recalc()">
      </div>
    </div>

    <div class="field-row">
      <div class="field">
        <label><span class="sym">Y</span> — Âge centrale <span class="unit">ans</span></label>
        <input type="number" id="Y" min="0" max="30" step="1" value="10" oninput="recalc()">
      </div>
      <div class="field">
        <label>I₂ — Efficacité <span class="computed-tag">calculé</span></label>
        <div class="computed-val" id="disp-I2">96.07 %</div>
      </div>
    </div>

    <div class="section-label">Dégradation des panneaux</div>

    <div class="field-row">
      <div class="field">
        <label><span class="sym">d</span> — Dégradation normale <span class="unit">%/an</span></label>
        <input type="number" id="d" min="0" max="5" step="0.05" value="0.4" oninput="recalc()">
      </div>
      <div class="field">
        <label><span class="sym">dn</span> — Dégradation accélérée (Défaut) <span class="unit">%/an</span></label>
        <input type="number" id="dn" min="0" max="30" step="0.5" value="6" oninput="recalc()">
      </div>
    </div>
    <div class="field-row">
      <div class="field">
        <label><span class="sym">Eff-IV</span> — Efficacité réelle mesurée <span class="unit">%</span></label>
        <input type="number" id="eff_iv" min="0" max="100" step="0.1" value="0" oninput="recalc()"
               title="Efficacité mesurée par courbe IV sur site. Laisser à 0 pour utiliser la valeur calculée (1-d)^Y.">
      </div>
      <div class="field">
        <label style="color:#64748b;font-size:10px">Efficacité utilisée</label>
        <div class="computed-val" id="disp-eff-caption" style="font-size:10px;color:#94a3b8;padding-top:2px">▶ calculée auto</div>
      </div>
    </div>

    <div class="section-label">Contrat &amp; revenus</div>

    <div class="field-row">
      <div class="field">
        <label><span class="sym">N</span> — Années restantes OA <span class="unit">ans</span></label>
        <input type="number" id="N" min="1" max="20" step="1" value="10" oninput="recalc()">
      </div>
      <div class="field">
        <label><span class="sym">p</span> — Tarif EDF OA <span class="unit">€/kWh</span></label>
        <input type="number" id="p" min="0" max="1" step="0.001" value="0.0818" oninput="recalc()">
      </div>
    </div>

    <div class="field-row">
      <div class="field">
        <label><span class="sym">N1</span> — Extension Rép/Rev <span class="unit">ans post-OA</span></label>
        <input type="number" id="N1" min="0" max="20" step="1" value="5" oninput="recalc()">
      </div>
      <div class="field">
        <label><span class="sym">N2</span> — Extension Repow <span class="unit">ans post-OA</span></label>
        <input type="number" id="N2" min="0" max="30" step="1" value="10" oninput="recalc()">
      </div>
    </div>

    <div class="field">
      <label><span class="sym">PPA</span> — Tarification post-OA <span class="unit">€/kWh (PPA / agrégateur)</span></label>
      <input type="number" id="PPA" min="0" max="0.2" step="0.005" value="0.03" oninput="recalc()">
    </div>

    <div class="section-label">Coûts des interventions</div>

    <div class="field-row">
      <div class="field">
        <label><span class="sym">Crep</span> <span class="unit">€/panneau</span> — Réparation</label>
        <input type="number" id="Crep" min="0" step="1" value="25" oninput="recalc()">
      </div>
      <div class="field">
        <label><span class="sym">Cdm</span> <span class="unit">€/panneau</span> — Démontage/Remontage</label>
        <input type="number" id="Cdm" min="0" step="1" value="4" oninput="recalc()">
      </div>
    </div>

    <div class="field-row">
      <div class="field">
        <label><span class="sym">Cde</span> <span class="unit">€/panneau</span> — Démantèlement + recyclage</label>
        <input type="number" id="Cde" min="0" step="1" value="15" oninput="recalc()">
      </div>
      <div class="field">
        <label><span class="sym">Cfac</span> <span class="unit">€/Wc</span> — Panneau «à façon»</label>
        <input type="number" id="Cfac" min="0" max="2" step="0.01" value="0.25" oninput="recalc()">
      </div>
    </div>

    <div class="field">
      <label><span class="sym">Crev</span> <span class="unit">€/Wc</span> — EPC Repowering clé en main</label>
      <input type="number" id="Crev" min="0" max="2" step="0.01" value="0.5" oninput="recalc()">
    </div>

    <div class="section-label">Paramètres opérationnels</div>

    <div class="field-row">
      <div class="field">
        <label><span class="sym">Down_rep</span> — Arrêt Rép/Rev <span class="unit">mois</span></label>
        <input type="number" id="Down_rep" min="0" max="12" step="0.5" value="1" oninput="recalc()">
      </div>
      <div class="field">
        <label><span class="sym">Down_repow</span> — Arrêt Repow <span class="unit">mois</span></label>
        <input type="number" id="Down_repow" min="0" max="24" step="1" value="8" oninput="recalc()">
      </div>
    </div>

    <div class="field">
      <label><span class="sym">u</span> — Uplift repowering <span class="unit">% capacité supplémentaire</span></label>
      <input type="number" id="u" min="0" max="50" step="1" value="10" oninput="recalc()">
    </div>

    <div class="section-label">Scénario Mix Réparation + Revamping</div>

    <div class="field">
      <label>Part de panneaux réparables <span class="sym">α_rep</span></label>
      <div class="slider-row">
        <input type="range" id="alpha_rep_slider" min="0" max="100" step="1" value="85"
               oninput="document.getElementById('alpha_rep').value=this.value/100; recalc()">
        <span class="slider-val" id="disp-alpha">85 %</span>
      </div>
      <input type="number" id="alpha_rep" min="0" max="1" step="0.01" value="0.85"
             oninput="document.getElementById('alpha_rep_slider').value=Math.round(this.value*100); recalc()"
             style="margin-top:5px">
    </div>
    <div class="mix-info" id="mix-info">
      <strong>Détail du mix :</strong>
      <span id="mix-detail">—</span>
    </div>
  </aside>

  <!-- ═══════════════════ RESULTS PANEL ═══════════════════ -->
  <main>

    <!-- KPI row -->
    <div class="kpi-row">
      <div class="kpi">
        <div class="kpi-label">Puissance centrale</div>
        <div class="kpi-value" id="kpi-Pcentrale">12 000</div>
        <div class="kpi-unit">kWc nominal</div>
      </div>
      <div class="kpi">
        <div class="kpi-label">Efficacité actuelle (I₂)</div>
        <div class="kpi-value" id="kpi-I2">96.1 %</div>
        <div class="kpi-unit">après <span id="kpi-Y">10</span> ans</div>
      </div>
      <div class="kpi">
        <div class="kpi-label">Production annuelle base</div>
        <div class="kpi-value" id="kpi-prod">13 545</div>
        <div class="kpi-unit">MWh / an (état actuel)</div>
      </div>
      <div class="kpi">
        <div class="kpi-label">Revenu annuel base</div>
        <div class="kpi-value" id="kpi-rev">1 108</div>
        <div class="kpi-unit">k€ / an (état actuel)</div>
      </div>
    </div>

    <!-- Comparison table -->
    <div class="table-wrap">
      <table>
        <thead>
          <tr>
            <th></th>
            <th class="th-defaut">Défaut<br><small>Inaction</small></th>
            <th class="th-rep">Réparation<br><small>100 % panneaux</small></th>
            <th class="th-rev">Revamping<br><small>100 % panneaux</small></th>
            <th class="th-repow">Repowering<br><small>+<span id="th-uplift">10</span> % capacité</small></th>
            <th class="th-mix">Mix Rép+Rev<br><small id="th-mix-pct">85% + 15%</small></th>
          </tr>
        </thead>
        <tbody>
          <tr>
            <td>Puissance après intervention</td>
            <td id="t-pow-defaut">—</td>
            <td id="t-pow-rep">—</td>
            <td id="t-pow-rev">—</td>
            <td id="t-pow-repow">—</td>
            <td id="t-pow-mix">—</td>
          </tr>
          <tr>
            <td>Extension post-OA</td>
            <td id="t-ext-defaut">—</td>
            <td id="t-ext-rep">—</td>
            <td id="t-ext-rev">—</td>
            <td id="t-ext-repow">—</td>
            <td id="t-ext-mix">—</td>
          </tr>
          <tr>
            <td>CAPEX (€)</td>
            <td id="t-capex-defaut">—</td>
            <td id="t-capex-rep">—</td>
            <td id="t-capex-rev">—</td>
            <td id="t-capex-repow">—</td>
            <td id="t-capex-mix">—</td>
          </tr>
          <tr>
            <td>Revenus cumulés EDF OA (€)</td>
            <td id="t-revoa-defaut">—</td>
            <td id="t-revoa-rep">—</td>
            <td id="t-revoa-rev">—</td>
            <td id="t-revoa-repow">—</td>
            <td id="t-revoa-mix">—</td>
          </tr>
          <tr>
            <td>Cash Flow EDF OA (€)</td>
            <td id="t-cfoa-defaut">—</td>
            <td id="t-cfoa-rep">—</td>
            <td id="t-cfoa-rev">—</td>
            <td id="t-cfoa-repow">—</td>
            <td id="t-cfoa-mix">—</td>
          </tr>
          <tr>
            <td>Revenus cumulés post-OA (€)</td>
            <td id="t-revpost-defaut">—</td>
            <td id="t-revpost-rep">—</td>
            <td id="t-revpost-rev">—</td>
            <td id="t-revpost-repow">—</td>
            <td id="t-revpost-mix">—</td>
          </tr>
          <tr class="highlight">
            <td><strong>Cash Flow Total (€)</strong></td>
            <td id="t-cftot-defaut">—</td>
            <td id="t-cftot-rep">—</td>
            <td id="t-cftot-rev">—</td>
            <td id="t-cftot-repow">—</td>
            <td id="t-cftot-mix">—</td>
          </tr>
          <tr class="delta-row">
            <td>ΔCCF vs Défaut (€)</td>
            <td class="neutral">—</td>
            <td id="t-delta-rep">—</td>
            <td id="t-delta-rev">—</td>
            <td id="t-delta-repow">—</td>
            <td id="t-delta-mix">—</td>
          </tr>
          <tr class="delta-row">
            <td>% vs Défaut</td>
            <td class="neutral">—</td>
            <td id="t-pct-rep">—</td>
            <td id="t-pct-rev">—</td>
            <td id="t-pct-repow">—</td>
            <td id="t-pct-mix">—</td>
          </tr>
          <tr class="chart-row">
            <td>ΔCCF — graphique</td>
            <td><div style="text-align:center;color:#94a3b8;font-size:11px;padding-bottom:6px;">référence</div></td>
            <td>
              <div class="bar-wrap"><div class="bar-fill" id="bar-fill-rep"></div></div>
              <div class="bar-lbl" id="bar-lbl-rep"></div>
              <div class="bar-sub" id="bar-sub-rep"></div>
            </td>
            <td>
              <div class="bar-wrap"><div class="bar-fill" id="bar-fill-rev"></div></div>
              <div class="bar-lbl" id="bar-lbl-rev"></div>
              <div class="bar-sub" id="bar-sub-rev"></div>
            </td>
            <td>
              <div class="bar-wrap"><div class="bar-fill" id="bar-fill-repow"></div></div>
              <div class="bar-lbl" id="bar-lbl-repow"></div>
              <div class="bar-sub" id="bar-sub-repow"></div>
            </td>
            <td>
              <div class="bar-wrap"><div class="bar-fill" id="bar-fill-mix"></div></div>
              <div class="bar-lbl" id="bar-lbl-mix"></div>
              <div class="bar-sub" id="bar-sub-mix"></div>
            </td>
          </tr>
        </tbody>
      </table>
    </div>


    <!-- Notes -->
    <div class="notes">
      <h3>Hypothèses &amp; définitions</h3>
      <ul>
        <li><strong>Réparation</strong> : restitution de l'intégrité électrique du panneau — ne remet pas à zéro la dégradation naturelle des cellules.</li>
        <li><strong>Revamping</strong> : remplacement par des panneaux «à façon» (format &amp; caractéristiques similaires) — panneaux neufs, dégradation repart de zéro.</li>
        <li><strong>Repowering</strong> : remplacement complet (panneaux, structure, onduleur…) avec uplift de capacité. Arrêt plus long (chantier complet).</li>
        <li><strong>Mix Rép+Rev</strong> : panneaux réparables → réparés ; panneaux non réparables → remplacés par des panneaux à façon pour revenir à la puissance nominale.</li>
        <li>O&amp;M annuel (nettoyage, inspection…) exclu — considéré identique pour toutes les stratégies.</li>
        <li>La dégradation accélérée (dn) s'applique uniquement au scénario Défaut (rien n'est fait).</li>
        <li>Post-OA : valorisation au tarif PPA / agrégateur. Réparation &amp; Revamping : +N1 ans. Repowering : +N2 ans.</li>
      </ul>
    </div>

  </main>
</div>

<script>
// ─── PRESETS ──────────────────────────────────────────────────────────────────
const PRESETS = {
  s1: { label: "Scénario 1",
        n: 40000, Pm: 300,   H: 1200, Y: 10, d: 0.4,  dn: 6, eff_iv: 0,
        N: 10,  p: 0.0818, PPA: 0.03, N1: 5, N2: 10,
        Crep: 25, Cdm: 4,  Cde: 15,  Cfac: 0.25, Crev: 0.5,
        Down_rep: 1, Down_repow: 8, u: 10, alpha_rep: 0.85 },
  s2: { label: "Scénario 2",
        n: 4304, Pm: 195,   H: 1180, Y: 14, d: 0.45, dn: 6, eff_iv: 0,
        N: 6,   p: 0.75,   PPA: 0.03, N1: 0, N2: 15,
        Crep: 30, Cdm: 5,  Cde: 18,  Cfac: 0.30, Crev: 0.70,
        Down_rep: 1, Down_repow: 8, u: 10, alpha_rep: 0.80 }
};

let activePreset = 's1';

function loadPreset(key) {
  activePreset = key;
  document.querySelectorAll('.preset-btn').forEach(b => b.classList.remove('active'));
  if (key === 'custom') {
    document.getElementById('btn-custom').classList.add('active');
    return;
  }
  const p = PRESETS[key];
  if (!p) return;
  const fields = ['n','Pm','H','Y','d','dn','eff_iv','N','p','PPA','N1','N2',
                  'Crep','Cdm','Cde','Cfac','Crev','Down_rep','Down_repow','u','alpha_rep'];
  fields.forEach(f => { const el = document.getElementById(f); if (el) el.value = p[f]; });
  document.getElementById('alpha_rep_slider').value = Math.round(p.alpha_rep * 100);
  document.querySelectorAll('.preset-btn')[key === 's1' ? 0 : 1].classList.add('active');
  recalc();
}

// ─── HELPERS ─────────────────────────────────────────────────────────────────
const $ = id => document.getElementById(id);
const v  = id => parseFloat($(id).value) || 0;

function fmtEuro(n) {
  return new Intl.NumberFormat('fr-FR', { style: 'currency', currency: 'EUR',
    maximumFractionDigits: 0 }).format(Math.round(n));
}
function fmtEuroShort(n) {
  const abs = Math.abs(n);
  const sign = n < 0 ? '-' : '';
  if (abs >= 1e6) return sign + (abs / 1e6).toFixed(2).replace('.', ',') + ' M€';
  if (abs >= 1e3) return sign + (abs / 1e3).toFixed(1).replace('.', ',') + ' k€';
  return sign + abs.toFixed(0) + ' €';
}
function fmtPct(n) {
  return (n >= 0 ? '+' : '') + (n * 100).toFixed(1) + ' %';
}
function fmtKwc(n) {
  return new Intl.NumberFormat('fr-FR', { maximumFractionDigits: 0 }).format(Math.round(n)) + ' kWc';
}

// ─── CORE CALCULATION ────────────────────────────────────────────────────────
function compute() {
  const n         = v('n');
  const Pm        = v('Pm');
  const H         = v('H');
  const Y         = v('Y');
  const d         = v('d')  / 100;   // input in %, convert to decimal
  const dn        = v('dn') / 100;   // input in %, convert to decimal
  const N         = Math.round(v('N'));
  const tarif     = v('p');
  const PPA       = v('PPA');
  const N1        = Math.round(v('N1'));
  const N2        = Math.round(v('N2'));
  const Crep      = v('Crep');
  const Cdm       = v('Cdm');
  const Cde       = v('Cde');
  const Cfac      = v('Cfac');
  const Crev      = v('Crev');
  const Down_rep  = v('Down_rep');
  const Down_repow= v('Down_repow');
  const u         = v('u')  / 100;   // input in %, convert to decimal
  const alpha_rep = v('alpha_rep');

  const eff_iv    = v('eff_iv');
  const Pcentrale = n * Pm / 1000;                    // kWc
  const I2        = eff_iv > 0 ? (eff_iv / 100) : Math.pow(1 - d, Y);
  const alpha_rev = 1 - alpha_rep;

  // Mix: restore nominal power with à-façon panels
  const P_res_rep = alpha_rep * n * Pm * I2 / 1000;   // kWc — repaired panels residual power
  const gap_kWc   = Math.max(0, Pcentrale - P_res_rep);
  const n_rev     = alpha_rev * n;
  const Pm_fac    = n_rev > 0 ? gap_kWc * 1000 / n_rev : 0;  // Wc per à-façon panel

  // ── CAPEX ──
  const capex = {
    defaut : 0,
    rep    : n * (Crep + Cdm),
    rev    : n * (Pm * Cfac + Cdm),
    repow  : n * Cde + Pcentrale * 1000 * (1 + u) * Crev,
    mix    : alpha_rep * n * (Crep + Cdm) + gap_kWc * 1000 * Cfac + n_rev * Cdm
  };

  // ── Annual power (kWc) at year k (1-indexed, continuous from intervention) ──
  function power(strat, k) {
    if (strat === 'defaut') return Pcentrale * I2 * Math.pow(1 - dn, k - 1);
    if (strat === 'rep')    return Pcentrale * I2 * Math.pow(1 - d,  k - 1);
    if (strat === 'rev')    return Pcentrale      * Math.pow(1 - d,  k - 1);
    if (strat === 'repow')  return Pcentrale * (1 + u) * Math.pow(1 - d, k - 1);
    if (strat === 'mix')    return Pcentrale      * Math.pow(1 - d,  k - 1);
  }

  // Downtime penalty:
  //   Repair / Revamping / Mix → applied to year 1 (works start immediately)
  //   Repowering              → applied to year N (last OA year, construction at transition)
  function downFactor(strat, k) {
    if (strat === 'defaut') return 1;
    if (strat === 'repow')  return k === N ? (1 - Down_repow / 12) : 1;
    return k === 1 ? (1 - Down_rep / 12) : 1;
  }

  function revYear(strat, k, t) { return H * t * power(strat, k) * downFactor(strat, k); }

  const ext = { defaut: N1, rep: N1, rev: N1, repow: N2, mix: N1 };
  const strats = ['defaut', 'rep', 'rev', 'repow', 'mix'];

  const revOA = {}, revPost = {}, cfOA = {}, cfTotal = {}, delta = {}, pct = {};

  strats.forEach(s => {
    let rOA = 0;
    for (let k = 1; k <= N;          k++) rOA   += revYear(s, k, tarif);
    let rPost = 0;
    for (let k = N + 1; k <= N + ext[s]; k++) rPost += revYear(s, k, PPA);
    revOA[s]   = rOA;
    revPost[s] = rPost;
    cfOA[s]    = rOA  - capex[s];
    cfTotal[s] = cfOA[s] + rPost;
  });

  strats.forEach(s => {
    delta[s] = cfTotal[s] - cfTotal.defaut;
    pct[s]   = cfTotal.defaut !== 0 ? delta[s] / cfTotal.defaut : 0;
  });

  return { Pcentrale, I2, alpha_rev, P_res_rep, gap_kWc, n_rev, Pm_fac,
           capex, revOA, revPost, cfOA, cfTotal, delta, pct,
           strats, ext, N, N1, N2, u };
}

// ─── BAR CHART (CSS, aligned with table columns) ─────────────────────────────
// Colors match the table header backgrounds exactly
const BAR_COLORS = {
  rep   : { pos: '#166534', neg: '#dcfce7' },
  rev   : { pos: '#1e3a5f', neg: '#dbeafe' },
  repow : { pos: '#4c1d95', neg: '#ede9fe' },
  mix   : { pos: '#92400e', neg: '#fef3c7' }
};
const MAX_BAR_H = 80; // px

function updateCharts(r) {
  const nonDefaut = ['rep', 'rev', 'repow', 'mix'];
  const vals = nonDefaut.map(s => r.delta[s]);
  const maxAbs = Math.max(...vals.map(Math.abs), 1);

  nonDefaut.forEach(s => {
    const val  = r.delta[s];
    const pct  = r.pct[s];
    const h    = Math.max(Math.abs(val) / maxAbs * MAX_BAR_H, 3);
    const col  = val >= 0 ? BAR_COLORS[s].pos : BAR_COLORS[s].neg;
    const fill = $('bar-fill-' + s);
    const lbl  = $('bar-lbl-'  + s);
    const sub  = $('bar-sub-'  + s);
    if (fill) { fill.style.height = h + 'px'; fill.style.backgroundColor = col; }
    if (lbl)  { lbl.textContent = fmtEuroShort(val);
                lbl.style.color = val >= 0 ? BAR_COLORS[s].pos : '#dc2626'; }
    if (sub)  { sub.textContent = fmtPct(pct);
                sub.style.color = val >= 0 ? '#16a34a' : '#dc2626'; }
  });
}

// ─── UI UPDATE ───────────────────────────────────────────────────────────────
function cell(id, html)    { const el = $(id); if (el) el.innerHTML = html; }
function cellEuro(id, n)   { cell(id, fmtEuro(n)); }
function cellDelta(id, n)  {
  const cls = n > 0 ? 'pos' : n < 0 ? 'neg' : 'neutral';
  cell(id, `<span class="${cls}">${fmtEuro(n)}</span>`);
}
function cellPct(id, n) {
  const cls = n > 0 ? 'pos' : n < 0 ? 'neg' : 'neutral';
  cell(id, `<span class="${cls}">${fmtPct(n)}</span>`);
}

function updateUI(r) {
  const { Pcentrale, I2, capex, revOA, revPost, cfOA, cfTotal, delta, pct, ext, u } = r;

  // KPIs
  $('kpi-Pcentrale').textContent = new Intl.NumberFormat('fr-FR').format(Math.round(Pcentrale));
  $('kpi-I2').textContent        = (I2 * 100).toFixed(1) + ' %';
  $('kpi-Y').textContent         = v('Y');

  // Eff-IV caption
  const eff_iv_disp = v('eff_iv');
  const i2_calc     = Math.pow(1 - v('d') / 100, v('Y')) * 100;
  if (eff_iv_disp > 0) {
    $('disp-eff-caption').textContent = '▶ Mesure IV : ' + eff_iv_disp.toFixed(1) + '%';
    $('disp-eff-caption').style.color = '#f59e0b';
  } else {
    $('disp-eff-caption').textContent = '▶ Calculée : ' + i2_calc.toFixed(1) + '% (d=' + v('d').toFixed(2) + '%, Y=' + Math.round(v('Y')) + ' ans)';
    $('disp-eff-caption').style.color = '#94a3b8';
  }
  const prodBase = Pcentrale * I2 * v('H');
  $('kpi-prod').textContent = (prodBase / 1000).toFixed(0);
  $('kpi-rev').textContent  = (prodBase * v('p') / 1000).toFixed(0);

  // Computed displays
  $('disp-Pcentrale').textContent = new Intl.NumberFormat('fr-FR').format(Math.round(Pcentrale)) + ' kWc';
  $('disp-I2').textContent        = (I2 * 100).toFixed(2) + ' %';
  $('disp-alpha').textContent     = Math.round(v('alpha_rep') * 100) + ' %';
  $('th-uplift').textContent      = Math.round(u * 100);
  const repPct = Math.round(v('alpha_rep') * 100);
  $('th-mix-pct').textContent     = repPct + '% + ' + (100 - repPct) + '%';

  // Mix info
  $('mix-detail').innerHTML =
    `${Math.round(r.strats && r.P_res_rep !== undefined ? v('alpha_rep') * 100 : 85)} % réparés ` +
    `(${new Intl.NumberFormat('fr-FR').format(Math.round(r.n_rev > 0 ? (1-v('alpha_rep'))*v('n') : 0))} panneaux remplacés` +
    ` · ${r.Pm_fac.toFixed(0)} Wc/panneau à façon · ` +
    `puissance gap : ${r.gap_kWc.toFixed(0)} kWc)`;

  // Power after intervention
  cell('t-pow-defaut', fmtKwc(Pcentrale * I2));
  cell('t-pow-rep',    fmtKwc(Pcentrale * I2));
  cell('t-pow-rev',    fmtKwc(Pcentrale));
  cell('t-pow-repow',  fmtKwc(Pcentrale * (1 + u)));
  cell('t-pow-mix',    fmtKwc(Pcentrale));

  // Extension
  ['defaut','rep','rev'].forEach(s => cell(`t-ext-${s}`, ext[s] === 0 ? '—' : `+${ext[s]} ans PPA`));
  cell('t-ext-repow', `+${ext.repow} ans PPA`);
  cell('t-ext-mix',   ext.mix === 0 ? '—' : `+${ext.mix} ans PPA`);

  // Table values
  r.strats.forEach(s => {
    cellEuro(`t-capex-${s}`,   capex[s]);
    cellEuro(`t-revoa-${s}`,   revOA[s]);
    cellEuro(`t-cfoa-${s}`,    cfOA[s]);
    cellEuro(`t-revpost-${s}`, revPost[s]);
    cellEuro(`t-cftot-${s}`,   cfTotal[s]);
  });

  // Delta and pct (skip défaut)
  ['rep','rev','repow','mix'].forEach(s => {
    cellDelta(`t-delta-${s}`, delta[s]);
    cellPct(`t-pct-${s}`, pct[s]);
  });

  // Highlight best non-défaut strategy
  const nonDefaut = ['rep','rev','repow','mix'];
  const best = nonDefaut.reduce((a, b) => cfTotal[a] > cfTotal[b] ? a : b);
  nonDefaut.forEach(s => {
    const cells = document.querySelectorAll(`[id$="-${s}"]`);
    cells.forEach(c => c.classList.remove('best-col'));
  });
  document.querySelectorAll(`[id$="-${best}"]`).forEach(c => c.classList.add('best-col'));

  // Badge on best
  document.querySelectorAll('.badge-best').forEach(b => b.remove());
  const bestCell = $(`t-cftot-${best}`);
  if (bestCell) {
    const badge = document.createElement('span');
    badge.className = 'badge badge-best';
    badge.textContent = '★ Meilleur';
    bestCell.appendChild(badge);
  }
}

// ─── MAIN RECALC ─────────────────────────────────────────────────────────────
function recalc() {
  // Mark as custom if user changed something
  if (activePreset !== 'custom') {
    // (keep preset highlight — user may be fine-tuning)
  }
  try {
    const r = compute();
    updateUI(r);
    updateCharts(r);
  } catch (e) {
    console.error(e);
  }
}

// ─── INIT ────────────────────────────────────────────────────────────────────
document.addEventListener('DOMContentLoaded', () => {
  recalc();
});
</script>
</body>
</html>
"""

with open(OUTPUT, "w", encoding="utf-8") as f:
    f.write(HTML)

print(f"Fichier généré : {OUTPUT}")
print(f"Ouvrez le fichier dans un navigateur : {OUTPUT}")
