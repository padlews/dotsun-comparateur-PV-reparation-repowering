"""
DOTSun — Tableaux Financiers PV (Streamlit)
Deployable on share.streamlit.io
"""
import math, os
import streamlit as st

st.set_page_config(page_title="DOTSun — Tableaux Financiers PV",
                   page_icon="🌞", layout="wide",
                   initial_sidebar_state="expanded")

# ── Presets ───────────────────────────────────────────────────────────────────
PRESETS = {
    "s1": dict(n=40000,Pm=300,H=1200,Y=10,d=0.40,dn=6.0,eff_iv=0.0,N=10,tarif=0.0818,PPA=0.03,
               N1=5,N2=10,Crep=25,Cdm=4,Cde=15,Cfac=0.25,Crev=0.5,
               Down_rep=1.0,Down_repow=8.0,u=10.0,alpha_pct=85,
               equity_pct=20.0,loan_dur=10,int_rate=4.0,infl_rate=2.0,
               tax_rate=25.0,maint_pct=5.0,opex_pct=2.0,ins_pct=1.5,
               rent=10000.0,amort_dur=10,treas_rate=1.0),
    "s2": dict(n=4304,Pm=195,H=1180,Y=14,d=0.45,dn=8.0,eff_iv=0.0,N=6,tarif=0.75,PPA=0.03,
               N1=5,N2=15,Crep=30,Cdm=5,Cde=18,Cfac=0.30,Crev=0.70,
               Down_rep=1.0,Down_repow=8.0,u=10.0,alpha_pct=80,
               equity_pct=20.0,loan_dur=10,int_rate=4.0,infl_rate=2.0,
               tax_rate=25.0,maint_pct=5.0,opex_pct=2.0,ins_pct=1.5,
               rent=10000.0,amort_dur=10,treas_rate=1.0),
}
PKEYS = list(PRESETS["s1"].keys())

def init_state(k):
    for pk, pv in PRESETS[k].items():
        st.session_state[f"fp_{pk}"] = pv

if "fp_init" not in st.session_state:
    init_state("s1")
    st.session_state.fp_init = True

# ── Calculation functions ─────────────────────────────────────────────────────
def get_params():
    p = {k: st.session_state[f"fp_{k}"] for k in PKEYS}
    n, Pm = float(p['n']), float(p['Pm'])
    d = float(p['d']) / 100
    Y, u = float(p['Y']), float(p['u']) / 100
    alpha_rep = float(p['alpha_pct']) / 100
    Pcentrale = n * Pm / 1000
    eff_iv = float(p.get('eff_iv', 0.0))
    I2 = (eff_iv / 100) if eff_iv > 0 else (1 - d) ** Y
    alpha_rev = 1 - alpha_rep
    P_res_rep = alpha_rep * n * Pm * I2 / 1000
    gap_kWc = max(0.0, Pcentrale - P_res_rep)
    n_rev = alpha_rev * n
    Pm_fac = gap_kWc * 1000 / n_rev if n_rev > 0 else 0.0
    capex = {
        'defaut': 0.0,
        'rep':    n * (float(p['Crep']) + float(p['Cdm'])),
        'rev':    n * (Pm * float(p['Cfac']) + float(p['Cdm'])),
        'repow':  n * float(p['Cde']) + Pcentrale * 1000 * (1+u) * float(p['Crev']),
        'mix':    alpha_rep * n * (float(p['Crep']) + float(p['Cdm'])) + gap_kWc * 1000 * float(p['Cfac']),
    }
    p.update(Pcentrale=Pcentrale, I2=I2, alpha_rev=alpha_rev, gap_kWc=gap_kWc,
             n_rev=n_rev, Pm_fac=Pm_fac, capex=capex,
             d_=d, dn_=float(p['dn'])/100, u_=u, alpha_rep=alpha_rep)
    return p

def get_fin():
    return {k: st.session_state[f"fp_{k}"]
            for k in ['equity_pct','loan_dur','int_rate','infl_rate',
                      'tax_rate','maint_pct','opex_pct','ins_pct',
                      'rent','amort_dur','treas_rate']}

def _power(s, k, p):
    Pc,I2,d,dn,u = p['Pcentrale'],p['I2'],p['d_'],p['dn_'],p['u_']
    if s=='defaut': return Pc*I2*(1-dn)**(k-1)
    if s=='rep':    return Pc*I2*(1-d)**(k-1)
    if s=='rev':    return Pc*(1-d)**(k-1)
    if s=='repow':  return Pc*(1+u)*(1-d)**(k-1)
    if s=='mix':    return Pc*(1-d)**(k-1)

def _dfactor(s, k, p):
    N = int(p['N'])
    if s=='defaut': return 1.0
    if s=='repow':  return (1-float(p['Down_repow'])/12) if k==N else 1.0
    return (1-float(p['Down_rep'])/12) if k==1 else 1.0

def calc_loan(debt, int_rate, loan_dur, total_yrs):
    if debt <= 0:
        return [dict(k=k,principal=0,interest=0,annuity=0,balance=0) for k in range(1,total_yrs+1)]
    r = int_rate / 100
    ann = debt*r/(1-(1+r)**(-loan_dur)) if r > 0 else debt/loan_dur
    bal, rows = debt, []
    for k in range(1, total_yrs+1):
        if k <= loan_dur:
            interest = bal * r
            principal = min(ann - interest, bal)
            bal = max(0.0, bal - principal)
            rows.append(dict(k=k,principal=principal,interest=interest,annuity=principal+interest,balance=bal))
        else:
            rows.append(dict(k=k,principal=0,interest=0,annuity=0,balance=0))
    return rows

def calc_defaut_ref(p, fin, total_yrs):
    rows, cum = [], 0.0
    N = int(p['N'])
    for k in range(1, total_yrs+1):
        tarif_k = float(p['tarif']) if k<=N else float(p['PPA'])
        CA = tarif_k * float(p['H']) * _power('defaut', k, p)
        EBITDA = CA * (1 - fin['maint_pct']/100 - fin['opex_pct']/100 - fin['ins_pct']/100) \
                 - fin['rent'] * (1+fin['infl_rate']/100)**(k-1)
        ann = EBITDA - max(0, EBITDA * fin['tax_rate']/100)
        cum += ann
        rows.append(dict(k=k, EBITDA=EBITDA, ann_treas=ann, cum_treas=cum))
    return rows

def calc_scenario(s, p, fin, def_ref=None):
    N = int(p['N'])
    total_yrs = N + int(p['N2']) if s=='repow' else N + int(p['N1'])
    CAPEX = p['capex'][s]
    equity = CAPEX * fin['equity_pct'] / 100
    debt   = CAPEX * (1 - fin['equity_pct']/100)
    loan   = calc_loan(debt, fin['int_rate'], int(fin['loan_dur']), total_yrs)
    rows, cum_treas, total_net, cum_incr = [], 0.0, 0.0, 0.0
    for k in range(1, total_yrs+1):
        tarif_k = float(p['tarif']) if k<=N else float(p['PPA'])
        prod    = float(p['H']) * _power(s, k, p) * _dfactor(s, k, p)
        CA      = tarif_k * prod
        maint   = CA * fin['maint_pct']/100
        opex    = CA * fin['opex_pct']/100
        ins     = CA * fin['ins_pct']/100
        rent    = fin['rent'] * (1+fin['infl_rate']/100)**(k-1)
        amort   = CAPEX/int(fin['amort_dur']) if (k<=int(fin['amort_dur']) and CAPEX>0) else 0.0
        EBITDA  = CA - maint - opex - ins - rent
        EBIT    = EBITDA - amort
        int_exp = loan[k-1]['interest']
        int_inc = max(0.0, cum_treas) * fin['treas_rate']/100
        fin_res = int_inc - int_exp
        EBT     = EBIT + fin_res
        tax     = max(0.0, EBT * fin['tax_rate']/100)
        net     = EBT - tax
        op_cf   = net + amort
        repay   = loan[k-1]['principal']
        ann_tr  = op_cf - repay
        cum_treas += ann_tr;  total_net += net
        def_eb  = def_ref[k-1]['EBITDA']    if def_ref else EBITDA
        def_at  = def_ref[k-1]['ann_treas'] if def_ref else ann_tr
        incr_eb = EBITDA - def_eb
        cum_incr += ann_tr - def_at
        dscr = incr_eb / loan[k-1]['annuity'] if loan[k-1]['annuity'] > 0 else None
        rows.append(dict(k=k, tarif_k=tarif_k, prod=prod, CA=CA,
                         maint=maint, opex=opex, ins=ins, rent=rent, amort=amort,
                         EBITDA=EBITDA, EBIT=EBIT,
                         int_exp=int_exp, int_inc=int_inc, fin_res=fin_res,
                         EBT=EBT, tax=tax, net=net,
                         op_cf=op_cf, repay=repay, ann_treas=ann_tr, cum_treas=cum_treas,
                         incr_eb=incr_eb, cum_incr=cum_incr, dscr=dscr, loan=loan[k-1]))
    ROE = cum_incr / equity if equity > 0 else None
    dvals = [r['dscr'] for r in rows if r['dscr'] is not None]
    dscr_avg = sum(dvals)/len(dvals) if dvals else None
    return dict(CAPEX=CAPEX, equity=equity, debt=debt, total_yrs=total_yrs,
                rows=rows, ROE=ROE, total_net=total_net, cum_incr=cum_incr, dscr_avg=dscr_avg)

