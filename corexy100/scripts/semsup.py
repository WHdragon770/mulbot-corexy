# Desenho sem suporte (FDM, tudo a 45 graus ou ponte curta): depende do lado que fica pra cima NA IMPRESSAO de cada peca.
# CIMA[peca] = vetor do mundo (quadro da peca na montagem) que aponta pra cima na mesa da Kobra X (placas/impressao_rot.json).
# gota: furo deitado vira gota (bico de 45 graus em cima); quilha: idem pra baixo (anel de parede atravessando cavidade);
# telhado: cavidade em caixa com teto em 2 aguas a 45 graus deixando so uma ponte curta no meio.
import os, json, numpy as np, manifold3d as mf
import shapely.geometry as sg
from base import cil, caixa

PONTE = 9.0                        # vao de ponte aceito (mm): o perfil da Kobra X no Slicer Next poe suporte em ponte > 10 (max_bridge_length)
_J = "/home/lucas/corexy100/scripts/placas/impressao_rot.json"     # rotacao montagem -> impressao (a mesma que o orienta.py usa)
CIMA = {k: np.linalg.inv(np.array(v, float)) @ [0, 0, 1.0] for k, v in json.load(open(_J)).items()
        if not k.startswith(("DL1-", "fusoZ", "porcaZ", "presilha"))}
LIGADO = os.environ.get("SEMSUP", "1") == "1"

def cima(peca):
    """vetor 'pra cima' da peca (None = desligado ou peca sem orientacao fixa)"""
    if not LIGADO: return None
    return CIMA.get(peca)

def espelha(v): return None if v is None else np.array([-v[0], v[1], v[2]])

def _frame(a, v):
    w = np.cross(a, v); return w / np.linalg.norm(w)

def gota(p0, p1, r, up=None, n=48, ap=None):
    """cilindro p0->p1 de raio r; se o eixo fica deitado na impressao, ganha o bico de 45 graus pra cima (teardrop).
    ap: distancia do eixo ate a ponta (padrao r*raiz(2) = 45 graus; menor que isso nao vale, maior = lados mais em pe)"""
    c = cil(p0, p1, r, n)
    if up is None: return c
    p0 = np.array(p0, float); p1 = np.array(p1, float); a = p1 - p0; L = np.linalg.norm(a); a /= L
    up = np.array(up, float); v = up - (up @ a) * a; nv = np.linalg.norm(v)
    if nv < 0.7: return c                                     # eixo em pe: furo redondo imprime sem problema
    v /= nv; w = _frame(a, v)
    ap = r * np.sqrt(2) if ap is None else max(ap, r * np.sqrt(2) * 0.9999)
    if ap < r * np.sqrt(2): ap = r * np.sqrt(2)
    cf = r / ap; sf = np.sqrt(1 - cf * cf)                     # pontos de tangencia
    tri = mf.CrossSection([[(r * sf, r * cf), (0.0, ap), (-r * sf, r * cf)]])   # (w, v), CCW
    pr = tri.extrude(L).transform(np.column_stack([w, v, a, p0]).tolist())
    return c + pr

def quilha(p0, p1, r, up=None, n=48, ap=None):
    """cilindro com bico de 45 graus pra BAIXO (material atravessando um vazio: comeca numa ponte fina e abre a 45)"""
    return gota(p0, p1, r, None if up is None else -np.array(up, float), n, ap)

def telhado(lo, hi, up=None, ponte=PONTE, alto=None):
    """caixa (cavidade) com o teto em 45 graus nas 2 aguas, sobrando ponte <= 'ponte' no meio. up = pra cima na impressao.
    alto = ponto (mundo): teto de 1 agua so, com a ponte encostada na parede do lado desse ponto (deixa um lado da cavidade alto)"""
    a_, b_ = np.array(lo, float), np.array(hi, float); lo, hi = np.minimum(a_, b_), np.maximum(a_, b_)
    box = caixa(lo, hi)
    if up is None: return box
    up = np.array(up, float); k = int(np.argmax(np.abs(up))); sg_ = np.sign(up[k])
    if abs(up[k]) < 0.99: return box                          # orientacao obliqua: nao trata
    hz = [i for i in range(3) if i != k]
    ext = hi - lo
    iw = min(hz, key=lambda i: ext[i]); il = [i for i in hz if i != iw][0]
    span = ext[iw]
    if span <= ponte: return box
    # secao no plano (w, h) com h = altura na impressao (cresce pra cima)
    h0, h1 = sorted((sg_ * lo[k], sg_ * hi[k])); w0, w1 = lo[iw], hi[iw]; cw = (w0 + w1) / 2
    drop = (span - ponte) / 2
    if alto is None:
        hb = min(h0, h1 - drop) - 1
        pol = sg.Polygon([(w0, hb), (w1, hb), (w1, h1 - drop), (cw + ponte / 2, h1), (cw - ponte / 2, h1), (w0, h1 - drop)])
    else:                                                      # 1 agua: ponte junto da parede do lado de 'alto'
        d2 = span - ponte; hb = min(h0, h1 - d2) - 1
        if alto[iw] < cw: pol = sg.Polygon([(w0, hb), (w1, hb), (w1, h1 - d2), (w0 + ponte, h1), (w0, h1)])
        else: pol = sg.Polygon([(w0, hb), (w1, hb), (w1, h1), (w1 - ponte, h1), (w0, h1 - d2)])
    pol = pol.intersection(sg.box(w0, h0, w1, h1))
    if pol.is_empty: return box
    pts = list(pol.exterior.coords)[:-1]
    if not sg.Polygon(pts).exterior.is_ccw: pts = pts[::-1]
    ew = np.zeros(3); ew[iw] = 1; eh = np.zeros(3); eh[k] = sg_; el = np.cross(ew, eh)
    origem = np.zeros(3); origem[il] = lo[il] if el[il] > 0 else hi[il]
    # ponto (w, h, l) -> w*ew + h*eh + l*el  (h ja e coordenada assinada ao longo de eh)
    return mf.CrossSection([pts]).extrude(ext[il]).transform(np.column_stack([ew, eh, el, origem]).tolist())

