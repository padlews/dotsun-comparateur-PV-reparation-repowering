# -*- coding: utf-8 -*-
"""
DOTSun — Générateur de Tableaux Financiers par Scénario
Génère tableaux_financier_scenarios.html
"""
import sys, os
sys.stdout.reconfigure(encoding="utf-8")

HTML = r"""<!DOCTYPE html>
<html lang="fr">
<head>
<meta charset="UTF-8"/>
<meta name="viewport" content="width=device-width,initial-scale=1"/>
<title>DOTSun — Tableaux Financiers PV</title>
<style>
*{box-sizing:border-box;margin:0;padding:0}
body{font-family:system-ui,sans-serif;background:#f1f5f9;color:#1e293b;font-size:13px}
/* ── Layout ── */
.layout{display:flex;min-height:100vh}
.sidebar{width:290px;min-width:290px;background:#1e293b;padding:16px;overflow-y:auto;position:sticky;top:0;max-height:100vh}
.main{flex:1;padding:20px;overflow-x:auto}
/* ── Sidebar ── */
.logo{font-size:22px;font-weight:900;letter-spacing:-.5px;margin-bottom:16px}
.logo .dot{color:#fff}.logo .sun{color:#f59e0b}
.sidebar h3{color:#94a3b8;font-size:10px;text-transform:uppercase;letter-spacing:.08em;margin:14px 0 6px}
.sidebar label{display:block;color:#cbd5e1;font-size:11px;margin-bottom:2px;margin-top:8px}
.sidebar input[type=number],.sidebar select{width:100%;background:#0f172a;border:1px solid #334155;
  color:#f1f5f9;border-radius:5px;padding:5px 8px;font-size:12px}
.sidebar input[type=range]{width:100%;accent-color:#f59e0b}
.info-box{background:#0f172a;border-radius:6px;padding:7px 10px;color:#94a3b8;font-size:11px;margin-top:6px;line-height:1.6}
.info-box b{color:#e2e8f0}
.btn-preset{background:#334155;color:#e2e8f0;border:none;border-radius:5px;padding:6px 10px;
  font-size:11px;cursor:pointer;width:48%;margin-right:2%}
.btn-preset:last-child{margin-right:0}
/* ── Page header ── */
.page-header{background:#1e293b;border-radius:10px;padding:14px 20px;margin-bottom:18px;
  display:flex;align-items:center;gap:16px}
.page-header .logo2{font-size:20px;font-weight:900;letter-spacing:-.5px}
.page-header .logo2 .dot{color:#fff}.page-header .logo2 .sun{color:#f59e0b}
.page-header .subtitle{color:#94a3b8;font-size:14px}
/* ── Tabs ── */
.tabs{display:flex;gap:6px;margin-bottom:18px;flex-wrap:wrap}
.tab-btn{padding:8px 18px;border-radius:6px 6px 0 0;border:none;cursor:pointer;font-size:12px;
  font-weight:600;background:#e2e8f0;color:#64748b;transition:.2s}
.tab-btn.active{color:#fff}
.tab-btn[data-s=defaut].active{background:#374151}
.tab-btn[data-s=repow].active{background:#b91c1c}
.tab-btn[data-s=rep].active{background:#166534}
.tab-btn[data-s=rev].active{background:#1e3a5f}
.tab-btn[data-s=mix].active{background:linear-gradient(90deg,#166534 50%,#1e3a5f 50%)}
.tab-btn[data-s=synthese].active{background:#0f172a}
.tab-pane{display:none}.tab-pane.active{display:block}
/* ── Section titles ── */
.section-title{font-size:14px;font-weight:700;color:#1e293b;margin:18px 0 8px;
  padding-bottom:4px;border-bottom:2px solid #e2e8f0}
/* ── Tables ── */
.tbl-wrap{overflow-x:auto;border-radius:8px;box-shadow:0 1px 4px rgba(0,0,0,.1);margin-bottom:20px}
table{border-collapse:collapse;width:100%;background:#fff;white-space:nowrap}
thead th{padding:7px 10px;font-size:11px;font-weight:700;text-align:center;color:#fff}
th.row-label{text-align:left;background:#0f172a;min-width:190px;position:sticky;left:0;z-index:2}
th.yr{min-width:80px}
td{padding:5px 10px;font-size:11px;text-align:right;border-bottom:1px solid #f1f5f9}
td.row-label{text-align:left;font-weight:500;color:#475569;background:#f8fafc;
  position:sticky;left:0;z-index:1;border-right:1px solid #e2e8f0}
td.section-head{background:#1e293b;color:#fff;font-weight:700;font-size:11px;text-align:left}
tr.sub td{background:#fafafa;color:#64748b}
tr.total td{background:#fefce8;font-weight:700}
tr.highlight td{background:#f0fdf4;font-weight:700;color:#166534}
tr.highlight.neg td{background:#fff1f2;color:#b91c1c}
tr.dscr td{color:#0f172a;font-weight:600}
td.pos{color:#166534;font-weight:600}td.neg{color:#b91c1c;font-weight:600}
td.neutral{color:#64748b}
/* ── KPI cards ── */
.kpis{display:flex;gap:12px;flex-wrap:wrap;margin-bottom:16px}
.kpi{background:#fff;border-radius:8px;padding:12px 16px;min-width:140px;
  box-shadow:0 1px 3px rgba(0,0,0,.08)}
.kpi .label{font-size:10px;color:#64748b;margin-bottom:4px}
.kpi .val{font-size:18px;font-weight:700;color:#0f172a}
.kpi .sub{font-size:10px;color:#94a3b8;margin-top:2px}
/* ── Synthèse ── */
#synthese-wrap table thead th{background:#0f172a}
#synthese-wrap table td.row-label{min-width:220px}
</style>
</head>
<body>
<div class="layout">

<!-- ══ SIDEBAR ══ -->
<aside class="sidebar">
  <div class="logo"><span class="dot">DOT</span><span class="sun">Sun</span></div>

  <div style="display:flex;gap:4%">
    <button class="btn-preset" onclick="loadPreset('s1')">📋 Scénario 1</button>
    <button class="btn-preset" onclick="loadPreset('s2')">📋 Scénario 2</button>
  </div>

  <h3>Centrale solaire</h3>
  <label>n — Nombre de panneaux</label>
  <input type="number" id="n" value="40000" step="100" oninput="update()">
  <label>Pm — Puissance/panneau (Wc)</label>
  <input type="number" id="Pm" value="300" step="5" oninput="update()">
  <label>H — Productible (kWh/kWc/an)</label>
  <input type="number" id="H" value="1200" step="10" oninput="update()">
  <label>Y — Âge de la centrale (ans)</label>
  <input type="number" id="Y" value="10" step="1" oninput="update()">

  <h3>Dégradation</h3>
  <label>d — Dégradation normale (%/an)</label>
  <input type="number" id="d" value="0.40" step="0.05" oninput="update()">
  <label>dn — Dégradation accélérée Défaut (%/an)</label>
  <input type="number" id="dn" value="6.0" step="0.5" oninput="update()">

  <h3>Contrat &amp; Revenus</h3>
  <label>N — Années restantes OA</label>
  <input type="number" id="N" value="10" step="1" oninput="update()">
  <label>p — Tarif EDF OA (€/kWh)</label>
  <input type="number" id="tarif" value="0.0818" step="0.001" oninput="update()">
  <label>N1 — Extension Rép/Rev (ans)</label>
  <input type="number" id="N1" value="5" step="1" oninput="update()">
  <label>N2 — Extension Repowering (ans)</label>
  <input type="number" id="N2" value="10" step="1" oninput="update()">
  <label>PPA — Tarif post-OA (€/kWh)</label>
  <input type="number" id="PPA" value="0.030" step="0.005" oninput="update()">

  <h3>Coûts d'intervention</h3>
  <label>Crep — Réparation (€/panneau)</label>
  <input type="number" id="Crep" value="25" step="1" oninput="update()">
  <label>Cdm — Démontage/Remontage (€/p.)</label>
  <input type="number" id="Cdm" value="4" step="1" oninput="update()">
  <label>Cde — Démantèlement+recyclage (€/p.)</label>
  <input type="number" id="Cde" value="15" step="1" oninput="update()">
  <label>Cfac — Panneau à façon (€/Wc)</label>
  <input type="number" id="Cfac" value="0.25" step="0.01" oninput="update()">
  <label>Crev — EPC Repowering (€/Wc)</label>
  <input type="number" id="Crev" value="0.50" step="0.01" oninput="update()">

  <h3>Opérationnel</h3>
  <label>Down_rep — Arrêt Rép/Rev (mois)</label>
  <input type="number" id="Down_rep" value="1" step="0.5" oninput="update()">
  <label>Down_repow — Arrêt Repowering (mois)</label>
  <input type="number" id="Down_repow" value="8" step="1" oninput="update()">
  <label>u — Uplift repowering (%)</label>
  <input type="number" id="u" value="10" step="1" oninput="update()">

  <h3>Mix Réparation + Revamping</h3>
  <label>α_rep — Part réparable (%): <b id="alpha-lbl" style="color:#f59e0b">85</b>%</label>
  <input type="range" id="alpha_pct" min="0" max="100" value="85"
    oninput="document.getElementById('alpha-lbl').textContent=this.value;update()">
  <div class="info-box" id="pmfac-box"></div>

  <h3>Hypothèses financières</h3>
  <label>Fonds propres (% CAPEX)</label>
  <input type="number" id="equity_pct" value="20" step="1" oninput="update()">
  <label>Durée emprunt (ans)</label>
  <input type="number" id="loan_dur" value="10" step="1" oninput="update()">
  <label>Taux d'intérêt (%)</label>
  <input type="number" id="int_rate" value="4" step="0.25" oninput="update()">
  <label>Taux d'inflation (%)</label>
  <input type="number" id="infl_rate" value="2" step="0.25" oninput="update()">
  <label>Taux d'imposition (%)</label>
  <input type="number" id="tax_rate" value="25" step="1" oninput="update()">
  <label>Maintenance (% CA)</label>
  <input type="number" id="maint_pct" value="5" step="0.5" oninput="update()">
  <label>OPEX (% CA)</label>
  <input type="number" id="opex_pct" value="2" step="0.5" oninput="update()">
  <label>Assurance (% CA)</label>
  <input type="number" id="ins_pct" value="1.5" step="0.25" oninput="update()">
  <label>Loyer annuel (€)</label>
  <input type="number" id="rent" value="10000" step="1000" oninput="update()">
  <label>Amortissement (ans)</label>
  <input type="number" id="amort_dur" value="10" step="1" oninput="update()">
  <label>Intérêt trésorerie (%)</label>
  <input type="number" id="treas_rate" value="1" step="0.25" oninput="update()">
</aside>

<!-- ══ MAIN ══ -->
<main class="main">
  <div class="page-header">
    <div class="logo2"><span class="dot">DOT</span><span class="sun">Sun</span></div>
    <div class="subtitle">Tableaux Financiers — Scénarios de Rénovation de Parc PV</div>
  </div>

  <!-- Tabs -->
  <div class="tabs">
    <button class="tab-btn active" data-s="synthese" onclick="showTab('synthese')">📊 Synthèse</button>
    <button class="tab-btn" data-s="defaut"  onclick="showTab('defaut')">Défaut</button>
    <button class="tab-btn" data-s="repow"   onclick="showTab('repow')">Repowering</button>
    <button class="tab-btn" data-s="rep"     onclick="showTab('rep')">Réparation</button>
    <button class="tab-btn" data-s="rev"     onclick="showTab('rev')">Revamping</button>
    <button class="tab-btn" data-s="mix"     onclick="showTab('mix')">Mix Rép+Rev</button>
  </div>

  <!-- Synthèse -->
  <div id="pane-synthese" class="tab-pane active">
    <div class="section-title">Tableau de Synthèse — Tous Scénarios</div>
    <div class="tbl-wrap" id="synthese-wrap"></div>
  </div>

  <!-- Per-scenario panes -->
  <div id="pane-defaut" class="tab-pane"></div>
  <div id="pane-repow"  class="tab-pane"></div>
  <div id="pane-rep"    class="tab-pane"></div>
  <div id="pane-rev"    class="tab-pane"></div>
  <div id="pane-mix"    class="tab-pane"></div>
</main>
</div>

<script>
// ── Helpers ──────────────────────────────────────────────────────────────────
const v = id => parseFloat(document.getElementById(id).value) || 0;
const fmtE = (x, dec=0) => {
  if(x===null||x===undefined||isNaN(x)) return '—';
  const s = x<0?'-':''; const a=Math.abs(x);
  if(a>=1e6) return s+(a/1e6).toFixed(2)+' M€';
  if(a>=1e3) return s+(a/1e3).toFixed(1)+' k€';
  return s+a.toFixed(dec)+' €';
};
const fmtPct = x => x===null||isNaN(x)?'—':(x*100).toFixed(1)+'%';
const fmtN   = (x,d=0) => x===null||isNaN(x)?'—':x.toFixed(d);
const fmtMWh = x => (x/1000).toFixed(0)+' MWh';
const cls = x => x>0?'pos':x<0?'neg':'neutral';

// ── Tab switching ─────────────────────────────────────────────────────────────
function showTab(s){
  document.querySelectorAll('.tab-pane').forEach(p=>p.classList.remove('active'));
  document.querySelectorAll('.tab-btn').forEach(b=>b.classList.remove('active'));
  document.getElementById('pane-'+s).classList.add('active');
  document.querySelector(`.tab-btn[data-s="${s}"]`).classList.add('active');
}

// ── Presets ───────────────────────────────────────────────────────────────────
const PRESETS = {
  s1:{n:40000,Pm:300,H:1200,Y:10,d:0.40,dn:6.0,N:10,tarif:0.0818,PPA:0.03,N1:5,N2:10,
      Crep:25,Cdm:4,Cde:15,Cfac:0.25,Crev:0.5,Down_rep:1,Down_repow:8,u:10,alpha_pct:85},
  s2:{n:4304,Pm:195,H:1180,Y:14,d:0.45,dn:8.0,N:6,tarif:0.75,PPA:0.03,N1:5,N2:15,
      Crep:30,Cdm:5,Cde:18,Cfac:0.30,Crev:0.70,Down_rep:1,Down_repow:8,u:10,alpha_pct:80},
};
function loadPreset(k){
  const p=PRESETS[k];
  for(const [id,val] of Object.entries(p)){
    const el=document.getElementById(id);
    if(el){el.value=val;if(id==='alpha_pct')document.getElementById('alpha-lbl').textContent=val;}
  }
  update();
}

// ── Core calculations ─────────────────────────────────────────────────────────
function getParams(){
  const n=v('n'), Pm=v('Pm'), H=v('H'), Y=v('Y');
  const d=v('d')/100, dn=v('dn')/100, N=Math.round(v('N'));
  const tarif=v('tarif'), PPA=v('PPA'), N1=Math.round(v('N1')), N2=Math.round(v('N2'));
  const Crep=v('Crep'),Cdm=v('Cdm'),Cde=v('Cde'),Cfac=v('Cfac'),Crev=v('Crev');
  const Down_rep=v('Down_rep'), Down_repow=v('Down_repow'), u=v('u')/100;
  const alpha_pct=v('alpha_pct'), alpha_rep=alpha_pct/100, alpha_rev=1-alpha_rep;
  const Pcentrale=n*Pm/1000, I2=Math.pow(1-d,Y);
  const P_res_rep=alpha_rep*n*Pm*I2/1000;
  const gap_kWc=Math.max(0,Pcentrale-P_res_rep);
  const n_rev=alpha_rev*n;
  const Pm_fac=n_rev>0?gap_kWc*1000/n_rev:0;
  const capex={
    defaut:0,
    rep:n*(Crep+Cdm),
    rev:n*(Pm*Cfac+Cdm),
    repow:n*Cde+Pcentrale*1000*(1+u)*Crev,
    mix:alpha_rep*n*(Crep+Cdm)+gap_kWc*1000*Cfac,
  };
  return {n,Pm,H,Y,d,dn,N,tarif,PPA,N1,N2,Crep,Cdm,Cde,Cfac,Crev,
          Down_rep,Down_repow,u,alpha_rep,alpha_rev,Pcentrale,I2,
          gap_kWc,n_rev,Pm_fac,capex};
}

function getFinParams(){
  return {
    equity_pct : v('equity_pct')/100,
    loan_dur   : Math.round(v('loan_dur')),
    int_rate   : v('int_rate')/100,
    infl_rate  : v('infl_rate')/100,
    tax_rate   : v('tax_rate')/100,
    maint_pct  : v('maint_pct')/100,
    opex_pct   : v('opex_pct')/100,
    ins_pct    : v('ins_pct')/100,
    rent       : v('rent'),
    amort_dur  : Math.round(v('amort_dur')),
    treas_rate : v('treas_rate')/100,
  };
}

function power(s, k, p){
  const {Pcentrale,I2,d,dn,u} = p;
  if(s==='defaut') return Pcentrale*I2*Math.pow(1-dn,k-1);
  if(s==='rep')    return Pcentrale*I2*Math.pow(1-d,k-1);
  if(s==='rev')    return Pcentrale*Math.pow(1-d,k-1);
  if(s==='repow')  return Pcentrale*(1+u)*Math.pow(1-d,k-1);
  if(s==='mix')    return Pcentrale*Math.pow(1-d,k-1);
}
function downFactor(s, k, p){
  const {N,Down_rep,Down_repow} = p;
  if(s==='defaut') return 1;
  if(s==='repow')  return k===N?(1-Down_repow/12):1;
  return k===1?(1-Down_rep/12):1;
}

function calcLoan(debt, int_rate, loan_dur, total_yrs){
  if(debt<=0) return Array.from({length:total_yrs},(_,i)=>({k:i+1,principal:0,interest:0,annuity:0,balance:0}));
  const r=int_rate;
  const annuity = r>0 ? debt*r/(1-Math.pow(1+r,-loan_dur)) : debt/loan_dur;
  const rows=[];
  let bal=debt;
  for(let k=1;k<=total_yrs;k++){
    if(k<=loan_dur){
      const interest=bal*r;
      const principal=Math.min(annuity-interest,bal);
      bal=Math.max(0,bal-principal);
      rows.push({k,principal,interest,annuity:principal+interest,balance:bal});
    } else {
      rows.push({k,principal:0,interest:0,annuity:0,balance:0});
    }
  }
  return rows;
}

// Calcule les flux Défaut (sans dette) sur total_yrs années pour référence incrémentale
function calcDefautRows(p, fin, total_yrs){
  const rows=[];
  let cum_treas=0;
  for(let k=1;k<=total_yrs;k++){
    const tarif_k = k<=p.N ? p.tarif : p.PPA;
    const prod_kWh = p.H * power('defaut',k,p);
    const CA = tarif_k * prod_kWh;
    const maintenance = CA * fin.maint_pct;
    const opex        = CA * fin.opex_pct;
    const insurance   = CA * fin.ins_pct;
    const rent        = fin.rent * Math.pow(1+fin.infl_rate, k-1);
    const EBITDA = CA - maintenance - opex - insurance - rent;
    const EBT  = EBITDA; // CAPEX=0 → pas d'amortissement ni résultat financier
    const tax  = Math.max(0, EBT * fin.tax_rate);
    const ann_treas = EBT - tax;
    cum_treas += ann_treas;
    rows.push({k, EBITDA, ann_treas, cum_treas});
  }
  return rows;
}

function calcScenario(s, p, fin, def_ref){
  // def_ref : tableau Défaut sur la même durée (null pour le scénario Défaut lui-même)
  const total_yrs = s==='repow'?p.N+p.N2:p.N+p.N1;
  const CAPEX=p.capex[s];
  const equity=CAPEX*fin.equity_pct;
  const debt=CAPEX*(1-fin.equity_pct);
  const loan=calcLoan(debt, fin.int_rate, fin.loan_dur, total_yrs);

  const rows=[];
  let cum_treas=0, total_net=0, cum_incr_treas=0;

  for(let k=1;k<=total_yrs;k++){
    const tarif_k = k<=p.N ? p.tarif : p.PPA;
    const prod_kWh = p.H * power(s,k,p) * downFactor(s,k,p);
    const CA = tarif_k * prod_kWh;

    const maintenance = CA * fin.maint_pct;
    const opex        = CA * fin.opex_pct;
    const insurance   = CA * fin.ins_pct;
    const rent        = fin.rent * Math.pow(1+fin.infl_rate, k-1);
    const amort       = k<=fin.amort_dur && CAPEX>0 ? CAPEX/fin.amort_dur : 0;

    const EBITDA = CA - maintenance - opex - insurance - rent;
    const EBIT   = EBITDA - amort;

    const int_exp  = loan[k-1].interest;
    const int_inc  = Math.max(0, cum_treas) * fin.treas_rate;
    const fin_res  = int_inc - int_exp;

    const EBT  = EBIT + fin_res;
    const tax  = Math.max(0, EBT * fin.tax_rate);
    const net  = EBT - tax;

    const op_cf      = net + amort;
    const debt_repay = loan[k-1].principal;
    const ann_treas  = op_cf - debt_repay;
    cum_treas       += ann_treas;
    total_net       += net;

    // ── Métriques incrémentales vs Défaut ──────────────────────────────────
    const def_ebitda    = def_ref ? def_ref[k-1].EBITDA    : EBITDA;
    const def_ann_treas = def_ref ? def_ref[k-1].ann_treas : ann_treas;
    const incr_ebitda   = EBITDA - def_ebitda;
    const incr_treas    = ann_treas - def_ann_treas;
    cum_incr_treas     += incr_treas;

    // DSCR = EBITDA incrémental / service de la dette
    const dscr = loan[k-1].annuity>0 ? incr_ebitda/loan[k-1].annuity : null;

    rows.push({k, tarif_k, prod_kWh, CA,
               maintenance, opex, insurance, rent, amort,
               EBITDA, EBIT, int_exp, int_inc, fin_res,
               EBT, tax, net,
               op_cf, debt_repay, ann_treas, cum_treas,
               incr_ebitda, incr_treas, cum_incr_treas, dscr,
               loan:loan[k-1]});
  }
  // ROE = trésorerie incrémentale cumulée / fonds propres investis
  const ROE = equity>0 ? cum_incr_treas/equity : null;
  return {CAPEX, equity, debt, total_yrs, rows, ROE, total_net, cum_incr_treas};
}

// ── Render scenario pane ──────────────────────────────────────────────────────
const STRAT_COLORS={defaut:'#374151',repow:'#b91c1c',rep:'#166534',rev:'#1e3a5f',mix:'#166534'};
const STRAT_LABELS={defaut:'Défaut',repow:'Repowering',rep:'Réparation',rev:'Revamping',mix:'Mix Rép+Rev'};

function yrCols(rows, total_yrs, N){
  let h='';
  for(let k=1;k<=total_yrs;k++){
    const oa = k<=N;
    h+=`<th class="yr" style="background:${oa?'#1e3a5f':'#374151'}">An ${k}${oa?' OA':' PPA'}</th>`;
  }
  return h;
}

function row(label, rows, fn, cls_fn=null, is_head=false, tag='td'){
  const cells = rows.map(r=>{
    const val=fn(r);
    const c=cls_fn?cls_fn(val,r):'';
    return `<td class="${c}">${val}</td>`;
  }).join('');
  const label_td = `<td class="row-label${is_head?' section-head':''}">${label}</td>`;
  return `<tr>${label_td}${cells}</tr>`;
}

function renderScenario(s, p, fin, sc){
  const color=STRAT_COLORS[s];
  const {rows, CAPEX, equity, debt, total_yrs, ROE, total_net} = sc;
  const N=p.N;

  // ── KPIs
  let html=`<div class="kpis">
    <div class="kpi"><div class="label">CAPEX</div><div class="val">${fmtE(CAPEX)}</div></div>
    <div class="kpi"><div class="label">Fonds propres</div><div class="val">${fmtE(equity)}</div></div>
    <div class="kpi"><div class="label">Dette</div><div class="val">${fmtE(debt)}</div></div>
    <div class="kpi"><div class="label">Durée totale</div><div class="val">${total_yrs} ans</div></div>
    <div class="kpi"><div class="label">ROE incrémental</div>
      <div class="val ${sc.ROE===null?'neutral':sc.ROE>=0?'pos':'neg'}">${sc.ROE===null?'N/A':fmtPct(sc.ROE)}</div>
      <div class="sub">Δ Trésorerie vs Défaut / FP</div></div>
    <div class="kpi"><div class="label">Δ Trésorerie cumulée vs Défaut</div>
      <div class="val ${sc.cum_incr_treas>=0?'pos':'neg'}">${fmtE(sc.cum_incr_treas)}</div></div>
  </div>`;

  // ── Loan table
  html+=`<div class="section-title">Échéancier d'emprunt</div>`;
  if(debt<=0){
    html+=`<p style="color:#64748b;margin-bottom:16px">Aucun emprunt (CAPEX = 0 ou 100 % fonds propres).</p>`;
  } else {
    html+=`<div class="tbl-wrap"><table>
    <thead><tr>
      <th class="row-label" style="background:#0f172a">Poste</th>${yrCols(rows,total_yrs,N)}
    </tr></thead><tbody>`;
    html+=row('Capital remboursé (€)',rows,r=>fmtE(r.loan.principal));
    html+=row('Intérêts (€)',         rows,r=>fmtE(r.loan.interest));
    html+=row('Total annuité (€)',    rows,r=>fmtE(r.loan.annuity));
    html+=row('Solde restant (€)',    rows,r=>fmtE(r.loan.balance));
    html+=`</tbody></table></div>`;
  }

  // ── P&L table
  html+=`<div class="section-title">Compte de Résultat &amp; Cash Flow</div>`;
  html+=`<div class="tbl-wrap"><table>
  <thead><tr>
    <th class="row-label" style="background:${color}">Poste</th>${yrCols(rows,total_yrs,N)}
  </tr></thead><tbody>`;

  // Revenue
  html+=`<tr><td class="row-label section-head">── Revenus</td>${rows.map(r=>`<td class="neutral" style="font-size:10px">${(r.tarif_k).toFixed(4)} €/kWh</td>`).join('')}</tr>`;
  html+=row('Production (MWh/an)',        rows,r=>fmtMWh(r.prod_kWh));
  html+=`<tr class="total"><td class="row-label">Chiffre d'affaires (€)</td>${rows.map(r=>`<td class="pos">${fmtE(r.CA)}</td>`).join('')}</tr>`;

  // Costs
  html+=`<tr><td class="row-label section-head">── Charges</td>${rows.map(()=>'<td></td>').join('')}</tr>`;
  html+=`<tr class="sub"><td class="row-label">  Maintenance (${fmtPct(fin.maint_pct)} CA)</td>${rows.map(r=>`<td>${fmtE(r.maintenance)}</td>`).join('')}</tr>`;
  html+=`<tr class="sub"><td class="row-label">  OPEX (${fmtPct(fin.opex_pct)} CA)</td>${rows.map(r=>`<td>${fmtE(r.opex)}</td>`).join('')}</tr>`;
  html+=`<tr class="sub"><td class="row-label">  Assurance (${fmtPct(fin.ins_pct)} CA)</td>${rows.map(r=>`<td>${fmtE(r.insurance)}</td>`).join('')}</tr>`;
  html+=`<tr class="sub"><td class="row-label">  Loyer (€)</td>${rows.map(r=>`<td>${fmtE(r.rent)}</td>`).join('')}</tr>`;

  // EBITDA
  html+=`<tr class="total"><td class="row-label">EBITDA (€)</td>${rows.map(r=>`<td class="${cls(r.EBITDA)}">${fmtE(r.EBITDA)}</td>`).join('')}</tr>`;

  html+=`<tr class="sub"><td class="row-label">  Amortissement (€)</td>${rows.map(r=>`<td>${fmtE(r.amort)}</td>`).join('')}</tr>`;
  html+=`<tr class="total"><td class="row-label">EBIT (€)</td>${rows.map(r=>`<td class="${cls(r.EBIT)}">${fmtE(r.EBIT)}</td>`).join('')}</tr>`;

  // Financial
  html+=`<tr><td class="row-label section-head">── Résultat financier</td>${rows.map(()=>'<td></td>').join('')}</tr>`;
  html+=`<tr class="sub"><td class="row-label">  Intérêts d'emprunt (−)</td>${rows.map(r=>`<td class="${r.int_exp>0?'neg':''}">${fmtE(-r.int_exp)}</td>`).join('')}</tr>`;
  html+=`<tr class="sub"><td class="row-label">  Intérêts trésorerie (+)</td>${rows.map(r=>`<td class="${r.int_inc>0?'pos':''}">${fmtE(r.int_inc)}</td>`).join('')}</tr>`;
  html+=`<tr class="sub"><td class="row-label">  Résultat financier net</td>${rows.map(r=>`<td class="${cls(r.fin_res)}">${fmtE(r.fin_res)}</td>`).join('')}</tr>`;

  // Tax / Net
  html+=`<tr class="total"><td class="row-label">Résultat avant impôt (EBT)</td>${rows.map(r=>`<td class="${cls(r.EBT)}">${fmtE(r.EBT)}</td>`).join('')}</tr>`;
  html+=`<tr class="sub"><td class="row-label">  Impôt (${fmtPct(fin.tax_rate)})</td>${rows.map(r=>`<td>${fmtE(-r.tax)}</td>`).join('')}</tr>`;
  html+=`<tr class="highlight"><td class="row-label">Résultat net (€)</td>${rows.map(r=>`<td class="${cls(r.net)}">${fmtE(r.net)}</td>`).join('')}</tr>`;

  // Cash flow
  html+=`<tr><td class="row-label section-head">── Cash Flow &amp; Trésorerie</td>${rows.map(()=>'<td></td>').join('')}</tr>`;
  html+=`<tr class="sub"><td class="row-label">  Cash flow opérationnel</td>${rows.map(r=>`<td class="${cls(r.op_cf)}">${fmtE(r.op_cf)}</td>`).join('')}</tr>`;
  html+=`<tr class="sub"><td class="row-label">  Remboursement dette</td>${rows.map(r=>`<td class="${r.debt_repay>0?'neg':''}">${r.debt_repay>0?fmtE(-r.debt_repay):'—'}</td>`).join('')}</tr>`;
  html+=`<tr class="total"><td class="row-label">Trésorerie annuelle</td>${rows.map(r=>`<td class="${cls(r.ann_treas)}">${fmtE(r.ann_treas)}</td>`).join('')}</tr>`;
  html+=`<tr class="total"><td class="row-label">Trésorerie cumulée</td>${rows.map(r=>`<td class="${cls(r.cum_treas)}">${fmtE(r.cum_treas)}</td>`).join('')}</tr>`;
  html+=`<tr class="total"><td class="row-label">Δ Trésorerie cumulée vs Défaut</td>${rows.map(r=>`<td class="${cls(r.cum_incr_treas)}">${fmtE(r.cum_incr_treas)}</td>`).join('')}</tr>`;
  html+=`<tr><td class="row-label" style="color:#64748b;font-size:10px">  EBITDA incrémental vs Défaut</td>${rows.map(r=>`<td class="${cls(r.incr_ebitda)}" style="font-size:10px">${fmtE(r.incr_ebitda)}</td>`).join('')}</tr>`;
  html+=`<tr class="dscr"><td class="row-label">DSCR (EBITDA incrémental / dette)</td>${rows.map(r=>`<td class="${r.dscr===null?'neutral':r.dscr>=1.2?'pos':r.dscr>=1?'neutral':'neg'}">${r.dscr===null?'—':r.dscr.toFixed(2)}</td>`).join('')}</tr>`;

  html+=`</tbody></table></div>`;
  return html;
}

// ── Synthèse ──────────────────────────────────────────────────────────────────
const STRATS=['defaut','repow','rep','rev','mix'];

function renderSynthese(p, fin, results){
  const sRow = (label, fn, cls_fn=null) => {
    let h=`<tr><td class="row-label">${label}</td>`;
    for(const s of STRATS){
      const val=fn(s, results[s]);
      const c=cls_fn?cls_fn(val,s):'';
      h+=`<td class="${c}">${val}</td>`;
    }
    return h+'</tr>';
  };

  let html=`<table><thead><tr>
    <th class="row-label" style="background:#0f172a;min-width:220px">Indicateur</th>`;
  for(const s of STRATS){
    html+=`<th style="background:${STRAT_COLORS[s]};min-width:110px;text-align:center">${STRAT_LABELS[s]}</th>`;
  }
  html+=`</tr></thead><tbody>`;

  html+=sRow('CAPEX', (s,r)=>fmtE(r.CAPEX));
  html+=sRow('Fonds propres (€)', (s,r)=>fmtE(r.equity));
  html+=sRow('Dette (€)', (s,r)=>fmtE(r.debt));
  html+=sRow('Durée totale (ans)', (s,r)=>r.total_yrs+' ans');

  html+=`<tr><td class="row-label section-head">── Revenus & Charges</td>${STRATS.map(()=>'<td></td>').join('')}</tr>`;
  html+=sRow('CA cumulé (€)', (s,r)=>fmtE(r.rows.reduce((a,x)=>a+x.CA,0)));
  html+=sRow('Charges cumulées (€)', (s,r)=>fmtE(r.rows.reduce((a,x)=>a+x.maintenance+x.opex+x.insurance+x.rent,0)));
  html+=sRow('EBITDA cumulé (€)', (s,r)=>fmtE(r.rows.reduce((a,x)=>a+x.EBITDA,0)),
    (val,s)=>val.includes('-')?'neg':'pos');

  html+=`<tr><td class="row-label section-head">── Résultats</td>${STRATS.map(()=>'<td></td>').join('')}</tr>`;
  html+=sRow('Résultat net cumulé (€)', (s,r)=>fmtE(r.total_net),
    (val)=>val.includes('-')?'neg':'pos');
  html+=sRow('Trésorerie finale (€)', (s,r)=>fmtE(r.rows[r.rows.length-1].cum_treas),
    (val)=>val.includes('-')?'neg':'pos');
  html+=sRow('Δ Trésorerie vs Défaut (€)', (s,r)=>s==='defaut'?'—':fmtE(r.cum_incr_treas),
    (val)=>val==='—'?'neutral':val.includes('-')?'neg':'pos');
  html+=sRow('ROE incrémental', (s,r)=>r.ROE===null?'N/A':fmtPct(r.ROE),
    (val)=>val==='N/A'?'neutral':val.startsWith('-')?'neg':'pos');
  html+=sRow('DSCR moyen', (s,r)=>{
    const dscrVals=r.rows.filter(x=>x.dscr!==null).map(x=>x.dscr);
    if(!dscrVals.length) return '—';
    return (dscrVals.reduce((a,b)=>a+b,0)/dscrVals.length).toFixed(2);
  },(val)=>val==='—'?'neutral':parseFloat(val)>=1.2?'pos':parseFloat(val)>=1?'neutral':'neg');

  html+=`</tbody></table>`;
  document.getElementById('synthese-wrap').innerHTML=html;
}

// ── Main update ───────────────────────────────────────────────────────────────
function update(){
  const p   = getParams();
  const fin = getFinParams();

  document.getElementById('pmfac-box').innerHTML=
    `<b>Panneau à façon :</b> ${p.Pm_fac.toFixed(0)} Wc · gap = ${p.gap_kWc.toFixed(0)} kWc`;

  // Pré-calcul Défaut de référence pour chaque durée de projet
  const def_ref_N1 = calcDefautRows(p, fin, p.N+p.N1);
  const def_ref_N2 = calcDefautRows(p, fin, p.N+p.N2);

  const results={};
  // Défaut : pas de référence incrémentale (il EST la référence)
  results['defaut'] = calcScenario('defaut', p, fin, null);
  // Autres scénarios : référence Défaut sur la même durée
  for(const s of ['rep','rev','mix']){
    results[s] = calcScenario(s, p, fin, def_ref_N1);
  }
  results['repow'] = calcScenario('repow', p, fin, def_ref_N2);

  for(const s of STRATS){
    document.getElementById('pane-'+s).innerHTML=renderScenario(s,p,fin,results[s]);
  }
  renderSynthese(p,fin,results);
}

update();
</script>
</body>
</html>
"""

OUT = os.path.join(os.path.dirname(__file__), "tableaux_financier_scenarios.html")
with open(OUT, "w", encoding="utf-8") as f:
    f.write(HTML)

print(f"✓ Généré : {OUT}")