def run_all(p, fin):
    ref1 = calc_defaut_ref(p, fin, int(p['N'])+int(p['N1']))
    ref2 = calc_defaut_ref(p, fin, int(p['N'])+int(p['N2']))
    res = {'defaut': calc_scenario('defaut', p, fin, None)}
    for s in ['rep','rev','mix']: res[s] = calc_scenario(s, p, fin, ref1)
    res['repow'] = calc_scenario('repow', p, fin, ref2)
    return res

def compute_comparateur(p):
    """Revenue-only comparison (no financial hypotheses) — mirrors streamlit_app.py compute()."""
    N, N1, N2 = int(p['N']), int(p['N1']), int(p['N2'])
    Pc, I2, d, dn, u = p['Pcentrale'], p['I2'], p['d_'], p['dn_'], p['u_']
    tarif, PPA = float(p['tarif']), float(p['PPA'])
    H = float(p['H'])
    Down_rep, Down_repow = float(p['Down_rep']), float(p['Down_repow'])
    capex = p['capex']
    ext = {'defaut': N1, 'rep': N1, 'rev': N1, 'repow': N2, 'mix': N1}

    def power(s, k):
        if s == 'defaut': return Pc * I2 * (1-dn)**(k-1)
        if s == 'rep':    return Pc * I2 * (1-d)**(k-1)
        if s == 'rev':    return Pc * (1-d)**(k-1)
        if s == 'repow':  return Pc * (1+u) * (1-d)**(k-1)
        if s == 'mix':    return Pc * (1-d)**(k-1)

    def dfactor(s, k):
        if s == 'defaut': return 1.0
        if s == 'repow':  return (1-Down_repow/12) if k==N else 1.0
        return (1-Down_rep/12) if k==1 else 1.0

    revOA, revPost, cfOA, cfTotal, delta, pct = {}, {}, {}, {}, {}, {}
    for s in STRATS:
        rOA   = sum(H * tarif * power(s, k) * dfactor(s, k) for k in range(1, N+1))
        rPost = sum(H * PPA   * power(s, k)                  for k in range(N+1, N+ext[s]+1))
        revOA[s]   = rOA
        revPost[s] = rPost
        cfOA[s]    = rOA - capex[s]
        cfTotal[s] = cfOA[s] + rPost
    for s in STRATS:
        delta[s] = cfTotal[s] - cfTotal['defaut']
        pct[s]   = delta[s] / cfTotal['defaut'] if cfTotal['defaut'] != 0 else 0.0
    return dict(revOA=revOA, revPost=revPost, cfOA=cfOA, cfTotal=cfTotal,
                delta=delta, pct=pct, ext=ext)

# ── Formatters ────────────────────────────────────────────────────────────────
def fe(x):
    if x is None or (isinstance(x, float) and math.isnan(x)): return '—'
    s = '-' if x < 0 else ''; a = abs(x)
    if a >= 1e6: return f"{s}{a/1e6:.2f} M€"
    if a >= 1e3: return f"{s}{a/1e3:.1f} k€"
    return f"{s}{a:.0f} €"

def fp(x):
    if x is None: return '—'
    return f"{'+'if x>=0 else ''}{x*100:.1f}%"

def fmwh(x): return f"{x/1000:.0f} MWh"

def frate(x): return f"{x:.4f} €/kWh"

# ── HTML table helpers ────────────────────────────────────────────────────────
STRATS  = ['defaut','repow','rep','rev','mix']
COLORS  = {'defaut':'#374151','repow':'#b91c1c','rep':'#166534','rev':'#1e3a5f','mix':'#166534'}
LABELS  = {'defaut':'Défaut','repow':'Repowering','rep':'Réparation','rev':'Revamping','mix':'Mix Rép+Rev'}

def _td(val, color='#1e293b', bg='', bold=False, align='center'):
    bgs = f"background:{bg};" if bg else ''
    bw  = 'font-weight:700;' if bold else ''
    return (f'<td style="padding:4px 7px;text-align:{align};border-bottom:1px solid #f1f5f9;'
            f'{bgs}"><span style="font-size:13px;color:{color};{bw}">{val}</span></td>')

def _tdl(label, bg='#f8fafc', color='#475569', bold=False, section=False):
    bw  = 'font-weight:700;' if bold or section else 'font-weight:500;'
    col = '#fff' if section else color
    bgs = '#1e293b' if section else bg
    return (f'<td style="padding:4px 8px;text-align:left;background:{bgs};'
            f'border-bottom:1px solid #e2e8f0;width:210px;min-width:210px;max-width:210px;'
            f'position:sticky;left:0;z-index:1">'
            f'<span style="font-size:13px;color:{col};{bw}">{label}</span></td>')

def _th(label, bg='#0f172a', align='center'):
    return (f'<th style="background:{bg};color:#fff;padding:5px 7px;text-align:{align};'
            f'font-size:12px;font-weight:700;white-space:nowrap">{label}</th>')

def val_color(x):
    if x is None: return '#64748b'
    return '#166534' if x > 0 else ('#b91c1c' if x < 0 else '#64748b')

def dscr_color(x):
    if x is None or not isinstance(x, (int, float)): return '#64748b'
    return '#166534' if x >= 1.2 else ('#64748b' if x >= 1.0 else '#b91c1c')

def render_scenario_table(s, sc, N):
    rows = sc['rows']
    color = COLORS[s]

    # Year header
    yr_ths = ''.join(
        f'<th style="background:{"#1e3a5f" if r["k"]<=N else "#374151"};'
        f'color:#fff;padding:5px 6px;text-align:center;font-size:10px;'
        f'min-width:72px;white-space:nowrap">An {r["k"]}'
        f'{"" if r["k"]<=N else " PPA"}</th>'
        for r in rows
    )

    def data_row(label, fn, bg='', bold=False, col_fn=None, section=False):
        cells = ''
        for r in rows:
            val = fn(r)
            c = col_fn(val) if col_fn else val_color(val) if isinstance(val, float) else '#1e293b'
            cells += _td(val if isinstance(val,str) else fe(val), color=c, bg=bg, bold=bold)
        return f'<tr>{_tdl(label,bg=bg if bg else "#f8fafc",bold=bold,section=section)}{cells}</tr>'

    h = f'<div style="overflow-x:auto;margin-bottom:16px"><table style="border-collapse:collapse;width:100%;background:#fff">'
    h += (f'<thead><tr>'
          f'<th style="background:{color};color:#fff;padding:5px 8px;text-align:left;font-size:12px;'
          f'font-weight:700;width:210px;min-width:210px;max-width:210px;white-space:nowrap">Indicateur</th>'
          f'{yr_ths}</tr></thead><tbody>')

    # Loan
    if sc['debt'] > 0:
        h += f'<tr>{_tdl("── Échéancier emprunt",section=True)}{"".join(_td("",bg="#1e293b") for _ in rows)}</tr>'
        h += data_row("Capital remboursé", lambda r: r['loan']['principal'])
        h += data_row("Intérêts", lambda r: r['loan']['interest'])
        h += data_row("Total annuité", lambda r: r['loan']['annuity'], bold=True)
        h += data_row("Solde restant", lambda r: r['loan']['balance'])

    # Revenue
    h += f'<tr>{_tdl("── Revenus",section=True)}{"".join(_td("",bg="#1e293b") for _ in rows)}</tr>'
    h += f'<tr>{_tdl("Tarif (€/kWh)")}'
    h += ''.join(_td(f"{r['tarif_k']:.4f}", color='#64748b') for r in rows) + '</tr>'
    h += f'<tr>{_tdl("Production (MWh/an)")}'
    h += ''.join(_td(f"{r['prod']/1000:.0f}", color='#1e293b') for r in rows) + '</tr>'
    h += data_row("Chiffre d'affaires", lambda r: r['CA'], bg='#f0fdf4', bold=True,
                  col_fn=lambda _: '#166534')

    # Costs
    h += f'<tr>{_tdl("── Charges",section=True)}{"".join(_td("",bg="#1e293b") for _ in rows)}</tr>'
    h += data_row("  Maintenance",  lambda r: r['maint'],  col_fn=lambda _: '#64748b')
    h += data_row("  OPEX",         lambda r: r['opex'],   col_fn=lambda _: '#64748b')
    h += data_row("  Assurance",    lambda r: r['ins'],    col_fn=lambda _: '#64748b')
    h += data_row("  Loyer",        lambda r: r['rent'],   col_fn=lambda _: '#64748b')
    h += data_row("EBITDA",         lambda r: r['EBITDA'], bold=True, bg='#fefce8')
    h += data_row("  Amortissement",lambda r: r['amort'],  col_fn=lambda _: '#64748b')
    h += data_row("EBIT",           lambda r: r['EBIT'],   bold=True)

    # Financial
    h += f'<tr>{_tdl("── Résultat financier",section=True)}{"".join(_td("",bg="#1e293b") for _ in rows)}</tr>'
    h += data_row("  Intérêts emprunt (−)", lambda r: -r['int_exp'])
    h += data_row("  Intérêts trésorerie (+)", lambda r: r['int_inc'])
    h += data_row("  Résultat financier net", lambda r: r['fin_res'])
    h += data_row("Résultat avant impôt (EBT)", lambda r: r['EBT'], bold=True)
    h += data_row("  Impôt",        lambda r: -r['tax'],   col_fn=lambda _: '#64748b')
    h += data_row("Résultat net",   lambda r: r['net'],    bold=True, bg='#f0fdf4')

    # Cash flow
    h += f'<tr>{_tdl("── Cash Flow & Trésorerie",section=True)}{"".join(_td("",bg="#1e293b") for _ in rows)}</tr>'
    h += data_row("  Cash flow opérationnel", lambda r: r['op_cf'])
    h += data_row("  Remboursement dette",    lambda r: -r['repay'])
    h += data_row("Trésorerie annuelle", lambda r: r['ann_treas'], bold=True)
    h += data_row("Trésorerie cumulée",  lambda r: r['cum_treas'], bold=True, bg='#fefce8')
    h += data_row("Δ Trésorerie cumulée vs Défaut", lambda r: r['cum_incr'], bold=True, bg='#f0fdf4')
    h += f'<tr>{_tdl("EBITDA incrémental vs Défaut",bold=False)}'
    h += ''.join(_td(fe(r['incr_eb']), color=val_color(r['incr_eb'])) for r in rows) + '</tr>'
    h += f'<tr>{_tdl("DSCR (incrémental)",bold=True)}'
    h += ''.join(_td('—' if r['dscr'] is None else f"{r['dscr']:.2f}",
                     color=dscr_color(r['dscr']), bold=True) for r in rows) + '</tr>'

    h += '</tbody></table></div>'
    return h

