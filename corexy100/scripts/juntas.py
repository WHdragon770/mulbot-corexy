# Registro de pecas impressas novas + juntas com fixadores impressos (Mulbot: rosca ISO, porca-barril)
import sys, os, numpy as np, manifold3d as mf
sys.path.insert(0, "/home/lucas/mulbot/scripts"); sys.path.insert(0, "/home/lucas/corexy100/scripts")
from base import cil, caixa, salva, tr, R4, DER
import fixadores as fx
FXD = f"{DER}/fixadores"; os.makedirs(FXD, exist_ok=True)

PEC = {}      # nome -> dict(m, cor, q)   (q = quadro: mundo / portico / carro / mesa)
FIX = []      # (nome, stl, T no quadro, cor, q)
def reg(nome, m, cor, q="mundo"): PEC[nome] = dict(m=m, cor=cor, q=q); return m
def sub(nome, m): PEC[nome]["m"] = PEC[nome]["m"] - m
FUROS = []    # (p0, p1, r) de todo furo de junta: cabos.py deixa um anel de parede em volta ao ocar o quadro
def cilf(p0, p1, r): FUROS.append((np.array(p0, float), np.array(p1, float), r)); return cil(p0, p1, r)
GOTAS = {}    # peca -> [(p0, p1, r)] furos de junta: semsup.aplica_gotas() poe o bico de 45 graus conforme a impressao da peca
def subf(nome, p0, p1, r):
    sub(nome, cilf(p0, p1, r)); GOTAS.setdefault(nome, []).append((np.array(p0, float), np.array(p1, float), r))

BAR = {10: 14.0, 6: 9.0}                      # diametro da porca-barril
CAB = {10: (16.0, 6.0), 6: (10.5, 4.0)}       # cabeca do parafuso botao (diametro, altura)
def _stl(nome, fn_gera):
    fn = f"{FXD}/{nome}.stl"
    if not os.path.exists(fn): fx.salvar(fn_gera(), fn)
    return fn
def stl_parafuso(d, L): return _stl(f"parafuso_M{d}x{L}", lambda: fx.parafuso_botao(d, L))
def stl_barril(d, comp): return _stl(f"barril_M{d}_D{BAR[d]:.0f}x{comp:.0f}", lambda: fx.barril(d, BAR[d], comp))
def stl_porca(d): return _stl(f"porca_M{d}", lambda: fx.porca(d))
def _base(u, ref):
    u = np.array(u, float); u /= np.linalg.norm(u)
    x = np.array(ref, float); x = x - (x @ u) * u
    if np.linalg.norm(x) < 1e-6: x = np.cross(u, [0, 0, 1.0]) if abs(u[2]) < 0.9 else np.cross(u, [1.0, 0, 0])
    x /= np.linalg.norm(x); return x, np.cross(u, x), u
def L5(v): return int(np.ceil(v / 5.0) * 5)

def junta_barril(cab, nut, P, u, L, bdir, blen, d=10, cb=0.0, q="mundo", nome=None, atravessa=()):
    """parafuso botao M{d}xL: cabeca apoiada em P (na peca 'cab'), entra no sentido u e rosca numa porca-barril
    atravessada na peca 'nut' (eixo bdir, comprimento blen), 6 mm antes da ponta. cb: rebaixo da cabeca (P -> superficie)"""
    P = np.array(P, float); u = np.array(u, float) / np.linalg.norm(u); bd = np.array(bdir, float) / np.linalg.norm(bdir)
    furo = fx.TAB[d]["furo"]
    if cb > 0: subf(cab, P - u * (cb + 1), P + u * 0.01, CAB[d][0] / 2 + 0.6)
    subf(cab, P - u * 1, P + u * (L + 1), furo / 2)
    for n in atravessa: subf(n, P - u * 1, P + u * (L + 1), furo / 2)
    subf(nut, P - u * 1, P + u * (L + 3), furo / 2)
    C = P + u * (L - 6)
    subf(nut, C - bd * (blen / 2 + 1), C + bd * (blen / 2 + 1), BAR[d] / 2 + 0.2)
    x, y, z = _base(u, bd)
    nome = nome or f"M{d}x{L}_{cab}_{nut}_{len(FIX)}"
    FIX.append((nome, stl_parafuso(d, L), R4(np.column_stack([x, y, z]), P), "azul", q))
    FIX.append(("barril_" + nome, stl_barril(d, blen), R4(np.column_stack([bd, np.cross(u, bd), u]), C), "azul", q))
