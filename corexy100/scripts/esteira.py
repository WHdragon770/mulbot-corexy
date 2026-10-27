# Esteira porta-cabos da cabeca (ESTEIRA=1, padrao; ESTEIRA=0 volta o umbilical): 2 esteiras impressas, sem suporte
#   X: deitada numa bandeja atras da viga X (portico), ponta fixa no meio, laco pro lado -X, ponta movel no braco do carro
#   Y: por fora do lado direito, bandeja presa na viga Y por 3 maos-francesas; ponta movel no suporte do portico D;
#      o cabo sai da ponta fixa pra tras e entra na torre de tras D (canais do quadro ate a RAMPS)
# Elo: placas de dentro (macho) e de fora (femea), pino de filamento 1,75 (furo 1,9), trava reta (canto de baixo) e 50 graus (ressalto)
# Imprime em pe (barra de baixo na mesa); barra de cima com 2 aguas a 45 deixando ponte de 9 mm.
import numpy as np, manifold3d as mf
from base import caixa, cil, salva, add, tr, R4, DER
import semsup
from juntas import reg, subf, junta_passante

P, H, WI, T, C = 16.0, 10.0, 16.0, 1.6, 0.3      # passo, altura, largura de dentro, placa, folga entre placas
RE = H / 2                                        # raio das pontas
YI0, YI1 = WI / 2, WI / 2 + T                     # camada de dentro (macho)
YO0, YO1 = YI1 + C, YI1 + C + T                   # camada de fora (femea)
J0, J1 = 5.5, P - 5.5                             # trecho cheio (as 2 camadas) entre as pontas
RP = 0.95                                         # furo do pino de filamento 1,75
TRAVA = 50.0                                      # dobra maxima por junta (graus)
RL = 19.5                                         # raio do laco (corda P em RL = 48,5 graus < trava)
NX, NY = 8, 9   # corexy100 (200: 11, 12)                                  # elos de cada esteira

def _par(lo, hi, y0, y1):
    """caixa nas 2 placas (y de -y1 a -y0 e de y0 a y1)"""
    return caixa((lo[0], -y1, lo[1]), (hi[0], -y0, hi[1])) + caixa((lo[0], y0, lo[1]), (hi[0], y1, hi[1]))
def _disco(x, y0, y1): return cil((x, -y1, 0), (x, -y0, 0), RE, 48) + cil((x, y0, 0), (x, y1, 0), RE, 48)
def _pino(x, y0, y1): return semsup.gota((x, -y1 - 1, 0), (x, y1 + 1, 0), RP, (0, 0, 1), 24)
def _barras(x0, x1, duas=False):
    """barra de baixo (na mesa) + barra de cima com 2 aguas a 45 (ponte de 9 mm); duas=True: as 2 com agua (peca que imprime virada)"""
    a = YI0 - 4.5
    cs = mf.CrossSection([[(-YI0, RE - 5.5), (-a, RE - 2.0), (a, RE - 2.0), (YI0, RE - 5.5), (YI0, RE), (-YI0, RE)]])
    m = cs.extrude(x1 - x0).rotate([90, 0, 90]).translate([x0, 0, 0])
    return m + (m.mirror([0, 0, 1]) if duas else caixa((x0, -YI0 - 0.01, -RE), (x1, YI0 + 0.01, -RE + 2.0)))
def _poly(pts, y0, y1):
    """perfil (x, z) extrudado nas 2 placas (y de y0 a y1 e espelho)"""
    m = mf.CrossSection([pts]).extrude(y1 - y0).rotate([90, 0, 0])
    return m.translate([0, y1, 0]) + m.translate([0, -y0, 0])
def _chanfro(s):
    """canto de tras do disco no lado s (-1 = baixo) com agua de 45 tangente (sem balanco na impressao); raio max 5,42 < 5,5"""
    k = float(RE / np.sqrt(2)); pts = [(0.0, 0.0), (-k, s * k), (-(2 * k - RE), s * RE), (0.0, s * RE)]
    ar = sum(x0 * z1 - x1 * z0 for (x0, z0), (x1, z1) in zip(pts, pts[1:] + pts[:1]))
    return pts if ar > 0 else pts[::-1]
def _dente(phi, rc, rr, y0, y1):
    c = (float(rc * np.cos(np.radians(phi))), float(rc * np.sin(np.radians(phi))))
    return cil((c[0], -y1, c[1]), (c[0], -y0, c[1]), rr, 16) + cil((c[0], y0, c[1]), (c[0], y1, c[1]), rr, 16)