def render_synthesis(results):
    def srow(label, fn, bold=False, section=False, col_fn=None):
        h = f'<tr>{_tdl(label, bold=bold, section=section)}'
        for s in STRATS:
            v = fn(s, results[s])
            c = col_fn(v) if col_fn else '#1e293b'
            h += _td(v, color=c, bold=bold)
        return h + '</tr>'

    h = '<div style="overflow-x:auto;margin-bottom:20px"><table style="border-collapse:collapse;background:#fff;width:100%"><thead><tr>'
    h += ('<th style="background:#0f172a;color:#fff;padding:5px 8px;text-align:left;font-size:12px;'
          'font-weight:700;width:210px;min-width:210px;max-width:210px;white-space:nowrap">Indicateur</th>')
    for s in STRATS:
        h += f'<th style="background:{COLORS[s]};color:#fff;padding:6px 10px;text-align:center;font-size:11px;min-width:110px">{LABELS[s]}</th>'
    h += '</tr></thead><tbody>'

    h += srow("CAPEX", lambda s,r: fe(r['CAPEX']))
    h += srow("Fonds propres (€)", lambda s,r: fe(r['equity']))
    h += srow("Dette (€)", lambda s,r: fe(r['debt']))
    h += srow("Durée totale (ans)", lambda s,r: f"{r['total_yrs']} ans")

    h += srow("── Revenus & Charges", lambda s,r: '', section=True)
    h += srow("CA cumulé (€)", lambda s,r: fe(sum(x['CA'] for x in r['rows'])),
              col_fn=lambda v: '#166534')
    h += srow("EBITDA cumulé (€)", lambda s,r: fe(sum(x['EBITDA'] for x in r['rows'])),
              col_fn=lambda v: '#166534' if '-' not in v and v!='—' else '#b91c1c')

    h += srow("── Résultats", lambda s,r: '', section=True)
    h += srow("Résultat net cumulé (€)", lambda s,r: fe(r['total_net']), bold=True,
              col_fn=lambda v: '#166534' if '-' not in v and v!='—' else '#b91c1c')
    h += srow("Trésorerie finale (€)", lambda s,r: fe(r['rows'][-1]['cum_treas']),
              col_fn=lambda v: '#166534' if '-' not in v and v!='—' else '#b91c1c')
    h += srow("Δ Trésorerie vs Défaut (€)", lambda s,r: '—' if s=='defaut' else fe(r['cum_incr']),
              bold=True,
              col_fn=lambda v: '#64748b' if v=='—' else '#166534' if '-' not in v else '#b91c1c')
    h += srow("ROE incrémental", lambda s,r: '—' if r['ROE'] is None else fp(r['ROE']),
              bold=True,
              col_fn=lambda v: '#64748b' if v=='—' else '#166534' if '-' not in v else '#b91c1c')
    h += srow("DSCR moyen", lambda s,r: '—' if r['dscr_avg'] is None else f"{r['dscr_avg']:.2f}",
              col_fn=dscr_color)

    h += '</tbody></table></div>'
    return h

def render_comparateur_table(p, rc):
    alpha_pct = int(p['alpha_pct'])
    u_pct     = int(p['u'])
    Pc, I2, u = p['Pcentrale'], p['I2'], p['u_']

    TH_COMP = {
        'defaut': ('#374151', 'Défaut',      'En l\'état'),
        'rep':    ('#166534', 'Réparation',  '100 % panneaux'),
        'rev':    ('#1e3a5f', 'Revamping',   '100 % panneaux'),
        'repow':  ('#b91c1c', 'Repowering',  f'+{u_pct} % capacité'),
        'mix':    ('#92400e', 'Mix Rép+Rev', f'{alpha_pct}% + {100-alpha_pct}%'),
    }

    def th_comp(s):
        bg = ('repeating-linear-gradient(135deg,#166534,#166534 5px,#1e3a5f 5px,#1e3a5f 10px)'
              if s == 'mix' else TH_COMP[s][0])
        title, sub = TH_COMP[s][1], TH_COMP[s][2]
        return (f'<th style="background:{bg};color:#fff;padding:10px 14px;text-align:center;'
                f'font-size:12px;font-weight:600;white-space:nowrap">'
                f'{title}<br><small style="font-weight:400;opacity:.85">{sub}</small></th>')

    def vs(txt, color='#1e293b', bold=False):
        bw = 'font-weight:700;' if bold else ''
        return f'<span style="font-size:13px;color:{color};{bw}">{txt}</span>'

    LBL_STYLE = ('padding:8px 14px;text-align:left;width:210px;min-width:210px;max-width:210px;'
                 'border-bottom:1px solid #f1f5f9;background:#f8fafc')
    VAL_STYLE = 'padding:8px 14px;text-align:center;border-bottom:1px solid #f1f5f9'

    def trow(label, cells, bg=''):
        tr = f'<tr style="background:{bg}">' if bg else '<tr>'
        tds = ''.join(f'<td style="{VAL_STYLE}">{c}</td>' for c in cells)
        return (f'{tr}<td style="{LBL_STYLE}">'
                f'<span style="font-size:13px;color:#475569">{label}</span></td>{tds}</tr>')

    ext = rc['ext']
    best_s = max(STRATS, key=lambda s: rc['cfTotal'][s])

    pow_cells = [
        vs(f"{round(Pc*I2)} kWc"),
        vs(f"{round(Pc*(1+u))} kWc"),
        vs(f"{round(Pc*I2)} kWc"),
        vs(f"{round(Pc)} kWc"),
        vs(f"{round(Pc)} kWc"),
    ]
    ext_cells   = [vs('—' if ext[s]==0 else f"+{int(ext[s])} ans PPA") for s in STRATS]
    capex_cells = [vs(fe(p['capex'][s])) for s in STRATS]
    revOA_cells = [vs(fe(rc['revOA'][s])) for s in STRATS]
    cfOA_cells  = [vs(fe(rc['cfOA'][s])) for s in STRATS]
    revPst_cells= [vs(fe(rc['revPost'][s])) for s in STRATS]

    cfT_cells = []
    for s in STRATS:
        badge = (' <span style="background:#dcfce7;color:#15803d;font-size:10px;'
                 'padding:2px 6px;border-radius:99px;font-weight:700">★</span>'
                 if s == best_s else '')
        cfT_cells.append(vs(fe(rc['cfTotal'][s]), bold=True) + badge)

    delta_cells, pct_cells = [], []
    for s in STRATS:
        if s == 'defaut':
            delta_cells.append(vs('—', '#64748b'))
            pct_cells.append(vs('—', '#64748b'))
        else:
            v = rc['delta'][s]
            col = '#16a34a' if v > 0 else ('#dc2626' if v < 0 else '#64748b')
            delta_cells.append(vs(fe(v), col, bold=True))
            vp = rc['pct'][s]
            colp = '#16a34a' if vp > 0 else ('#dc2626' if vp < 0 else '#64748b')
            pct_cells.append(vs(f"{'+'if vp>=0 else ''}{vp*100:.1f}%", colp, bold=True))

    h = ('<div style="overflow-x:auto;background:#fff;border-radius:12px;'
         'box-shadow:0 1px 3px rgba(0,0,0,.08);margin-bottom:16px">'
         '<table style="width:100%;border-collapse:collapse"><thead><tr>'
         '<th style="background:#0f172a;color:#fff;padding:10px 14px;text-align:left;'
         'width:210px;min-width:210px;max-width:210px;font-size:12px">Indicateur</th>')
    h += ''.join(th_comp(s) for s in STRATS)
    h += '</tr></thead><tbody>'
    h += trow("Puissance après intervention", pow_cells)
    h += trow("Extension post-OA", ext_cells)
    h += trow("CAPEX (€)", capex_cells)
    h += trow("Revenus cumulés EDF OA (€)", revOA_cells)
    h += trow("Cash Flow EDF OA (€)", cfOA_cells)
    h += trow("Revenus cumulés post-OA (€)", revPst_cells)
    h += trow("<strong>Cash Flow Total (€)</strong>", cfT_cells, bg='#fefce8')
    h += trow("ΔCCF vs Défaut (€)", delta_cells, bg='#f8fafc')
    h += trow("% vs Défaut", pct_cells, bg='#f8fafc')
    h += '</tbody></table></div>'
    return h