def junta_passante(pecas, P, u, grip, d=10, q="mundo", nome=None, ref=(1, 0, 0)):
    """parafuso botao atravessando 'pecas' (aperto = grip) com porca sextavada impressa do outro lado"""
    P = np.array(P, float); u = np.array(u, float) / np.linalg.norm(u)
    furo = fx.TAB[d]["furo"]; hp = fx.TAB[d]["porca"]
    for n in pecas: subf(n, P - u * 1, P + u * (grip + 1), furo / 2)
    L = L5(grip + hp + 1.0)
    x, y, z = _base(u, ref)
    nome = nome or f"M{d}x{L}_{'_'.join(pecas)}_{len(FIX)}"
    FIX.append((nome, stl_parafuso(d, L), R4(np.column_stack([x, y, z]), P), "azul", q))
    FIX.append(("porca_" + nome, stl_porca(d), R4(np.column_stack([x, y, z]), P + u * grip), "azul", q))

# ---------- divisao com emenda sobreposta (meia-madeira)
def _semi(ax, lo, hi):
    a = [-5000.0] * 3; b = [5000.0] * 3; a[ax] = lo; b[ax] = hi; return caixa(a, b)
EMENDAS = []  # (nome, nA, nB, ax, p, Lp, t, ct): cabos.py fecha a cavidade na face da emenda (septo) -> o anel do parafuso fica preso nos 2 lados
def corta(nome, nA, nB, ax, p):
    """divide PEC[nome] no plano ax = p (sem sobreposicao): nA fica com ax < p"""
    m = PEC[nome]["m"]; c = PEC[nome]["cor"]; q = PEC[nome]["q"]
    del PEC[nome]; reg(nA, m ^ _semi(ax, -5000, p), c, q); reg(nB, m ^ _semi(ax, p, 5000), c, q)
    g = GOTAS.pop(nome, []); GOTAS[nA] = list(g); GOTAS[nB] = list(g)
def emenda(nome, nA, nB, ax, p, Lp, t, ct, parafusos=2, d=10, ref=(1, 0, 0)):
    """divide PEC[nome] no plano ax=p com sobreposicao de comprimento Lp; na sobreposicao A fica com t<ct e B com t>=ct.
    Parafusos passantes ao longo de t nas posicoes p +- Lp/4"""
    m = PEC[nome]["m"]; c = PEC[nome]["cor"]; q = PEC[nome]["q"]
    EMENDAS.append((nome, nA, nB, ax, p, Lp, t, ct))
    lap = _semi(ax, p - Lp / 2, p + Lp / 2)
    A = m ^ (_semi(ax, -5000, p - Lp / 2) + (lap ^ _semi(t, -5000, ct)))
    B = m ^ (_semi(ax, p + Lp / 2, 5000) + (lap ^ _semi(t, ct, 5000)))
    del PEC[nome]; reg(nA, A, c, q); reg(nB, B, c, q)
    g = GOTAS.pop(nome, []); GOTAS[nA] = list(g); GOTAS[nB] = list(g)     # os 2 pedacos herdam os furos (cada um com a sua impressao)
    b = m.bounding_box(); lo = np.array(b[:3]); hi = np.array(b[3:]); mid = (lo + hi) / 2
    other = [i for i in range(3) if i not in (ax, t)][0]
    ps = [p - Lp / 4, p + Lp / 4] if parafusos == 2 else [p]
    for s in ps:
        P = mid.copy(); P[ax] = s; P[t] = lo[t]; u = np.zeros(3); u[t] = 1
        junta_passante([nA, nB], P, u, hi[t] - lo[t], d=d, q=q, ref=ref)