def _femea():
    """camada de fora em volta do pivo x=0: disco + agua de 45 embaixo (apoia na mesa; ao subir no laco desce so 0,4 mm)
    + dente atras (trava reta: a esteira de cima nao arria) + ressalto em cima (trava de 50 graus)"""
    m = _disco(0, YO0, YO1) + _par((0, -RE), (J0 + 0.01, RE), YO0, YO1) + _poly(_chanfro(-1), YO0, YO1)
    return m + _dente(190.0, 4.95, 0.6, YO0, YO1) + _dente(180 - TRAVA, 4.75, 0.75, YO0, YO1)
def _macho():
    """camada de dentro em volta do pivo x=P: disco + canto reto de baixo"""
    return _disco(P, YI0, YI1) + _par((J1 - 0.01, -RE), (P, RE), YI0, YI1) + _par((P, -RE), (P + RE, 0), YI0, YI1)

def elo():
    m = _femea() + _macho() + _par((J0, -RE), (J1, RE), YI0, YO1) + _barras(J0, J1)
    return m - _pino(0, YO0, YO1) - _pino(P, YI0, YI1)
def ponta_fixa():
    """macho de um elo 'zero' + corpo com piso e 2 furos M3 (pivo em x=P, esteira segue pra +x)"""
    m = _macho() + _par((J0, -RE), (J1, RE), YI0, YO1) + _barras(J0, J1) - _pino(P, YI0, YI1)
    m += _par((-8.0, -RE), (J0 + 0.01, RE), YI0, YO1) + caixa((-8.0, -YI0 - 0.01, -RE), (J0 + 0.01, YI0 + 0.01, -RE + 2.0))
    for y in (-4.0, 4.0): m -= cil((-1.0, y, -RE - 1), (-1.0, y, -RE + 3), 1.7, 24)
    return m
def soquete(s):
    """femea p/ o ultimo elo (pivo em x=0, esteira chega de -x): disco (o elo pode chegar inclinado) + corpo cheio ate x=12.
    s = lado do elo (z local) que fica pra baixo na impressao: leva a agua de 45"""
    m = _disco(0, YO0, YO1) + _par((0, -RE), (12.0, RE), YO0, YO1) + _poly(_chanfro(s), YO0, YO1)
    m += _par((J0, -RE), (12.0, RE), YI0, YO1) + _barras(J0, 12.0, True)
    return m - semsup.gota((0, -YO1 - 1, 0), (0, YO1 + 1, 0), RP, None, 24)   # o furo vira gota conforme a impressao da peca

# ---------------- caminho da esteira: reta de baixo, meia volta de raio RL, reta de cima; pivos a cada P (corda)
def _cam(s, ul):
    if s <= ul: return np.array([s, 0.0])
    if s <= ul + np.pi * RL:
        t = (s - ul) / RL; return np.array([ul + RL * np.sin(t), RL - RL * np.cos(t)])
    return np.array([ul - (s - ul - np.pi * RL), 2 * RL])
def _pivos(ul, n):
    ps, s = [np.zeros(2)], 0.0
    for _ in range(n):
        a, b = s, s + P * 1.6
        for _ in range(60):
            mid = (a + b) / 2
            if np.linalg.norm(_cam(mid, ul) - ps[-1]) < P: a = mid
            else: b = mid
        s = (a + b) / 2; ps.append(_cam(s, ul))
    return ps
def pivos(um, n):
    """pivos (u, v) com o 1o em (0,0) e o ultimo em (um, 2*RL): acha onde fica o laco (ul)"""
    a, b = -50.0, 400.0
    for _ in range(60):
        ul = (a + b) / 2; pN = _pivos(ul, n)[-1]
        if pN[0] < um: a = ul
        else: b = ul
    ps = _pivos((a + b) / 2, n)
    assert abs(ps[-1][1] - 2 * RL) < 1e-3 and abs(ps[-1][0] - um) < 0.05, ("esteira nao fecha", ps[-1], um)
    return ps, (a + b) / 2