# ── PDF generation ────────────────────────────────────────────────────────────
def generate_pdf(p, fin, results, rc):
    from fpdf import FPDF
    from datetime import date as _date

    def _find_font(name):
        for path in [f"/usr/share/fonts/truetype/dejavu/{name}",
                     f"/usr/share/fonts/dejavu/{name}",
                     os.path.join(os.path.dirname(__import__("fpdf").__file__), "fonts", name)]:
            if os.path.exists(path): return path
        return None

    REG  = _find_font("DejaVuSans.ttf")
    BOLD = _find_font("DejaVuSans-Bold.ttf") or _find_font("DejaVuSansCondensed-Bold.ttf")
    if not REG:
        raise FileNotFoundError("DejaVuSans.ttf non trouvé. Vérifiez packages.txt.")

    STRAT_COLORS_RGB = {
        'defaut':(55,65,81),'repow':(185,28,28),'rep':(22,101,52),'rev':(30,58,95),'mix':(22,101,52)}

    DISCLAIMER = ("Ce document est fourni à titre informatif. Les projections reposent sur des "
                  "hypothèses de modélisation et ne garantissent pas les résultats futurs. "
                  "DOTSun SAS décline toute responsabilité quant à leur utilisation décisionnelle.")

    # ── Build parameters lists (used in portrait page) ──
    proj_params = [
        ("n — Panneaux", f"{int(p['n']):,}"),
        ("Pm (Wc)", f"{p['Pm']:.0f}"),
        ("Pcentrale (kWc)", f"{p['Pcentrale']:,.0f}"),
        ("H (kWh/kWc/an)", f"{p['H']:.0f}"),
        ("Y — Âge (ans)", f"{p['Y']:.0f}"),
        ("d — Dégr. normale (%/an)", f"{p['d']:.2f}%"),
        ("dn — Dégr. Défaut (%/an)", f"{p['dn']:.1f}%"),
        ("Eff. actuelle (Eff-IV)" if float(p.get('eff_iv',0))>0 else "Eff. calculée (d×Y)",
         f"{p['I2']*100:.2f}% *"),
        ("N — Années OA", f"{int(p['N'])}"),
        ("Tarif OA (€/kWh)", f"{p['tarif']:.4f}"),
        ("PPA post-OA (€/kWh)", f"{p['PPA']:.3f}"),
        ("N1 — Extension Rép/Rev", f"{int(p['N1'])} ans"),
        ("N2 — Extension Repow.", f"{int(p['N2'])} ans"),
    ]
    fin_params = [
        ("Fonds propres", f"{fin['equity_pct']:.0f}% du CAPEX"),
        ("Durée emprunt", f"{int(fin['loan_dur'])} ans"),
        ("Taux intérêt", f"{fin['int_rate']:.2f}%"),
        ("Inflation", f"{fin['infl_rate']:.2f}%"),
        ("Imposition", f"{fin['tax_rate']:.0f}%"),
        ("Maintenance", f"{fin['maint_pct']:.1f}% CA"),
        ("OPEX", f"{fin['opex_pct']:.1f}% CA"),
        ("Assurance", f"{fin['ins_pct']:.2f}% CA"),
        ("Loyer annuel", f"{fin['rent']:,.0f} €"),
        ("Amortissement", f"{int(fin['amort_dur'])} ans"),
        ("Intérêt trésorerie", f"{fin['treas_rate']:.2f}%"),
    ]

    lw, vw = 52, 22

    syn_labels = [
        "CAPEX","Fonds propres","Dette","Durée totale",
        "CA cumulé","EBITDA cumulé","Résultat net cumulé",
        "Trésorerie finale","Δ Trésorerie vs Défaut","ROE incrémental","DSCR moyen"
    ]
    def syn_val(s, sc, label):
        r = sc; rows = r['rows']
        if label=="CAPEX":               return fe(r['CAPEX'])
        if label=="Fonds propres":       return fe(r['equity'])
        if label=="Dette":               return fe(r['debt'])
        if label=="Durée totale":        return f"{r['total_yrs']} ans"
        if label=="CA cumulé":           return fe(sum(x['CA'] for x in rows))
        if label=="EBITDA cumulé":       return fe(sum(x['EBITDA'] for x in rows))
        if label=="Résultat net cumulé": return fe(r['total_net'])
        if label=="Trésorerie finale":   return fe(rows[-1]['cum_treas'])
        if label=="Δ Trésorerie vs Défaut": return '—' if s=='defaut' else fe(r['cum_incr'])
        if label=="ROE incrémental":     return '—' if r['ROE'] is None else f"{r['ROE']*100:.1f}%"
        if label=="DSCR moyen":         return '—' if r['dscr_avg'] is None else f"{r['dscr_avg']:.2f}"
        return '—'

    class MixedPDF(FPDF):
        def __init__(self):
            super().__init__(unit='mm', format='A4')
            self.add_font("dv", "",  REG)
            self.add_font("dv", "B", BOLD)
        def _f(self, style='', size=8): self.set_font("dv", style, size)
        def header(self):
            self._f("B", 12); self.set_text_color(30,41,59)
            w = self.get_string_width("DOT")
            self.cell(w, 7, "DOT")
            self.set_text_color(245,158,11)
            self.cell(self.get_string_width("Sun"), 7, "Sun")
            self._f("", 7); self.set_text_color(100,116,139)
            self.cell(0, 7, "   Tableaux Financiers — Scénarios de Rénovation PV", ln=True)
            self.set_draw_color(203,213,225)
            self.line(8, self.get_y(), self.w-8, self.get_y()); self.ln(2)
        def footer(self):
            self.set_y(-16)
            self.set_draw_color(203,213,225)
            self.line(8, self.get_y(), self.w-8, self.get_y()); self.ln(1)
            self._f("B",7); self.set_text_color(30,41,59)
            self.cell(self.get_string_width("DOT"), 4, "DOT")
            self.set_text_color(245,158,11)
            self.cell(self.get_string_width("Sun"), 4, "Sun")
            self._f("",6); self.set_text_color(100,116,139)
            self.cell(0, 4, f"   Rapport du {_date.today().strftime('%d/%m/%Y')}  |  Page {self.page_no()}")
            self.set_y(-11)
            self._f("",5); self.set_text_color(148,163,184)
            self.set_x(self.l_margin); self.multi_cell(0, 3, DISCLAIMER)

    mp = MixedPDF()
    mp.set_auto_page_break(auto=True, margin=22)

    STRAT_LABELS_FR = {'defaut':'Défaut','repow':'Repowering','rep':'Réparation',
                       'rev':'Revamping','mix':'Mix Rép+Rev'}

    # ── Shared helpers ──────────────────────────────────────────────────────────
    def _section(title):
        mp._f("B",10); mp.set_text_color(15,23,42)
        mp.cell(0,6,title,ln=True)
        mp.set_draw_color(203,213,225); mp.line(8,mp.get_y(),mp.w-8,mp.get_y()); mp.ln(2)

    def _params_table():
        for i in range(max(len(proj_params), len(fin_params))):
            bg=(248,250,252) if i%2==0 else (255,255,255); mp.set_fill_color(*bg)
            if i<len(proj_params):
                mp.set_text_color(100,116,139); mp._f("",7); mp.cell(lw,5,proj_params[i][0],fill=True)
                mp.set_text_color(15,23,42); mp._f("B",7); mp.cell(vw,5,proj_params[i][1],fill=True)
            else: mp.cell(lw+vw,5,"",fill=True)
            mp.cell(4,5,"")
            if i<len(fin_params):
                mp.set_text_color(100,116,139); mp._f("",7); mp.cell(lw,5,fin_params[i][0],fill=True)
                mp.set_text_color(15,23,42); mp._f("B",7); mp.cell(vw,5,fin_params[i][1],fill=True)
            mp.ln()

    def _syn_table():
        col_l = 46; col_v = (mp.w-16-col_l)/5
        mp._f("B",7); mp.set_text_color(255,255,255); mp.set_fill_color(15,23,42)
        mp.cell(col_l,6,"Indicateur",fill=True,border=0)
        for s in STRATS:
            mp.set_fill_color(*STRAT_COLORS_RGB[s])
            mp.cell(col_v,6,LABELS[s],fill=True,border=0,align='C')
        mp.ln()
        for i,lbl in enumerate(syn_labels):
            bg=(248,250,252) if i%2==0 else (255,255,255); mp.set_fill_color(*bg)
            bold_r = lbl in ("Résultat net cumulé","Δ Trésorerie vs Défaut","ROE incrémental")
            mp._f("B" if bold_r else "",7); mp.set_text_color(71,85,105)
            mp.cell(col_l,5.5,lbl,fill=True,border=0)
            for s in STRATS:
                mp.set_text_color(15,23,42)
                mp._f("B" if bold_r else "",7)
                mp.cell(col_v,5.5,syn_val(s,results[s],lbl),fill=True,border=0,align='C')
            mp.ln()

    def _strat_ren_table():
        col_lc = 50; col_vc = (mp.w-16-col_lc)/5
        mp._f("B",7); mp.set_text_color(255,255,255); mp.set_fill_color(15,23,42)
        mp.cell(col_lc,6,"Indicateur",fill=True,border=0)
        for s in STRATS:
            mp.set_fill_color(*STRAT_COLORS_RGB[s])
            mp.cell(col_vc,6,STRAT_LABELS_FR[s],fill=True,border=0,align='C')
        mp.ln()
        Pc_=p['Pcentrale']; I2_=p['I2']; u__=p['u_']
        pow_v=[f"{round(Pc_*I2_)} kWc",f"{round(Pc_*(1+u__))} kWc",
               f"{round(Pc_*I2_)} kWc",f"{round(Pc_)} kWc",f"{round(Pc_)} kWc"]
        ext_=rc['ext']
        ext_v=['—' if ext_[s]==0 else f"+{int(ext_[s])} ans" for s in STRATS]
        crow=[
            ("Puissance après intervention", pow_v,                                    False,False),
            ("Extension post-OA",            ext_v,                                    False,False),
            ("CAPEX",    [fe(p['capex'][s])    for s in STRATS],                       False,False),
            ("Revenus OA",[fe(rc['revOA'][s])  for s in STRATS],                      False,False),
            ("CF EDF OA",[fe(rc['cfOA'][s])    for s in STRATS],                      False,False),
            ("Revenus post-OA",[fe(rc['revPost'][s]) for s in STRATS],                False,False),
            ("Cash Flow Total",[fe(rc['cfTotal'][s]) for s in STRATS],                True, False),
            ("ΔCCF vs Défaut",[None]+[rc['delta'][s] for s in STRATS if s!='defaut'], True, True),
            ("% vs Défaut",  [None]+[rc['pct'][s]   for s in STRATS if s!='defaut'],  False,True),
        ]
        for i,(lbl,vals,bold,is_d) in enumerate(crow):
            bg=(248,250,252) if i%2==0 else (255,255,255); mp.set_fill_color(*bg)
            mp._f("B" if bold else "",7); mp.set_text_color(71,85,105)
            mp.cell(col_lc,5.5,lbl,fill=True,border=0)
            for v in vals:
                if is_d and v is None:
                    mp.set_text_color(100,116,139); mp._f("",7)
                    mp.cell(col_vc,5.5,"—",fill=True,border=0,align='C')
                elif is_d and isinstance(v,float):
                    tc2=(22,163,74) if v>=0 else (185,28,28)
                    mp.set_text_color(*tc2); mp._f("B",7)
                    txt=fe(v) if lbl.startswith("ΔCCF") else f"{'+'if v>=0 else ''}{v*100:.1f}%"
                    mp.cell(col_vc,5.5,txt,fill=True,border=0,align='C')
                else:
                    mp.set_text_color(15,23,42); mp._f("B" if bold else "",7)
                    mp.cell(col_vc,5.5,str(v),fill=True,border=0,align='C')
            mp.ln()
        # Bannière recommandée
        best_r=max(STRATS,key=lambda s:rc['pct'][s])
        best_p=rc['pct'][best_r]
        mp.ln(2); mp.set_fill_color(240,253,244)
        mp._f("B",9); mp.set_text_color(22,101,52)
        mp.cell(0,8,f"Stratégie Recommandée : {STRAT_LABELS_FR[best_r]}"
                    f"   —   {'+'if best_p>=0 else ''}{best_p*100:.1f}% vs Défaut",
                fill=True,ln=True)
        if best_r=='mix':
            mp._f("",8); mp.set_text_color(22,101,52); mp.set_fill_color(240,253,244)
            mp.cell(0,6,
                f"   Module à façon : {round(p['Pm_fac'])} Wc   |"
                f"   Part remplacement : {round(p['alpha_rev']*100)}%   |"
                f"   Nb modules : {round(p['n_rev']):,}",
                fill=True,ln=True)

    def _hyp_table():
        HYP=[("Réparation","Restitution de l'intégrité électrique du panneau — ne remet pas à zéro la dégradation naturelle des cellules."),
             ("Revamping","Remplacement par des panneaux à façon (format & caractéristiques similaires) — panneaux neufs."),
             ("Repowering","Remplacement complet (panneaux, structure, onduleur...) avec uplift de capacité. Arrêt plus long."),
             ("Mix Rép+Rev","Panneaux réparables → réparés ; non réparables → remplacés à façon pour revenir à la puissance nominale."),
             ("Défaut","Aucune intervention — dégradation accélérée (dn) appliquée chaque année.")]
        NOTES=["Post-OA : valorisation au tarif PPA / agrégateur. Réparation & Revamping : +N1 ans. Repowering : +N2 ans.",
               "Le scénario Défaut bénéficie également de N1 années post-OA (à dégradation accélérée).",
               "Les hypothèses financières (CAPEX, emprunt, fiscalité, O&M) sont détaillées dans le tableau de synthèse."]
        col_s2=32; col_d2=mp.w-16-col_s2
        mp._f("B",8); mp.set_fill_color(15,23,42); mp.set_text_color(255,255,255)
        mp.cell(col_s2,7,"Stratégie",fill=True,border=0)
        mp.cell(col_d2,7,"Définition",fill=True,border=0); mp.ln()
        for i,(strat,defn) in enumerate(HYP):
            bg=(248,250,252) if i%2==0 else (255,255,255); mp.set_fill_color(*bg)
            x0h,y0h=mp.l_margin,mp.get_y()
            mp.set_xy(x0h+col_s2,y0h); mp._f("",8); mp.set_text_color(71,85,105)
            mp.multi_cell(col_d2,5,defn,fill=True,border=0)
            y1h=mp.get_y(); rh=max(y1h-y0h,5)
            mp.set_xy(x0h,y0h); mp._f("B",8); mp.set_text_color(15,23,42)
            mp.set_fill_color(*bg); mp.cell(col_s2,rh,strat,fill=True,border=0)
            mp.set_y(y1h)
        mp.ln(3)
        mp._f("",7); mp.set_text_color(100,116,139)
        for note in NOTES:
            mp.set_x(mp.l_margin); mp.multi_cell(0,4,f"- {note}")

    # ── Diagram ──────────────────────────────────────────────────────────────────
    def _draw_diagram():
        N_=int(p['N']); N1_=int(p['N1']); N2_=int(p['N2'])
        d_=p['d_']; dn_=p['dn_']; u_=p['u_']; I2_=p['I2']
        tarif_=float(p['tarif']); PPA_=float(p['PPA'])
        Pc_=p['Pcentrale']

        # Years elapsed before decision (common "avant projet" curve)
        if d_ > 0 and 0 < I2_ < 1.0:
            Y_ = max(5, round(math.log(I2_) / math.log(1 - d_)))
        else:
            Y_ = 10

        # Timeline: 0 → Y_ (decision) → Y_+N_ (end OA) → Y_+N_+max(N1_,N2_)
        total = Y_ + N_ + max(N1_, N2_)

        PL=mp.l_margin; PR=mp.w-8
        lbl_w=18
        gx=PL+lbl_w; gw=PR-gx
        gy=mp.get_y()+4; gh=52

        def tx(t): return gx + t/total * gw
        p_top = (1 + u_) * 1.14
        p_bot = max(0.0, I2_ * (1 - dn_)**(N_ + N1_) * 0.80)
        def py(f): return gy + gh * (1 - (f - p_bot) / (p_top - p_bot))

        xY  = tx(Y_)              # decision point
        xYN = tx(Y_ + N_)         # end of OA
        xYN1= tx(Y_ + N_ + N1_)   # end PPA — Déf/Rép/Rev/Mix
        xYN2= tx(Y_ + N_ + N2_)   # end PPA — Repowering

        yNom = py(1.0)
        yI2  = py(I2_)

        # Graph background
        mp.set_fill_color(250,251,255); mp.set_draw_color(200,210,225)
        mp.set_line_width(0.3); mp.rect(gx,gy,gw,gh,'FD')

        # Shaded "avant projet" zone
        mp.set_fill_color(238,242,250)
        mp.rect(gx, gy, xY-gx, gh, 'F')

        # Zone labels above graph
        zl_y = gy - 4.5
        mp._f("",5); mp.set_text_color(100,116,139)
        mp.set_xy((gx+xY)/2-14, zl_y); mp.cell(28,3.5,"Avant projet",align='C')
        mp.set_xy((xY+xYN)/2-14, zl_y); mp.cell(28,3.5,"OA restantes",align='C')
        mp.set_xy(xYN+2, zl_y); mp.cell(50,3.5,"Post-OA (PPA)")

        # Vertical dashed separators at decision and end-OA
        mp.set_draw_color(160,170,190); mp.set_line_width(0.25)
        mp.set_dash_pattern(dash=1.5,gap=1)
        mp.line(xY, gy, xY, gy+gh)
        mp.line(xYN, gy, xYN, gy+gh)
        mp.set_dash_pattern()

        # Nominal reference line (blue dashed)
        mp.set_draw_color(96,165,250); mp.set_line_width(0.5)
        mp.set_dash_pattern(dash=3,gap=1.5)
        mp.line(gx,yNom,gx+gw,yNom)
        mp.set_dash_pattern()
        mp._f("",5.5); mp.set_text_color(96,165,250)
        mp.set_xy(gx+2, yNom-4.5)
        mp.cell(50,4,f"Puissance nominale  {round(Pc_)} kWc")

        # Helper: draw label with white background so it floats above lines
        def lbl(x, y, txt, col_rgb):
            tw = mp.get_string_width(txt)
            mp.set_fill_color(255,255,255)
            mp.rect(x-0.8, y-0.5, tw+3, 4.2, 'F')
            mp._f("",5.5); mp.set_text_color(*col_rgb)
            mp.set_xy(x, y); mp.cell(tw+2, 3.8, txt)

        # ── Common "avant projet" curve (black) — Pc at t=0 → I2 at t=Y ──
        mp.set_draw_color(30,41,59); mp.set_line_width(0.6)
        mp.line(gx, py(1.0), xY, yI2)
        lbl(gx+3, gy+2, f"Avant projet  -{d_*100:.2f}%/an", (30,41,59))

        # I2 annotation at decision point
        mp._f("",5.5); mp.set_text_color(100,116,139)
        mp.set_xy(xY+1.5, yI2+0.5)
        mp.cell(22,3.5,f"I2={I2_*100:.1f}%")

        # ── Post-decision scenario lines (drawn first, labels on top) ──

        pw_def_end = I2_ * (1-dn_)**(N_+N1_)
        pw_rep_end = I2_ * (1-d_)**(N_+N1_)
        pw_rev_end = 1.0 * (1-d_)**(N_+N1_)
        pw_rpw_end = (1+u_) * (1-d_)**N2_
        y_rev = py(1.0)
        y_rpw = py(1+u_)

        # 1. Défaut (dark gray, dashed)
        mp.set_draw_color(55,65,81); mp.set_line_width(0.5)
        mp.set_dash_pattern(dash=2.5,gap=1.5)
        mp.line(xY, yI2, xYN1, py(pw_def_end))
        mp.set_dash_pattern()

        # 2. Réparation (green, solid)
        mp.set_draw_color(22,101,52); mp.set_line_width(0.5)
        mp.line(xY, yI2, xYN1, py(pw_rep_end))

        # 3. Revamping/Mix (amber) — arrow shaft touches y_rev exactly
        mp.set_draw_color(180,120,0); mp.set_line_width(0.4)
        mp.line(xY-1.0, yI2, xY-1.0, y_rev)
        ah=1.2
        mp.line(xY-1.0, y_rev, xY-1.0-ah, y_rev+ah)
        mp.line(xY-1.0, y_rev, xY-1.0+ah, y_rev+ah)
        mp.set_line_width(0.5)
        mp.line(xY, y_rev, xYN1, py(pw_rev_end))

        # 4. Repowering (red) — arrow shaft touches y_rpw exactly
        mp.set_draw_color(185,28,28); mp.set_line_width(0.4)
        mp.line(xY+1.0, yI2, xY+1.0, y_rpw)
        ah=1.2
        mp.line(xY+1.0, y_rpw, xY+1.0-ah, y_rpw+ah)
        mp.line(xY+1.0, y_rpw, xY+1.0+ah, y_rpw+ah)
        mp.set_line_width(0.5)
        mp.line(xY, y_rpw, xYN2, py(pw_rpw_end))

        # +u% annotation on repowering arrow (right of shaft)
        mp._f("B",6); mp.set_text_color(185,28,28)
        mp.set_xy(xY+2.5, (yI2+y_rpw)/2-2)
        mp.cell(12,4,f"+{u_*100:.0f}%")

        # ── Labels: all left-aligned at same x = mid of post-decision zone ──
        # x_lbl = midpoint between decision and end of N1 PPA
        x_lbl = (xY + xYN1) / 2
        t_mid = (N_ + N1_) / 2.0          # years after decision at x_lbl

        # Y position of each line at x_lbl
        y_rpw_at = py((1+u_) * (1-d_)**t_mid)
        y_rev_at = py(1.0    * (1-d_)**t_mid)
        y_rep_at = py(I2_    * (1-d_)**t_mid)
        y_def_at = py(I2_    * (1-dn_)**t_mid)

        # Repowering & Rev/Mix: label ABOVE line  |  Réparation & Défaut: label BELOW
        lbl(x_lbl, y_rpw_at - 5.5, f"Repowering  -{d_*100:.2f}%/an",        (185,28,28))
        lbl(x_lbl, y_rev_at - 5.5, f"Revamping / Rép+Mix  -{d_*100:.2f}%/an",(180,120,0))
        lbl(x_lbl, y_rep_at + 1.0, f"Réparation  -{d_*100:.2f}%/an",        (22,101,52))
        lbl(x_lbl, y_def_at + 1.0, f"Défaut  -{dn_*100:.1f}%/an",           (55,65,81))

        # Y-axis labels
        mp._f("",6); mp.set_text_color(71,85,105)
        for i,ll in enumerate(["Puissance","des panneaux","de la","centrale"]):
            mp.set_xy(PL, gy+gh/2-9+i*4.2); mp.cell(lbl_w-1,4,ll,align='C')

        # ── Period bars ──
        bar_y=gy+gh+3; bh=6.5; gap_b=2.0

        def bar(x,w,rgb,txt,y):
            mp.set_fill_color(*rgb); mp.rect(x,y,w,bh,'F')
            mp._f("B",5.5); mp.set_text_color(255,255,255)
            mp.set_xy(x+1,y+1); mp.cell(w-2,bh-2,txt,align='C')

        # Row label offset
        lbl_off = bar_y - 3.5

        # Row 1 — Déf / Rép / Rev / Mix
        mp._f("",5); mp.set_text_color(100,116,139)
        mp.set_xy(gx+1, lbl_off); mp.cell(50,3.5,"Déf / Rép / Rev / Mix")
        bar(gx,    xYN-gx,      (34,197,94),
            f"EDF OA — {N_} ans restantes — {tarif_:.4f} €/kWh", bar_y)
        bar(xYN,   xYN1-xYN,   (202,138,4),
            f"PPA — {N1_} ans — {PPA_:.3f} €/kWh", bar_y)

        # Row 2 — Repowering
        bar_y2=bar_y+bh+gap_b
        mp._f("",5); mp.set_text_color(100,116,139)
        mp.set_xy(gx+1, lbl_off+bh+gap_b); mp.cell(25,3.5,"Repowering")
        bar(gx,    xYN-gx,      (34,197,94),
            f"EDF OA — {N_} ans restantes — {tarif_:.4f} €/kWh", bar_y2)
        bar(xYN,   xYN2-xYN,   (202,138,4),
            f"PPA — {N2_} ans — {PPA_:.3f} €/kWh", bar_y2)

        # X-axis year labels
        yr_y = bar_y2+bh+1.5
        mp._f("",5.5); mp.set_text_color(30,41,59)
        mp.set_xy(gx,     yr_y); mp.cell(xY-gx,    4, f"~{Y_} ans",  align='C')
        mp.set_xy(xY,     yr_y); mp.cell(xYN-xY,   4, f"{N_} ans",   align='C')
        mp.set_xy(xYN,    yr_y); mp.cell(xYN1-xYN, 4, f"+{N1_} ans", align='C')
        if xYN2 > xYN1+5:
            mp.set_xy(xYN, yr_y+4); mp.cell(xYN2-xYN, 4, f"+{N2_} ans (Repow.)", align='C')

        mp.set_line_width(0.2)
        mp.set_y(yr_y+9)

    # ── PAGE 1 : Paramètres + Diagramme ─────────────────────────────────────────
    mp.add_page('P')
    mp._f("B",14); mp.set_text_color(15,23,42)
    mp.cell(0,8,"Rapport Financier - Scénarios de Rénovation PV",ln=True); mp.ln(2)
    _section("Paramètres du scénario")
    _params_table(); mp.ln(3)
    _section("Schéma — Évolution de la puissance par scénario")
    _draw_diagram(); mp.ln(2)

    # ── PAGE 2 : Stratégie Rénovation + Synthèse Financière + Hypothèses ────────
    mp.add_page('P')
    mp._f("B",12); mp.set_text_color(15,23,42)
    mp.cell(0,7,"Stratégie de Rénovation — Comparatif Cash Flow net de CAPEX",ln=True)
    mp.set_draw_color(203,213,225); mp.line(8,mp.get_y(),mp.w-8,mp.get_y()); mp.ln(2)
    _strat_ren_table(); mp.ln(4)
    _section("Synthèse Financière")
    _syn_table(); mp.ln(4)
    _section("Hypothèses & Définitions")
    _hyp_table()

    # ── PAGES 3+ : Tableaux financiers paysage ───────────────────────────────────
    for s in STRATS:
        sc=results[s]; rows=sc['rows']; total_yrs=sc['total_yrs']
        N_oa=int(p['N']); color=STRAT_COLORS_RGB[s]
        mp.add_page('L')
        mp._f("B",12); mp.set_text_color(*color)
        mp.cell(0,7,f"Scénario : {LABELS[s]}",ln=True)
        mp._f("",8); mp.set_text_color(100,116,139)
        roe_s='N/A' if sc['ROE'] is None else f"{sc['ROE']*100:.1f}%"
        dscr_s='N/A' if sc['dscr_avg'] is None else f"{sc['dscr_avg']:.2f}"
        mp.cell(0,5,
            f"CAPEX : {fe(sc['CAPEX'])}   FP : {fe(sc['equity'])}   "
            f"Dette : {fe(sc['debt'])}   Durée : {total_yrs} ans   "
            f"ROE incr. : {roe_s}   DSCR moy. : {dscr_s}   "
            f"Delta Tresor. vs Défaut : {fe(sc['cum_incr'])}",ln=True)
        mp.ln(1)
        usable=mp.w-16; cl=52; cy=(usable-cl)/total_yrs
        mp._f("B",6); mp.set_text_color(255,255,255); mp.set_fill_color(*color)
        mp.cell(cl,6,"Indicateur",fill=True,border=0)
        for r in rows:
            bg2=(30,58,95) if r['k']<=N_oa else (55,65,81); mp.set_fill_color(*bg2)
            mp.cell(cy,6,f"An {r['k']}",fill=True,border=0,align='C')
        mp.ln()

        def mrow(label,fn,head=False,bold=False):
            if head:
                mp.set_fill_color(*color); mp._f("B",6); mp.set_text_color(255,255,255)
                mp.cell(cl,5,label,fill=True,border=0)
                mp.cell(cy*total_yrs,5,'',fill=True,border=0); mp.ln(); return
            mp.set_fill_color(248,250,252); mp._f("B" if bold else "",6); mp.set_text_color(71,85,105)
            mp.cell(cl,4.8,label,fill=True,border=0)
            mp._f("B" if bold else "",6)
            for r in rows:
                v=fn(r)
                if isinstance(v,float):
                    tc=(22,163,74) if v>0 else (185,28,28) if v<0 else (100,116,139)
                    mp.set_text_color(*tc); v=fe(v)
                else: mp.set_text_color(15,23,42)
                mp.cell(cy,4.8,str(v),fill=True,border=0,align='R')
            mp.ln()

        if sc['debt']>0:
            mrow("── Échéancier emprunt",None,head=True)
            mrow("Capital remboursé",lambda r:r['loan']['principal'])
            mrow("Intérêts",         lambda r:r['loan']['interest'])
            mrow("Total annuité",    lambda r:r['loan']['annuity'],bold=True)
            mrow("Solde restant",    lambda r:r['loan']['balance'])
        mrow("── Compte de résultat",None,head=True)
        mrow("Tarif (€/kWh)",       lambda r:f"{r['tarif_k']:.4f}")
        mrow("Production (MWh)",    lambda r:f"{r['prod']/1000:.0f}")
        mrow("Chiffre d'affaires",  lambda r:r['CA'],bold=True)
        mrow("  Maintenance",       lambda r:r['maint'])
        mrow("  OPEX",              lambda r:r['opex'])
        mrow("  Assurance",         lambda r:r['ins'])
        mrow("  Loyer",             lambda r:r['rent'])
        mrow("EBITDA",              lambda r:r['EBITDA'],bold=True)
        mrow("  Amortissement",     lambda r:r['amort'])
        mrow("EBIT",                lambda r:r['EBIT'],bold=True)
        mrow("  Intérêts emprunt",  lambda r:-r['int_exp'])
        mrow("  Intérêts tréso.",   lambda r:r['int_inc'])
        mrow("Résultat avant impôt",lambda r:r['EBT'],bold=True)
        mrow("  Impôt",             lambda r:-r['tax'])
        mrow("Résultat net",        lambda r:r['net'],bold=True)
        mrow("── Cash Flow",        None,head=True)
        mrow("CF opérationnel",     lambda r:r['op_cf'])
        mrow("Rembt. dette",        lambda r:-r['repay'])
        mrow("Trésorerie annuelle", lambda r:r['ann_treas'],bold=True)
        mrow("Trésorerie cumulée",  lambda r:r['cum_treas'],bold=True)
        mrow("Delta Tréso. vs Défaut",lambda r:r['cum_incr'],bold=True)
        mrow("DSCR incrémental",    lambda r:f"{r['dscr']:.2f}" if r['dscr'] is not None else '—',bold=True)

    return bytes(mp.output())