def aplica_gotas(PEC, GOTAS, extra=None):
    """bico de 45 graus em todo furo de junta deitado (na impressao da peca). extra: {peca: [(p0, p1, r)]} furos do proprio desenho"""
    n = 0
    fontes = [GOTAS] + ([extra] if extra else [])
    for nome, d in PEC.items():
        up = cima(nome)
        if up is None: continue
        bicos = []
        for F in fontes:
            for p0, p1, r in F.get(nome, []):
                g = gota(p0, p1, r, up)
                if g.volume() <= cil(p0, p1, r, 48).volume() + 1e-6: continue      # em pe: nada a fazer
                if (d["m"] ^ cil(p0, p1, r + 1.0, 32)).is_empty(): continue        # o furo nao passa nesta peca
                bicos.append(g)
        # 2 furos deitados paralelos que se cruzam deixam uma ponta de material pendurada entre eles: vira rasgo (casca convexa)
        specs = [(np.array(p0, float), np.array(p1, float), r) for F in fontes for p0, p1, r in F.get(nome, [])]
        for i in range(len(specs)):
            for j in range(i + 1, len(specs)):
                (a0, a1, ra), (b0, b1, rb) = specs[i], specs[j]
                ua = (a1 - a0) / np.linalg.norm(a1 - a0); ub = (b1 - b0) / np.linalg.norm(b1 - b0)
                if np.linalg.norm(np.cross(ua, ub)) > 1e-3 or abs(ua @ up) > 0.7: continue
                dist = np.linalg.norm(np.cross(b0 - a0, ua))
                if dist >= ra + rb - 0.05 or dist < 1e-3: continue
                ta = sorted(((b0 - a0) @ ua, (b1 - a0) @ ua)); La = np.linalg.norm(a1 - a0)
                lo, hi = max(0.0, ta[0]), min(La, ta[1])
                if hi - lo < 0.5: continue
                g1 = gota(a0 + ua * lo, a0 + ua * hi, ra, up); q0 = b0 + ub * ((a0 + ua * lo - b0) @ ub); q1 = b0 + ub * ((a0 + ua * hi - b0) @ ub)
                bicos.append((g1 + gota(q0, q1, rb, up)).hull())
        if bicos:
            d["m"] = d["m"] - mf.Manifold.batch_boolean(bicos, mf.OpType.Add); n += len(bicos)
    return n

def pino(base, ponta, r, up, w=1.5, folga=0.5, n=32):
    """pino deitado saindo de uma parede (base -> ponta): quilha de 45 graus + mao-francesa de 45 graus da parede ate a quilha.
    folga: a quilha/mao-francesa param antes da ponta (a face da ponta encosta em peca que gira)"""
    base = np.array(base, float); ponta = np.array(ponta, float); u = ponta - base; L = np.linalg.norm(u); u /= L
    m = cil(base, ponta, r, n)
    if up is None: return m
    up = np.array(up, float); v = up - (up @ u) * u
    if np.linalg.norm(v) < 0.7: return m
    v /= np.linalg.norm(v); wv = np.cross(u, v)
    fim = ponta - u * folga; Lq = L - folga
    m += quilha(base, fim, r, up, n)
    a = r * np.sqrt(2)                                          # ponta da quilha (abaixo do eixo)
    # triangulo no plano (u, v): (0, -a), (Lq, -a), (0, -a - Lq) -> extrudado em +-w
    tri = mf.CrossSection([[(0.0, -a), (0.0, -a - Lq), (Lq, -a)][::-1]])
    pts = [(0.0, -a), (Lq, -a), (0.0, -a - Lq)]
    ar = sum(pts[i][0] * pts[(i + 1) % 3][1] - pts[(i + 1) % 3][0] * pts[i][1] for i in range(3))
    tri = mf.CrossSection([pts if ar > 0 else pts[::-1]])
    # (s, t, e) -> base + s*u + t*v + e*wv ; precisa ser destro: se (u, v, wv) nao for, troca o sinal de e
    M = np.column_stack([u, v, wv, base - wv * w])
    return m + tri.extrude(2 * w).transform(M.tolist())

def limpa(m, vmin=0.05):
    """tira os pedacinhos de volume ~0 que sobram de booleana com face coincidente (atrapalham o corte e o fatiador)"""
    ps = [p for p in m.decompose() if p.volume() > vmin]
    if not ps: return m
    return ps[0] if len(ps) == 1 else mf.Manifold.batch_boolean(ps, mf.OpType.Add)