def elos_T(origem, du, dv, um, n):
    """matrizes dos n elos: origem = 1o pivo, du/dv = vetores do mundo do eixo da esteira (pro laco) e de 'pra cima'"""
    o, du, dv = (np.array(v, float) for v in (origem, du, dv))
    ps, ul = pivos(um, n); Ts = []
    for a, b in zip(ps, ps[1:]):
        d = (b - a) / np.linalg.norm(b - a); ex = d[0] * du + d[1] * dv; ez = -d[1] * du + d[0] * dv
        Ts.append(R4(np.column_stack([ex, np.cross(ez, ex), ez]), o + a[0] * du + a[1] * dv))
    return Ts, ul

# ---------------- montagem (chamado pelo cxy.py)
YCX_E, Z0X, XFX = 34.5, 400.0, 14.0        # X (quadro do portico): centro da esteira em y, pivos de baixo em z, pivo fixo em x
XCY_E, Z0Y, YFY = 185.0, 346.0, 42.6       # Y (quadro do mundo): centro em x, pivos de baixo em z, pivo fixo em y
DXM, DYM = 14.0, -5.0                      # pivo movel: x no carro (X) / y no portico (Y)
def esteira_X(XC):
    return elos_T((XFX, YCX_E, Z0X), (-1, 0, 0), (0, 0, 1), XFX - (XC + DXM), NX)
def esteira_Y(YG):
    return elos_T((XCY_E, YFY, Z0Y), (0, -1, 0), (0, 0, 1), YFY - (YG + DYM), NY)