# ── Header ────────────────────────────────────────────────────────────────────
st.markdown("""
<div style="background:#1e293b;padding:14px 24px;border-radius:10px;
            margin-bottom:20px;display:flex;align-items:center;gap:16px">
  <span style="font-size:22px;font-weight:900;letter-spacing:-.5px">
    <span style="color:#fff">DOT</span><span style="color:#f59e0b">Sun</span>
  </span>
  <span style="font-size:14px;color:#94a3b8">
    Tableaux Financiers — Scénarios de Rénovation de Parc PV
  </span>
</div>""", unsafe_allow_html=True)

# ── Sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown('<div style="display:inline-block;background:#1e293b;border-radius:6px;'
                'padding:4px 12px;margin-bottom:10px"><span style="font-size:24px;font-weight:900">'
                '<span style="color:#fff">DOT</span><span style="color:#f59e0b">Sun</span>'
                '</span></div>', unsafe_allow_html=True)
    st.markdown("### ⚙️ Paramètres")
    c1,c2 = st.columns(2)
    if c1.button("📋 Scénario 1", use_container_width=True): init_state("s1"); st.rerun()
    if c2.button("📋 Scénario 2", use_container_width=True): init_state("s2"); st.rerun()

    st.markdown("#### Centrale solaire")
    st.number_input("n — Panneaux", min_value=1.0, step=100.0, format="%.0f", key="fp_n")
    st.number_input("Pm — Puissance/panneau (Wc)", min_value=1.0, step=5.0, format="%.0f", key="fp_Pm")
    st.number_input("H — Productible (kWh/kWc/an)", min_value=500.0, max_value=2500.0, step=10.0, format="%.0f", key="fp_H")
    st.number_input("Y — Âge (ans)", min_value=0.0, max_value=30.0, step=1.0, key="fp_Y")

    st.markdown("#### Dégradation")
    st.number_input("d — Normale (%/an)", min_value=0.0, max_value=5.0, step=0.05, format="%.2f", key="fp_d")
    st.number_input("dn — Accélérée Défaut (%/an)", min_value=0.0, max_value=30.0, step=0.5, format="%.1f", key="fp_dn")
    st.number_input(
        "Eff-IV — Efficacité réelle mesurée (%)",
        min_value=0.0, max_value=100.0, step=0.1, format="%.1f",
        key="fp_eff_iv",
        help="Efficacité réelle mesurée par courbe IV sur site. Laisser à 0 pour utiliser la valeur calculée (d × Y).",
    )
    _d_disp  = st.session_state.get("fp_d", 0.40)
    _Y_disp  = st.session_state.get("fp_Y", 10.0)
    _iv_disp = st.session_state.get("fp_eff_iv", 0.0)
    _i2_calc = (1 - _d_disp / 100) ** _Y_disp * 100
    if _iv_disp > 0:
        st.caption(f"▶ Efficacité utilisée : **{_iv_disp:.1f}%** *(mesure IV)*")
    else:
        st.caption(f"▶ Efficacité calculée : **{_i2_calc:.1f}%** *(d={_d_disp:.2f}%, Y={_Y_disp:.0f} ans)*")

    st.markdown("#### Contrat & Revenus")
    st.number_input("N — Années restantes OA", min_value=1.0, max_value=20.0, step=1.0, key="fp_N")
    st.number_input("p — Tarif EDF OA (€/kWh)", min_value=0.0, max_value=1.5, step=0.001, format="%.4f", key="fp_tarif")
    st.number_input("N1 — Extension Rép/Rev (ans)", min_value=0.0, max_value=20.0, step=1.0, key="fp_N1")
    st.number_input("N2 — Extension Repowering (ans)", min_value=0.0, max_value=30.0, step=1.0, key="fp_N2")
    st.number_input("PPA — Tarif post-OA (€/kWh)", min_value=0.0, max_value=0.5, step=0.005, format="%.3f", key="fp_PPA")

    st.markdown("#### Coûts d'intervention")
    st.number_input("Crep (€/panneau)", min_value=0.0, step=1.0, key="fp_Crep")
    st.number_input("Cdm (€/panneau)", min_value=0.0, step=1.0, key="fp_Cdm")
    st.number_input("Cde (€/panneau)", min_value=0.0, step=1.0, key="fp_Cde")
    st.number_input("Cfac (€/Wc)", min_value=0.0, max_value=2.0, step=0.01, format="%.2f", key="fp_Cfac")
    st.number_input("Crev (€/Wc)", min_value=0.0, max_value=3.0, step=0.01, format="%.2f", key="fp_Crev")

    st.markdown("#### Opérationnel")
    st.number_input("Down_rep (mois)", min_value=0.0, max_value=12.0, step=0.5, format="%.1f", key="fp_Down_rep")
    st.number_input("Down_repow (mois)", min_value=0.0, max_value=24.0, step=1.0, key="fp_Down_repow")
    st.number_input("u — Uplift repowering (%)", min_value=0.0, max_value=50.0, step=1.0, key="fp_u")

    st.markdown("#### Mix Réparation + Revamping")
    _ap = st.slider("α_rep — Part réparable (%)", 0, 100, key="fp_alpha_pct")
    st.caption(f"Réparation : **{_ap}%** — Revamping : **{100-_ap}%**")

    st.markdown("#### Hypothèses financières")
    st.number_input("Fonds propres (% CAPEX)", min_value=0.0, max_value=100.0, step=1.0, key="fp_equity_pct")
    st.number_input("Durée emprunt (ans)", min_value=1.0, max_value=25.0, step=1.0, key="fp_loan_dur")
    st.number_input("Taux d'intérêt (%)", min_value=0.0, max_value=20.0, step=0.25, key="fp_int_rate")
    st.number_input("Inflation (%)", min_value=0.0, max_value=10.0, step=0.25, key="fp_infl_rate")
    st.number_input("Imposition (%)", min_value=0.0, max_value=50.0, step=1.0, key="fp_tax_rate")
    st.number_input("Maintenance (% CA)", min_value=0.0, max_value=20.0, step=0.5, key="fp_maint_pct")
    st.number_input("OPEX (% CA)", min_value=0.0, max_value=20.0, step=0.5, key="fp_opex_pct")
    st.number_input("Assurance (% CA)", min_value=0.0, max_value=10.0, step=0.25, key="fp_ins_pct")
    st.number_input("Loyer annuel (€)", min_value=0.0, step=1000.0, format="%.0f", key="fp_rent")
    st.number_input("Amortissement (ans)", min_value=1.0, max_value=30.0, step=1.0, key="fp_amort_dur")
    st.number_input("Intérêt trésorerie (%)", min_value=0.0, max_value=10.0, step=0.25, key="fp_treas_rate")

# ── Compute ───────────────────────────────────────────────────────────────────
p       = get_params()
fin     = get_fin()
results = run_all(p, fin)
rc      = compute_comparateur(p)

# KPI bar
k1,k2,k3,k4 = st.columns(4)
k1.metric("Pcentrale", f"{p['Pcentrale']:,.0f} kWc")
k2.metric("Efficacité I₂", f"{p['I2']*100:.1f}%", f"après {int(p['Y'])} ans")
k3.metric("Panneau à façon", f"{p['Pm_fac']:.0f} Wc")
k4.metric("Gap kWc", f"{p['gap_kWc']:.0f} kWc")
st.markdown("<div style='margin-bottom:8px'></div>", unsafe_allow_html=True)

# ── Tabs ──────────────────────────────────────────────────────────────────────
tab_syn, tab_def, tab_rpw, tab_rep, tab_rev, tab_mix, tab_ren = st.tabs(
    ["📊 Synthèse", "Défaut", "Repowering", "Réparation", "Revamping", "Mix Rép+Rev",
     "🏗️ Stratégie Rénovation"])

with tab_syn:
    st.markdown("#### Tableau de Synthèse — Tous Scénarios")
    st.markdown(render_synthesis(results), unsafe_allow_html=True)

for tab, s in zip([tab_def, tab_rpw, tab_rep, tab_rev, tab_mix], STRATS):
    with tab:
        sc = results[s]
        c1,c2,c3,c4,c5 = st.columns(5)
        c1.metric("CAPEX", fe(sc['CAPEX']))
        c2.metric("Fonds propres", fe(sc['equity']))
        c3.metric("Dette", fe(sc['debt']))
        roe_disp = 'N/A' if sc['ROE'] is None else fp(sc['ROE'])
        c4.metric("ROE incrémental", roe_disp)
        dscr_disp = 'N/A' if sc['dscr_avg'] is None else f"{sc['dscr_avg']:.2f}"
        c5.metric("DSCR moyen", dscr_disp)
        st.markdown(render_scenario_table(s, sc, int(p['N'])), unsafe_allow_html=True)