def aplica(G):
    QT, XC, YG, FD = G["QT"], G["XC"], G["YG"], G["FUROS_DESENHO"]
    fe = salva(elo(), "elo_esteira"); fp = salva(ponta_fixa(), "pontaFixa_esteira")
    for k, T_ in enumerate(esteira_X(XC)[0]): add(f"eloX_{k}", fe, QT["portico"] @ T_, "preto")
    for k, T_ in enumerate(esteira_Y(YG)[0]): add(f"eloY_{k}", fe, T_, "preto")
    # pontas fixas: o pivo P da ponta fica no 1o pivo da esteira, ponta virada pra tras do laco
    add("pontaFixaX", fp, QT["portico"] @ R4(np.column_stack([[-1, 0, 0], [0, -1, 0], [0, 0, 1]]), (XFX + P, YCX_E, Z0X)), "preto")
    add("pontaFixaY", fp, R4(np.column_stack([[0, -1, 0], [1, 0, 0], [0, 0, 1]]), (XCY_E, YFY + P, Z0Y)), "preto")

    # ---- bandeja X: prateleira atras da viga X + aba descendo na face de tras da viga (4x M3 em insertos na viga)
    yb, zt = 12.97, Z0X - RE
    m = caixa((-75, yb, zt - 4), (75, YCX_E + YO1 + 1.5, zt)) + caixa((-75, yb, 376), (75, yb + 4, zt))
    for x in (-60, -20, 20, 60):
        p0, p1 = (x, yb + 4.5, 385), (x, yb - 0.5, 385); m -= cil(p0, p1, 1.7, 24); FD.setdefault("bandejaX", []).append((np.array(p0), np.array(p1), 1.7))
        subf("trilhoX", (x, yb + 0.5, 385), (x, yb - 6.5, 385), 2.0)
    for y in (-4.0, 4.0): m -= cil((XFX + P + 1, YCX_E + y, zt - 5), (XFX + P + 1, YCX_E + y, zt + 1), 1.7, 24)   # M3 da ponta fixa
    reg("bandejaX", m, "cinza", "portico")

    # ---- braco do carro: em cima do pe do suporte da extrusora (M3 da direita passa nele, vira M3x18) ate o soquete
    xs, zs = DXM, Z0X + 2 * RL                                     # pivo movel no quadro do carro
    sq = soquete(-1).transform(R4(np.column_stack([[1, 0, 0], [0, -1, 0], [0, 0, -1]]), (xs, YCX_E, zs))[:3].tolist())
    ztop = zs + RE + 3.0
    m = sq + caixa((xs + J0, -36.0, G["ZPE"]), (30.0, 12.0, ztop)) + caixa((xs + J0, -12.0, zs - RE), (xs + 12.0, YCX_E + YO1, ztop))
    m = m + caixa((xs + J0, YCX_E - YO1, zs + RE - 0.01), (xs + 12.0, YCX_E + YO1, ztop)) + caixa((xs - RE, YCX_E + YO0, zs + RE - 0.01), (xs + 12.0, YCX_E + YO1, ztop)) + caixa((xs - RE, YCX_E - YO1, zs + RE - 0.01), (xs + 12.0, YCX_E - YO0, ztop))
    m -= cil((G["XI3"], G["YI3"], G["ZPE"] - 1), (G["XI3"], G["YI3"], ztop + 1), 1.7, 24)
    FD.setdefault("bracoEsteiraX", []).append((np.array((xs, YCX_E - YO1 - 1, zs)), np.array((xs, YCX_E + YO1 + 1, zs)), RP))
    reg("bracoEsteiraX", m, "verm", "carro")

    # ---- suporte no portico D: placa na face de fora (2x M3 em insertos) + soquete da esteira Y
    xf, ys, zs = 162.5, DYM, Z0Y + 2 * RL
    sq = soquete(1).transform(R4(np.column_stack([[0, 1, 0], [1, 0, 0], [0, 0, -1]]), (XCY_E, ys, zs))[:3].tolist())
    m = sq + caixa((xf, ys + J0, zs - RE), (XCY_E - YO1 + 0.01, ys + 12.0, zs + RE)) + caixa((xf, -24.0, zs - RE), (xf + 4.0, 10.0, zs + 20))
    for y, z in ((-17.0, zs + 13), (3.0, zs + 13)):
        p0, p1 = (xf + 4.5, y, z), (xf - 0.5, y, z); m -= cil(p0, p1, 1.7, 24); FD.setdefault("suporteEsteiraY", []).append((np.array(p0), np.array(p1), 1.7))
        subf("suportePortico_D", (xf + 0.5, y, z), (xf - 7.0, y, z), 2.0)
    FD["suporteEsteiraY"].append((np.array((XCY_E - YO1 - 1, ys, zs)), np.array((XCY_E + YO1 + 1, ys, zs)), RP))
    reg("suporteEsteiraY", m, "verm", "portico")

    # ---- bandeja Y (2 pecas) com maos-francesas presas na alma da viga Y por M6 passante
    zt = Z0Y - RE; x0, x1 = XCY_E - YO1 - 1.5, XCY_E + YO1 + 1.5
    perfil = mf.CrossSection([[(138, 265), (150, 265), (150, 283), (x1, zt - 10), (x1, zt), (174, zt), (174, 325), (138, 289)]])
    def mao(y): return perfil.extrude(8.0).rotate([90, 0, 0]).translate([0, y + 4.0, 0])
    for nome, (ya, yb_), ms in (("bandejaY_F", (-103.0, 70.0), (-85.0, 40.0)), ("bandejaY_T", (70.0, 166.0), (90.0, 130.0))):
        m = caixa((x0, ya, zt - 4), (x1, yb_, zt))
        for y in ms: m += mao(y)
        reg(nome, m, "cinza")
        for y in ms: junta_passante([nome, "trilhoY_D"], (150.0, y, 274.0), (-1, 0, 0), 200.0 - 163.5, d=6)
    for y in (-4.0, 4.0):   # M3 da ponta fixa (passa na bandeja da frente)
        G["PEC"]["bandejaY_F"]["m"] -= cil((XCY_E + y, YFY + P + 1, zt - 5), (XCY_E + y, YFY + P + 1, zt + 1), 1.7, 24)

    # ---- cabos (so na montagem/render): ponta fixa X -> por cima do portico D -> soquete Y; ponta fixa Y -> torre de tras D
    from correia import tubo
    c1 = tubo([(XFX + 10, YCX_E, Z0X), (60, YCX_E, Z0X - 1), (82, YCX_E, Z0X + 1), (89.5, YCX_E, 415), (90, YCX_E - 2, 452),   # sobe em x > 134 (fora do braco do carro)
              (130, 20, 460), (166, ys + 8, zs + 8), (XCY_E, ys + 10, zs)], r=3.5)
    c1.export(f"{DER}/caboEsteira_XY.stl"); add("caboEsteira_XY", f"{DER}/caboEsteira_XY.stl", QT["portico"], "preto")
    c2 = tubo([(XCY_E, YFY + 10, Z0Y), (XCY_E, 150, Z0Y - 1), (XCY_E - 6, 164, 362), (164, 165, 369), (153, 165, 369)], r=3.5)
    c2.export(f"{DER}/caboEsteira_Y.stl"); add("caboEsteira_Y", f"{DER}/caboEsteira_Y.stl", np.eye(4), "preto")