with tab_ren:
    st.markdown("#### Stratégie Rénovation — Comparatif Cash Flow (hors hypothèses financières)")
    st.caption("Ce tableau reprend la logique du Comparateur de Stratégies : revenus bruts cumulés et Cash Flow net de CAPEX, sans modélisation d'emprunt ni de fiscalité.")
    st.markdown(render_comparateur_table(p, rc), unsafe_allow_html=True)

# ── PDF download ──────────────────────────────────────────────────────────────
from datetime import date as _dt
st.markdown("---")
try:
    pdf_bytes = generate_pdf(p, fin, results, rc)
    st.download_button(
        label="📄 Télécharger le rapport PDF complet",
        data=pdf_bytes,
        file_name=f"DOTSun_Tableaux_Financiers_{_dt.today().strftime('%Y%m%d')}.pdf",
        mime="application/pdf",
    )
except Exception as e:
    st.warning(f"PDF indisponible : {e}")

with st.expander("📋 Hypothèses & Définitions"):
    st.markdown("""
| Stratégie | Définition |
|---|---|
| **Réparation** | Restitution de l'intégrité électrique du panneau — ne remet pas à zéro la dégradation naturelle des cellules. |
| **Revamping** | Remplacement par des panneaux «à façon» (format & caractéristiques similaires) — panneaux neufs. |
| **Repowering** | Remplacement complet (panneaux, structure, onduleur…) avec uplift de capacité. Arrêt plus long. |
| **Mix Rép+Rev** | Panneaux réparables → réparés ; non réparables → remplacés à façon pour revenir à la puissance nominale. |
| **Défaut** | Aucune intervention — dégradation accélérée (dn) appliquée chaque année. |

- Post-OA : valorisation au tarif PPA / agrégateur. Réparation & Revamping : +N1 ans. Repowering : +N2 ans.
- Le scénario Défaut bénéficie également de N1 années post-OA (à dégradation accélérée).
- Les hypothèses financières (CAPEX, emprunt, fiscalité, O&M) sont détaillées dans le tableau de synthèse.
""")
