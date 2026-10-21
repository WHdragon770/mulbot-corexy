# CoreXY estilo Mulbot (area 200x200x200) - montagem completa
# Variaveis de pose: XC (carro X), YG (centro do portico em Y), ZM (mesa: distancia do vidro abaixo do bico)
import sys; sys.path.insert(0, "/home/lucas/corexy/scripts")
from base import *
from juntas import PEC, FIX, reg, sub, junta_barril, junta_passante, emenda

# ================= parametros
Z0 = float(os.environ.get("Z0", 355.0))   # base dos trilhos Y
XR = 176.0                    # centro dos trilhos Y (+-)
LY = 290.0; Y0 = 47.63        # trilho Y: comprimento e centro em Y
YY0, YY1 = Y0 - LY / 2, Y0 + LY / 2
LX = 290.0                    # trilho X
XZ = XR; YZB = 40.0           # trilhos Z (embaixo dos trilhos Y): centro em X (+-) e base em Y (cabeca para a frente)
ZZT = Z0; LZ = 275.0          # topo e comprimento dos trilhos Z
# correias (2 planos empilhados). Placas das polias loucas: faces a +-20.2 do centro da correia
ZBASE = Z0 + CARRO_TOPO       # topo dos carros Y = fundo da base do suporte do portico
TPL = 8.0; TPM = 12.0         # espessura das placas (base/topo) e da placa do meio
GAP = 20.2
ZB = ZBASE + TPL + GAP; ZA = ZB + 2 * GAP + TPM
ZTOP = ZA + GAP + TPL         # topo das placas de cima
ZH = ZB - 52.0                # face inferior da cabeca do trilho X (cabeca para baixo, igual Mulbot)
XI = 170.0; XS = XI + RP; XO = XS + 2 * RP; XM = XS + RP
YF = -145.0; YM = 180.0
YFR0, YFR1 = YF - 18.0, 222.0 # quadro: frente e tras (postes/vigas de base)
XP0, XP1 = 161.0, 191.0       # postes e vigas laterais (x)
# pose
XC = float(os.environ.get("XC", 0.0))
YG = float(os.environ.get("YG", 47.63))
ZM = float(os.environ.get("ZM", 0.0))
YS = YG - 24.0                # linha das correias no sentido X (na frente do trilho X)
D_HOT = REF["HOT"][1] - 44.763   # bico em Y relativo ao centro do trilho X (-47.63)
ZBICO = ZH - 27.0
ZVIDRO = ZBICO - ZM           # topo do vidro
ZPLACA = ZVIDRO - 31.175      # fundo do suporte da mesa (DL1-03-04)
ZCZ = ZPLACA - 42.0           # centro do carro Z
QT = {"mundo": np.eye(4), "portico": tr((0, YG, 0)), "carro": tr((XC, YG, 0)), "mesa": tr((0, 0, ZCZ))}

def furo_v(x, y, z0, z1, d): return cil((x, y, z0), (x, y, z1), d / 2, 32)
FUROS_DESENHO = {}   # peca -> [(p0, p1, r)] furos do proprio desenho (fora das juntas) que viram gota na impressao
def espelhaX(m): return m.mirror([1, 0, 0])
Dstem = 8.9
LST_PL, LST_PM = 10.0, 14.0   # comprimento dos eixos das polias loucas (cortados) nas placas fina/do meio
def ambos(f):
    """chama f(lado, sx) p/ direita e esquerda"""
    for lado, sx in (("D", 1), ("E", -1)): f(lado, sx)

# ================= guias em V impressas no X e no Y (mesma roldana do Z, zv.py; versao com esferas: cxy.py.bak_esferasXY)
# viga em T: aba com V nas 2 bordas + alma; 3 roldanas por carro (2 fixas num lado, excentrica do outro),
# bucha excentrica tipo espacador (sextavado de 6 mm entre placa e roldana, chave entra pelo lado)
import zv, semsup
ZWY = ZBASE - zv.ESP - zv.HW              # plano das roldanas Y (embaixo da base do suporte do portico)
def viga_y(x0):
    """aba em cima (V nas bordas +-x), alma descendo ate Z0; secao em (x, -z) extrudada ao longo de Y"""
    return zv.secao_v(x0, -ZWY, -Z0).extrude(LY).transform([[1, 0, 0, 0], [0, 0, 1, YY0], [0, -1, 0, 0]])
for lado, sx in (("E", -1), ("D", 1)):
    reg("trilhoY_" + lado, viga_y(sx * XR), "cinza")
RODAS_Y = [(XR - zv.XCW, -19.0), (XR - zv.XCW, 19.0), (XR + zv.XCW, 0.0)]   # lado direito, quadro YG=0 (fixas por dentro)
# X: aba vertical virada para a frente, alma para tras ate y=13; roldanas atras da torre de presilhas (face y=-19)
ZT0 = ZH + 35.54                          # fundo da torre de presilhas = topo da prateleira do hotend
YCX = -19.0; YWX = YCX + zv.ESP + zv.HW   # face de tras do carro X e plano das roldanas X
ZLX = ZT0 + 5.3                           # roldanas fixas de baixo (cabeca do M6 logo acima da prateleira, furo abaixo da fenda da correia B)
ZCX = ZLX + zv.XCW; ZUX = ZCX + zv.XCW    # centro da viga X e excentrica de cima
HAX = 12.0                                # meia-altura da alma da viga X
RODAS_X = [(-19.0, ZLX), (19.0, ZLX), (0.0, ZUX)]
def viga_x():
    """secao em (z, y) extrudada ao longo de X (de +LX/2 para -LX/2)"""
    return zv.secao_v(ZCX, YWX, 13.0, HAX).extrude(LX).transform([[0, 0, -1, LX / 2], [0, 1, 0, 0], [1, 0, 0, 0]])
reg("trilhoX", viga_x(), "cinza", "portico")
dX = tr((XC, YG - 44.763, ZH - 197.5))
for n in ["hotend", "hotend_bloco", "hotend_bico", "presilhaHotend"]:
    p, t, c = RI[n]; add(n, p, dX @ t, c)
RZ = np.column_stack([[-1, 0, 0], [0, 0, -1], [0, -1, 0]])
SZ = ZZT - ZCZ                # posicao do carro ao longo do trilho Z
GUIAZ = os.environ.get("GUIAZ", "v")      # v = guia em V com roldanas (zv.py) | esferas = trilho/carro Mulbot
YW = YZB - CARRO_TOPO + 2.0 + zv.HW       # plano das roldanas (face do braco + ressalto de 2 mm + meia roldana)
for lado, sx in (("E", -1), ("D", 1)):
    F = R4(RZ, (sx * XZ, YZB, ZZT))
    if GUIAZ == "v":
        reg("trilhoZ_" + lado, zv.viga_v(sx * XZ, YW, YZB, ZZT - LZ, ZZT), "cinza")
    else:
        reg("trilhoZ_" + lado, trilho(LZ).transform(F[:3].tolist()), "cinza")
        carro("carroZ_" + lado, F, SZ)

# ================= ventoinha 5015 na frente do hotend + duto estreito (passa entre as presilhas da mesa nos cantos)
# quadro do bico: origem na ponta do bico. Abaixo de bico+7.5 o duto fica em |x| < 7 (as presilhas ficam fora disso)
YFV = -17.7; ZFV = 60.0; XFV = -15.0          # ventoinha: face de tras, centro (z), deslocamento p/ saida ficar em x~0
def duto():
    m = caixa((-40, -17.7, 35), (19, -12.7, 85))                                   # espinha (presa nos 2 parafusos da presilha do hotend)
    for sx in (-12.7, 12.7): m -= cil((sx, -19, 56.19), (sx, -12, 56.19), 1.7, 24)
    m -= cil((XFV + 20.3, -19, ZFV - 20.3), (XFV + 20.3, -12, ZFV - 20.3), 1.6, 24)   # orelhas da 5015
    m -= cil((XFV - 20.3, -19, ZFV + 20.3), (XFV - 20.3, -12, ZFV + 20.3), 1.6, 24)
    # sem suporte: tirante, soquete, descida e bico vao ate o plano de tras da espinha (y = -12.7) -> imprime deitado nele
    m += caixa((12, -17.7, 15), (18, -12.7, 35))                                   # tirante espinha -> soquete
    m += caixa((-12, -35, 15), (12, -12.7, 23))                                    # soquete na boca da ventoinha
    m += caixa((-9.5, -33, 8.5), (9.5, -12.7, 15.5))                               # descida
    m += caixa((-6.5, -33, 2.0), (6.5, -12.7, 10.0))                               # bico estreito (saida a 12.7 mm do bico)
    m -= caixa((-10.3, -33.0, 14.9), (10.3, -17.4, 23.1))
    m -= caixa((-7.5, -31, 10.0), (7.5, -18, 15.2))
    m -= caixa((-4.5, -31, 4.0), (4.5, -18, 10.2)) + caixa((-4.5, -31, 4.0), (4.5, -12.0, 8.0))
    return m
TN0 = tr((0, D_HOT, ZBICO))       # quadro do bico com XC=0, YG=0
reg("dutoCoreXY", duto().transform(TN0[:3].tolist()), "azul", "carro")
add("ventoinha5015", f"{VT}/ventoinha5015.stl", QT["carro"] @ TN0 @ R4(np.column_stack([[1, 0, 0], [0, 0, 1], [0, -1, 0]]), (XFV, YFV, ZFV)), "preto")

# ================= suporte do portico (base = placa das roldanas Y; segura a viga X e as 2 polias loucas)
YLING = 25.4 + 17.1           # ponta da lingueta do fim de curso Y (aperta a chave com YG = 152)
def suporte_portico(yB, yA, lingueta=False):
    """lado direito no quadro YG=0. yB/yA: y das polias dos planos B/A"""
    m = caixa((145, -44, ZBASE), (XR + 25.4, 25.4, ZBASE + TPL))
    m += caixa((XR + 20, -44, ZBASE), (XR + zv.XCW + 10, 15, ZBASE + TPL))             # orelha da roldana excentrica (fora); vai ate y=-44: imprime em pe sem suporte
    if lingueta: m += caixa((156.5, 25.4, ZBASE), (164.5, YLING, ZBASE + TPL))       # aperta o fim de curso Y
    m += caixa((145, -13, ZBASE), (155, 13, ZTOP))                                     # parede: ponta da viga X
    m += caixa((130, -12, ZCX + HAX), (155, 12, ZCX + HAX + 10))                        # aba por cima da alma da viga X
    tri = mf.CrossSection([[(145.0, -13.0), (145.0, -12.0), (128.0, 5.0), (128.0, -13.0)]])         # sem suporte: ponta da aba chanfrada a 45 graus (impressao com +Y pra cima)
    m -= tri.extrude(12).translate([0, 0, ZCX + HAX - 1])
    m += caixa((145, -44, ZB + GAP), (184, -5, ZB + GAP + TPM))                         # placa do meio
    m += caixa((145, -44, ZA + GAP), (184, -5, ZTOP))                                   # placa de cima
    m += caixa((150, -44, ZBASE), (158, -36, ZTOP))                                     # coluna
    # sem suporte (imprime com +Y pra cima): o fundo da parede entre as placas era ponte de ~40 mm -> 2 aguas de 45 graus
    # saindo de cada placa, sobra ponte de semsup.PONTE no meio (correias passam em y -17 / -31, abaixo das aguas)
    for z0, z1 in ((ZBASE + TPL, ZB + GAP), (ZB + GAP + TPM, ZA + GAP)):
        dr = (z1 - z0 - semsup.PONTE) / 2
        for zb, s_ in ((z0, 1), (z1, -1)):
            pts = [(zb, -13.0 + 0.01), (zb, -13.0 - dr), (zb + s_ * dr, -13.0 + 0.01)]          # (z, y)
            ar = sum(pts[i][0] * pts[(i + 1) % 3][1] - pts[(i + 1) % 3][0] * pts[i][1] for i in range(3))
            cs = mf.CrossSection([pts if ar > 0 else pts[::-1]])
            m += cs.extrude(10.0).transform([[0, 0, -1, 155.0], [0, 1, 0, 0], [1, 0, 0, 0]])  # (z, y, w) -> (155 - w, y, z), destro
    for x, y in RODAS_Y[:2]:                                                           # folga da cabeca do M6 das roldanas fixas
        m -= cil((x, y, ZBASE + TPL - 0.01), (x, y, ZBASE + TPL + 20), 6.0, 48)
        if y < 0:                                                                      # a de y=-19 fica embaixo da parede: alivio vai ate ela, teto em V 45
            pent = mf.CrossSection([[(x - 6, y), (x + 6, y), (x + 6, -13.0), (x, -7.0), (x - 6, -13.0)]])
            fim = ZB + GAP - (ZB + GAP - ZBASE - TPL - semsup.PONTE) / 2          # ate o comeco da agua de cima (sem trecho chato em balanco)
            m -= pent.extrude(fim - (ZBASE + TPL) + 0.02).translate([0, 0, ZBASE + TPL - 0.01])
    fs = [((XI, yB, ZBASE - 1), (XI, yB, ZBASE + TPL + 1), Dstem / 2), ((XI, yB, ZB + GAP - 1), (XI, yB, ZB + GAP + TPM + 1), Dstem / 2),
          ((XI, yA, ZB + GAP - 1), (XI, yA, ZB + GAP + TPM + 1), Dstem / 2), ((XI, yA, ZA + GAP - 1), (XI, yA, ZTOP + 1), Dstem / 2)]
    up = np.array([0, 1.0, 0])                                                         # imprime com +Y pra cima (em pe na borda da frente)
    for x, y in RODAS_Y[:2]:                                                           # espacador das fixas (so na pista interna)
        m += semsup.pino((x, y, ZBASE + 0.5), (x, y, ZBASE - zv.ESP), 4.6, up)       # quilha + mao-francesa 45 graus (param 0.5 antes da roda)
    bx, by = RODAS_Y[2]                                                                # excentrica: ressalto da bucha + folga do M6
    fs.append(((bx - zv.EXC, by, ZBASE - 1), (bx - zv.EXC, by, ZBASE + TPL + 1), 6.0 + zv.TOL["fdm"]["bucha"]))
    for a, b, r in fs: m -= semsup.gota(a, b, r, up, 64)
    return m
for lado, sx, yB, yA in (("D", 1, -31, -17), ("E", -1, -17, -31)):
    m = suporte_portico(yB, yA, lingueta=(lado == "E"))
    reg("suportePortico_" + lado, m if sx > 0 else espelhaX(m), "verm", "portico")
    # viga X presa na parede (2x M6 com barril) e na aba (1x M6 vertical)
    n = "suportePortico_" + lado
    for z in (ZCX - 5.5, ZCX + 5.5):       # cabeca rebaixada 4.5 mm (senao raspa na parede interna da torre de tras)
        junta_barril(n, "trilhoX", (sx * 150.5, 0, z), (-sx, 0, 0), 30, (0, 1, 0), 19.05, d=6, cb=4.5, q="portico")
    junta_barril(n, "trilhoX", (sx * 138, 8.0, ZCX + HAX + 10), (0, 0, -1), 22, (1, 0, 0), 10.0, d=6, q="portico")   # atras dos horizontais

# ================= presilha das correias no carro do hotend (torre com 2 planos, pino para dar a volta na correia)
RO = 3.0 + 0.9; PINX = 10.0
EXTRUSORA = os.environ.get("EXTRUSORA", "direta")   # direta = EZR em cima do carro | bowden = EZR no quadro (Mulbot)
ZTP = ZA + (14 if EXTRUSORA == "direta" else 8)       # topo da torre (direta: +6 mm p/ os insertos do suporte)
XI3 = 24.5; YI3 = -28.0                               # insertos M3 (latao, furo 4.0 x 6) no topo da torre
def torre_presilha():
    m = caixa((-30, -37, ZT0 - 1.0), (30, -19, ZTP))   # desce 1 mm dentro da prateleira (vira 1 peca so)
    for z in (ZA, ZB):
        for s in (-1, 1):
            m -= semsup.telhado((s * (PINX - RO - 1.2), -24 - 2 * RO - 1.3, z - 6.4), (s * 31, -24 + 1.3, z + 6.4), (1, 0, 0))   # fundo da fenda: teto 45 graus (carro imprime com +X pra cima)
    for s in (-1, 1):
        m += cil((s * PINX, -24 - RO, ZT0), (s * PINX, -24 - RO, ZA + 8), 3.0)
        if EXTRUSORA == "direta": m -= furo_v(s * XI3, YI3, ZTP - 6, ZTP + 1, 4.0)
    return m
# ================= carro X (1 peca): prateleira do hotend da Mulbot (frente do carroHotend, sem o carro de esferas)
# + torre de presilhas + espacadores das roldanas + braco que aperta o fim de curso X
YBR = (-19.0, 18.0); ZBR = (512.0, 520.0)              # braco do fim de curso X (atras da torre, por cima da viga)
XIB, ZIB = -24.0, (508.0, 531.0)                       # 2 insertos M3 (latao 4.0 x 6) na face de tras da torre p/ o braco (fora das fendas das correias)
def braco_fim_x():
    """braco que aperta o fim de curso X: peca separada (imprime deitada na face x=-30), aparafusada na face de tras da torre"""
    m = caixa((-30, YCX, 503.0), (-18, YCX + 4.0, 535.0))                 # flange encostada na torre (4 mm)
    m += caixa((-30, YCX + 4.0 - 0.01, ZBR[0]), (-24, YBR[1], ZBR[1]))    # braco (mesma face x = -30 que aperta a chave)
    for z in ZIB:
        m -= semsup.gota((XIB, YCX - 1, z), (XIB, YCX + 5, z), 1.7, (1, 0, 0), 24)   # M3 passante
    return m
def carro_x():
    p, t, c = RI["carroHotend"]
    m = peca_mf(p, tr((0, -44.763, ZH - 197.5)) @ t) ^ caixa((-40, -60, ZT0 - 20), (40, -25.4, ZT0 + 1))
    m += torre_presilha()
    for z in ZIB: m -= semsup.gota((XIB, YCX + 0.01, z), (XIB, YCX - 6.0, z), 2.0, (1, 0, 0), 24)   # insertos M3 do braco do fim de curso
    sl = m ^ caixa((-25.2, -60, ZT0 - 20), (-24.4, -25.4, ZT0 - 1.0))          # sem suporte (imprime deitado na face x=-30 da torre):
    for k in range(7): m += sl.translate([-0.8 * (k + 1), 0, 0])              # a prateleira (borda em x=-25.4) desce ate x=-30 (ficava 4.6 mm no ar)
    m -= caixa((-40, -60, ZT0 - 21), (-30, 0, ZT0 + 1))
    for x, z in RODAS_X[:2]:
        m += semsup.pino((x, YCX - 0.5, z), (x, YCX + zv.ESP, z), 4.6, (1, 0, 0))   # quilha + mao-francesa 45 graus (param 0.5 antes da roda)
    m -= caixa((-40, -70, ZT0 - 30), (-30, 30, ZTP + 10))                   # nada abaixo da face x=-30 (mesa da impressao)
    bx, bz = RODAS_X[2]                                   # excentrica: ressalto raso (3 mm, fora da fenda da correia A) + folga do M6
    m -= cil((bx, YCX + 0.01, bz - zv.EXC), (bx, YCX - 3.0, bz - zv.EXC), 6.0 + zv.TOL["fdm"]["bucha"], 64)
    m -= cil((bx, YCX + 1, bz - zv.EXC), (bx, -38, bz - zv.EXC), 4.2, 32)
    return m
reg("carroX", carro_x(), "azul", "carro")
reg("bracoFimCursoX", braco_fim_x(), "azul", "carro")

# ================= roldanas X e Y (rolamento de roletes impresso em resina, 1 peca so) + buchas excentricas + M6
_rr = zv.roldana_resina(partes=True)
salva(_rr["roda"] + _rr["pista"], "rodaV"); salva(_rr["roletes"], "rodaV_roletes")     # na montagem: pontes ja quebradas
salva(zv.bucha_esp(3.0), "buchaX"); salva(zv.bucha_esp(TPL), "buchaY")
def roda(nome, T):
    add(nome, f"{DER}/rodaV.stl", T, "verm"); add(nome + "_roletes", f"{DER}/rodaV_roletes.stl", T, "cinza")
RwX = np.column_stack([[1, 0, 0], [0, 0, -1], [0, 1, 0]])            # eixo da roldana (z local) -> +Y
for k, (x, z) in enumerate(RODAS_X):
    roda(f"rodaX_{k}", QT["carro"] @ R4(RwX, (x, YWX, z)))
    grip = (YCX + 37.0) + zv.ESP + 2 * zv.HW                           # torre (18) + espacador + roldana
    junta_passante(["carroX"], (x, -37.0, z), (0, 1, 0), grip, d=6, q="carro")
bx, bz = RODAS_X[2]
add("buchaX", f"{DER}/buchaX.stl", QT["carro"] @ R4(np.column_stack([[0, 0, 1], [1, 0, 0], [0, 1, 0]]), (bx, YCX, bz - zv.EXC)), "latao")
for lado, sx in (("D", 1), ("E", -1)):
    for k, (x, y) in enumerate(RODAS_Y):
        roda(f"rodaY_{lado}{k}", QT["portico"] @ tr((sx * x, y, ZWY)))
        junta_passante(["suportePortico_" + lado], (sx * x, y, ZBASE + TPL), (0, 0, -1), TPL + zv.ESP + 2 * zv.HW, d=6, q="portico")
    bx, by = RODAS_Y[2]
    add(f"buchaY_{lado}", f"{DER}/buchaY.stl",
        QT["portico"] @ R4(np.column_stack([[sx, 0, 0], [0, -sx, 0], [0, 0, -1]]), (sx * (bx - zv.EXC), by, ZBASE)), "latao")

# ================= torres da frente (polias loucas dos cantos) e de tras (motores A/B)
def torre_frente(xB, xA):
    yi = YF + RP; y0, y1 = YF - 18, YF + 22
    m = caixa((150, y0, ZBASE), (200, y1, ZBASE + TPL))
    m += caixa((150, y0, ZB + GAP), (200, y1, ZB + GAP + TPM)) + caixa((150, y0, ZA + GAP), (200, y1, ZTOP))
    m += caixa((150, y0, ZBASE), (200, YF - 4, ZTOP)) + caixa((194, y0, ZBASE), (200, y1, ZTOP))
    m += caixa((155, y0, ZBASE - 25), (161, y1, ZBASE)) + caixa((191, y0, ZBASE - 25), (197, y1, ZBASE))   # saia em volta do poste
    m -= furo_v(xB, yi, ZBASE - 1, ZBASE + TPL + 1, Dstem)
    m -= furo_v(xB, yi, ZB + GAP - 1, ZB + GAP + TPM + 1, Dstem); m -= furo_v(xA, yi, ZB + GAP - 1, ZB + GAP + TPM + 1, Dstem)
    m -= furo_v(xA, yi, ZA + GAP - 1, ZTOP + 1, Dstem)
    return m
def torre_tras(zface, baixo):
    """placa do motor (baixo=True: eixo para cima, placa em cima da face)"""
    zp0, zp1 = (zface, zface + 6.0) if baixo else (zface - 6.0, zface)
    m = caixa((158, 156, zp0), (206, 222, zp1))                                          # placa do motor
    m += caixa((158, 208, Z0 + H_TRILHO), (206, 222, zp1))                               # parede de tras (em cima do poste)
    m += caixa((158, 156, ZBASE + 12), (162.5, 222, zp1))                                # parede interna (4.5: o corpo do motor comeca em x=162.85)
    m += caixa((155, 208, Z0 + H_TRILHO - 25), (161, 222, Z0 + H_TRILHO)) + caixa((191, 200, Z0 + H_TRILHO - 25), (197, 222, Z0 + H_TRILHO))
    ch = mf.CrossSection([[(154.0, Z0 + H_TRILHO - 4.0), (158.0, Z0 + H_TRILHO + 0.01), (154.0, Z0 + H_TRILHO + 0.01)]])  # (x, z)
    m -= ch.extrude(16).transform([[1, 0, 0, 0], [0, 0, -1, 223], [0, 1, 0, 0]])   # chanfro 45 graus no topo de fora da saia (y 207..223)
    m -= cil((XM, YM, zp0 - 1), (XM, YM, zp1 + 1), 11.5)
    for dx in (-15.5, 15.5):
        for dy in (-15.5, 15.5): m -= furo_v(XM + dx, YM + dy, zp0 - 1, zp1 + 1, 3.4)
    return m
for lado, sx, xB, xA in (("D", 1, XI, XM), ("E", -1, XM, XI)):
    m = torre_frente(xB, xA); reg("torreFrente_" + lado, m if sx > 0 else espelhaX(m), "azul")
for lado, sx, zf, bx in (("D", 1, ZA - POLIA_FACE, True), ("E", -1, ZB + POLIA_FACE, False)):
    m = torre_tras(zf, bx); reg("torreTras_" + lado, m if sx > 0 else espelhaX(m), "azul")

# ================= quadro: postes, vigas de base, bases Z, travessas de cima
ZFACE_MZ = 43.0               # face do motor Z (corpo ate z=3)
SM = ZZT - ZFACE_MZ - 124.96  # deslocamento do conjunto motor/fuso ao longo do trilho Z
Fm = json.load(open(f"{DER}/zrel.json"))
YFUSO = YZB - 111.13
ZTZ = ZZT - LZ                # pe do trilho Z
def base_z(zf):
    """bloco no chao (lado direito): motor Z (eixo para cima) + colar do fuso + soquete do pe do trilho Z.
    Linguetas de emenda (meia altura) para as vigas laterais na frente e atras"""
    m = caixa((XZ - 28, -30, 0), (XZ + 28, 46, ZTZ)) + caixa((XZ - 28, -96, 0), (XZ + 28, -30, 66.0))
    m += caixa((XP0, -126, 0), (XP1, -96, 15)) + caixa((XP0, 46, 0), (XP1, 86, 15))           # linguetas
    m += caixa((XZ - 16, -12, ZTZ), (XZ - 9.825, 46, ZTZ + 25)) + caixa((XZ + 9.825, -12, ZTZ), (XZ + 16, 46, ZTZ + 25))
    m += caixa((XZ - 16, YZB + 0.3, ZTZ), (XZ + 16, 46, ZTZ + 25))                           # soquete do trilho Z
    m -= caixa((XZ - 21.6, YFUSO - 21.6, -1), (XZ + 21.6, YFUSO + 21.6, zf))         # alojamento do motor
    m -= semsup.telhado((XZ - 15, YFUSO - 30, -1), (XZ + 15, YFUSO, 12), (0, 0, 1))  # passagem do cabo (frente), teto em 45 graus
    m -= cil((XZ, YFUSO, zf - 1), (XZ, YFUSO, zf + 3), 11.5)                            # ressalto do motor
    m -= cil((XZ, YFUSO, zf + 2), (XZ, YFUSO, 67), 14.3)                                # colar do fuso
    for dx in (-15.5, 15.5):
        for dy in (-15.5, 15.5): m -= furo_v(XZ + dx, YFUSO + dy, zf - 1, zf + 8, 3.4)
    return m
def b(a, c): return caixa(a, c)
for lado, sx in (("D", 1), ("E", -1)):
    S = (lambda m: m) if sx > 0 else espelhaX
    reg("baseZ_" + lado, S(base_z(ZFACE_MZ)), "azul")
    reg("baseLatF_" + lado, S(b((XP0, YFR0, 0), (XP1, -126, 30)) + b((XP0, -126, 15), (XP1, -96, 30))), "cinza")
    reg("baseLatT_" + lado, S(b((XP0, 86, 0), (XP1, YFR1, 30)) + b((XP0, 46, 15), (XP1, 86, 30))), "cinza")
    reg("posteFrente_" + lado, S(b((XP0, YFR0, 30), (XP1, YY0, ZBASE))), "cinza")
    reg("posteTras_" + lado, S(b((XP0, YY1, 30), (XP1, YFR1, Z0 + H_TRILHO))), "cinza")
    reg("chapaZY_" + lado, S(b((XZ - 9.525 - 10, -12, ZZT - 60), (XZ - 9.525, 40, ZZT + 48))), "azul")
reg("baseFrente", b((-XP0, YFR0, 0), (XP0, YFR0 + 30, 30)), "cinza")
reg("baseTras", b((-XP0, YFR1 - 30, 0), (XP0, YFR1, 30)), "cinza")
reg("travFrente", b((-200, YFR0 - 14, ZBASE), (200, YFR0, ZBASE + 60)), "cinza")
reg("travTras", b((-206, YFR1, ZBASE), (206, YFR1 + 14, ZBASE + 50)), "cinza")

# ----- juntas do quadro (M10 impresso; porca-barril onde a peca e estreita)
for lado, sx in (("D", 1), ("E", -1)):
    X = lambda x: sx * x
    pf, pt, bl, bz = "posteFrente_" + lado, "posteTras_" + lado, "baseLatF_" + lado, "baseZ_" + lado
    tY, tZ, ch = "trilhoY_" + lado, "trilhoZ_" + lado, "chapaZY_" + lado
    # trilho Y -> postes (frente: rebaixo fundo no poste; tras: atravessa o poste)
    for z in (Z0 + 15, Z0 + 40):
        junta_barril(pf, tY, (X(XR), YY0 - 16, z), (0, 1, 0), 45, (1, 0, 0), 19.05, cb=YY0 - 16 - YFR0)
        junta_barril(pt, tY, (X(XR), YFR1, z), (0, -1, 0), 60, (1, 0, 0), 19.05)
    # postes -> vigas laterais (de baixo para cima, barril no poste)
    for y, vg in ((-138, bl), (-120, bz), (-104, bz), (200, "baseLatT_" + lado)):
        junta_barril(vg, pf if y < 0 else pt, (X(XR), y, 7), (0, 0, 1), 55, (1, 0, 0), 30, cb=7, atravessa=(bl,) if vg == bz else ())
    # vigas de frente/tras -> vigas laterais (de fora para dentro, barril na viga transversal)
    junta_barril(bl, "baseFrente", (X(XP1), -148, 15), (-sx, 0, 0), 55, (0, 0, 1), 30)
    junta_barril("baseLatT_" + lado, "baseTras", (X(XP1), 215, 15), (-sx, 0, 0), 55, (0, 0, 1), 30)
    # base Z <-> vigas laterais (linguetas sobrepostas, parafuso passante vertical)
    for y in (56, 76): junta_passante([bz, "baseLatT_" + lado], (X(XR), y, 0), (0, 0, 1), 30)
    # pe do trilho Z no soquete da base Z (passante em X)
    junta_passante([bz, tZ], (X(XZ - 16), 15, ZTZ + 12), (sx, 0, 0), 32)
    # topo do trilho Z <-> trilho Y: chapa na face interna, passantes em X
    for y, z in ((0, ZZT + 14), (28, ZZT + 36)): junta_passante([ch, tY], (X(XZ - 19.525), y, z), (sx, 0, 0), 29.05)
    for y, z in ((0, ZZT - 20), (28, ZZT - 45)): junta_passante([ch, tZ], (X(XZ - 19.525), y, z), (sx, 0, 0), 29.05)
    # torres em cima dos postes: saia + passante em X
    for y in (YF - 8, YF + 12): junta_passante(["torreFrente_" + lado, pf], (X(155), y, ZBASE - 12.5), (sx, 0, 0), 42)
    junta_passante(["torreTras_" + lado, pt], (X(155), 215, Z0 + H_TRILHO - 12.5), (sx, 0, 0), 42)
    # travessas de cima: passantes em Y (porca do lado de dentro, fora dos planos das correias)
    for z in (Z0 + 100, Z0 + 152): junta_passante(["travFrente", "torreFrente_" + lado], (X(152), YFR0 - 14, z), (0, 1, 0), 28, d=6)
    for x in (175, 196): junta_passante(["travTras", "torreTras_" + lado], (X(x), YFR1 + 14, ZBASE + 16), (0, -1, 0), 28, d=6)   # +16: porca acima da rampa da ponte da torre
# divisoes para caber numa mesa de 220 (emenda sobreposta + 2 passantes)
for lado in ("D", "E"):
    emenda("posteFrente_" + lado, "posteFrenteInf_" + lado, "posteFrenteSup_" + lado, 2, 235.0, 60, 0, XR * (1 if lado == "D" else -1))
    emenda("posteTras_" + lado, "posteTrasInf_" + lado, "posteTrasSup_" + lado, 2, 226.0, 60, 0, XR * (1 if lado == "D" else -1))
emenda("baseFrente", "baseFrente_E", "baseFrente_D", 0, 45.0, 60, 2, 15.0)    # fora do meio: a passagem do cabo do display (x -10..10) nao cai no septo da emenda
emenda("baseTras", "baseTras_E", "baseTras_D", 0, 0.0, 60, 2, 15.0)
emenda("travFrente", "travFrente_E", "travFrente_D", 0, 0.0, 60, 2, ZBASE + 30, d=6)
emenda("travTras", "travTras_E", "travTras_D", 0, 0.0, 60, 2, ZBASE + 25, d=6)
# base Z em 2 pecas na face do motor Z: embaixo um anel aberto (alojamento sem teto), em cima a tampa onde o motor parafusa
# (as 2 imprimem em pe sem suporte); 4 x M6 de cima pra baixo com porca-barril na de baixo
from juntas import corta
for lado, sx in (("D", 1), ("E", -1)):
    X = lambda x: sx * x
    bi, bs = "baseZInf_" + lado, "baseZSup_" + lado
    corta("baseZ_" + lado, bi, bs, 2, ZFACE_MZ)
    for dx in (-21, 21):
        junta_barril(bs, bi, (X(XZ + dx), -20, ZTZ), (0, 0, -1), 65, (0, 1, 0), 16, d=6)      # corpo (fora do soquete do trilho Z e da cavidade)
        junta_barril(bs, bi, (X(XZ + dx), -38, 66.0), (0, 0, -1), 50, (0, 1, 0), 16, d=6)     # bloco da frente (parede atras do motor)

# ================= Z: porca/fuso da Mulbot + motores
def fuso_longo():
    fn = f"{DER}/DL1-02-06_longo.stl"      # +40 mm = 10 passos de 4 mm -> 250 mm
    if not os.path.exists(fn):
        m = M(mesh("DL1-02-06"))
        a = m ^ caixa((-60, 60, -1), (0, 120, 141.0)); b_ = (m ^ caixa((-60, 60, 100.5), (0, 120, 211))).translate([0, 0, 40])
        salva(a + b_, "DL1-02-06_longo")
    return fn
for lado, sx in (("E", -1), ("D", 1)):
    F = R4(RZ, (sx * XZ, YZB, ZZT))
    if GUIAZ == "v":     # fuso e porca com rosca trapezoidal parametrica (folga de MAT=fdm|resina)
        fz, EIXO_FUSO = zv.fuso(F @ tr((0, SM, 0)) @ np.array(Fm["fuso"]))
        reg("fusoZ_" + lado, fz, "verm"); reg("porcaZ_" + lado, zv.porca(F @ tr((0, SZ, 0)) @ np.array(Fm["porca"]), EIXO_FUSO), "azul")
    else:
        add("porcaZ_" + lado, "DL1-04-06", F @ tr((0, SZ, 0)) @ np.array(Fm["porca"]), "azul")
        add("fusoZ_" + lado, fuso_longo(), F @ tr((0, SM, 0)) @ np.array(Fm["fuso"]), "verm")
    motor("motorZ_" + lado, F @ tr((0, SM, 0)) @ np.array(Fm["motor"]), polia=False)

# ================= braco da mesa (carro Z + porca -> suporte da mesa)
EM = 1.10; VID = 235.0        # suporte DL1-03-04 ampliado 10% em XY e vidro 235x235 (vidro de Ender 3)
# roldanas no braco (x relativo ao trilho do lado direito, z relativo a ZCZ): 2 fixas por fora, excentrica por dentro
# (por fora ficam acima da porca, z >= -19, senao a cabeca do M6 bate nela)
RODAS_Z = [(zv.XCW, -19.0), (zv.XCW, 21.0), (-zv.XCW, 1.0)]
def braco_mesa():
    """lado direito, quadro com ZCZ = 0"""
    yf = YZB - CARRO_TOPO; yp = yf - 9.5                     # face do carro (-45.61) e face da porca (-55.11)
    if GUIAZ == "v":
        m = caixa((XZ - 36, yp, -46), (XZ + 36, yf, 25.4))   # placa vertical (roldanas + porca)
        m += caixa((XZ + 15, yp, 25.4), (XZ + 36, yf, 32))    # sobe por fora p/ a roldana de cima
        for x, z in RODAS_Z[:2]: m += cil((XZ + x, yf - 0.5, z), (XZ + x, yf + 2.0, z), 4.6, 32)   # ressalto do anel interno
        bx, bz = RODAS_Z[2]; m -= cil((XZ + bx, yp - 1, bz - zv.EXC), (XZ + bx, yf + 1, bz - zv.EXC), 6.0 + zv.TOL["fdm"]["bucha"], 64)
    else:
        m = caixa((XZ - 25.4, yp, -46), (XZ + 25.4, yf, 25.4))   # placa vertical (carro + porca)
    m += caixa((150.6, yp, 25.4), (160, yf, 42))             # alma
    m += caixa((41, yp, 32), (160, -31, 42)) + caixa((41, yp, 32), (102, 28, 42))   # braco horizontal sob a mesa (ate x=102: o furo M3 em x=99.1 nao estoura a borda)
    m += caixa((60, yp, 12), (130 if GUIAZ == "v" else 148, -31, 32))   # nervura (curta: roldana de dentro passa); desce ate a face da placa: imprime deitado nela
    if GUIAZ != "v":
        for dx in (-CARRO_FX, CARRO_FX):                      # carro Z: furos ao longo de Y
            for dz in (-CARRO_FY, CARRO_FY): m -= cil((XZ + dx, yp - 1, dz), (XZ + dx, yf + 1, dz), 1.7, 24)
    for dx in (-20.64, 20.64):                                # suporte da mesa (furos dos carros Y da Mulbot, ampliados); gota: imprime com +Y pra cima
        for dy in (-17.46, 17.46): m -= semsup.gota(((69.45 + dx) * EM, dy * EM, 31), ((69.45 + dx) * EM, dy * EM, 43), 1.7, (0, 1, 0), 24)
    if GUIAZ != "v":
        _Fz = R4(RZ, (XZ, YZB, ZZT)) @ Tcarro(ZZT)            # alivio p/ as tampas do carro Z
        for _T in (_Fz @ T1c, _Fz @ T2c):
            _m = mesh("DL1-03-02").copy(); _m.apply_transform(_T); _b = _m.bounds
            m -= caixa(_b[0] - 0.6, _b[1] + 0.6)
    from asm import world_holes                               # furos da porca Z
    Tpz = R4(RZ, (XZ, YZB, ZZT)) @ tr((0, ZZT, 0)) @ np.array(Fm["porca"])
    for a_, b2, d_ in world_holes("DL1-04-06", Tpz, dmax=4):
        a_ = np.array(a_); b2 = np.array(b2); u = (b2 - a_) / np.linalg.norm(b2 - a_)
        if abs(u[1]) > 0.9: m -= cil((a_[0], -60, a_[2]), (a_[0], -40, a_[2]), 1.7, 24)
    return m
bm = braco_mesa()
reg("bracoMesa_D", bm, "verm", "mesa"); reg("bracoMesa_E", espelhaX(bm), "verm", "mesa")
if GUIAZ == "v":
    _rp = zv.roldana_resina(partes=True)          # mesma roldana de resina do X/Y (pontes ja quebradas)
    salva(_rp["roda"] + _rp["pista"], "rodaZ"); salva(_rp["roletes"], "rodaZ_roletes")
    yp_, yf_ = YZB - CARRO_TOPO - 9.5, YZB - CARRO_TOPO
    Rw = np.column_stack([[1, 0, 0], [0, 0, -1], [0, 1, 0]])          # eixo da roldana (z local) -> +Y
    Rb = np.column_stack([[0, 0, 1], [1, 0, 0], [0, 1, 0]])           # bucha: excentricidade (x local) -> +Z
    for lado, sx in (("D", 1), ("E", -1)):
        for k, (x, z) in enumerate(RODAS_Z):
            X = sx * (XZ + x); Tw = QT["mesa"] @ R4(Rw, (X, YW, z))
            add(f"rodaZ_{lado}{k}", f"{DER}/rodaZ.stl", Tw, "verm"); add(f"rodaZ_{lado}{k}_roletes", f"{DER}/rodaZ_roletes.stl", Tw, "cinza")
            if k < 2:      # fixas: M6 da frente, porca atras do anel interno
                junta_passante(["bracoMesa_" + lado], (X, yp_, z), (0, 1, 0), 9.5 + 2.0 + 2 * zv.HW, d=6, q="mesa")
            else:          # excentrica: bucha impressa com sextavado na frente da placa
                salva(zv.bucha(11.5), "buchaZ")
                add(f"buchaZ_{lado}", f"{DER}/buchaZ.stl", QT["mesa"] @ R4(Rb, (X, yp_, z - zv.EXC)), "latao")
                junta_passante([], (X, yp_ - 4.0, z), (0, 1, 0), 4.0 + 11.5 + 2 * zv.HW, d=6, q="mesa")

# ================= mesa da Mulbot (vidro flutuante, presilhas, molas)
dM = tr((0, 0, ZVIDRO - (REF["ZVID"] + 3.3)))
PRESILHA = os.environ.get("PRESILHA", "disco")   # disco = botao excentrico serrilhado | baixa = aba chata giratoria | gancho = DL1-03-07 original
def suporte_mesa_110():
    fn = f"{DER}/DL1-03-04_110.stl"
    if not os.path.exists(fn):
        p, t, c = RI["suporteMesa"]; m = mesh(p).copy(); m.apply_transform(t); m.apply_transform(np.diag([EM, EM, 1, 1])); m.export(fn)
    return fn
add("mesa_suporteMesa", suporte_mesa_110(), dM, "verm")
add("mesa_vidro", f"{VT}/vidro.stl", np.diag([VID / 203.2, VID / 203.2, 1, 1]) @ tr((0, 0, ZVIDRO - 3.3)), "vidro")
for n in RI:
    if n.split("_")[0] in ("knob", "mola", "localizador", "presilha", "porcaPresilha"):
        p, t, c = RI[n]; k = int(n.split("_")[1]); sx, sy = ((1, -1), (1, 1), (-1, 1), (-1, -1))[k]
        if n.startswith("presilha_") and PRESILHA != "gancho": p = f"{DER}/presilha_{PRESILHA}.stl"   # scripts/presilha_mesa.py
        add("mesa_" + n, p, tr((sx * 92.3 * (EM - 1), sy * 92.3 * (EM - 1), 0)) @ dM @ t, c)

# ================= CoreXY: polias, motores, correias
GI = {"A_D": (XI, YS + RP, ZA), "B_D": (XI, YS - RP, ZB), "A_E": (-XI, YS - RP, ZA), "B_E": (-XI, YS + RP, ZB)}
FI = {"A_D": (XM, YF + RP, ZA), "B_D": (XI, YF + RP, ZB), "A_E": (-XI, YF + RP, ZA), "B_E": (-XM, YF + RP, ZB)}
for D, nm in ((GI, "loucaPortico_"), (FI, "loucaFrente_")):
    for k, c in D.items():
        polia_louca(nm + k, c, Linf=LST_PL if k[0] == "B" else LST_PM, Lsup=LST_PM if k[0] == "B" else LST_PL)
RMOT = np.column_stack([[1, 0, 0], [0, -1, 0], [0, 0, -1]])     # eixo do motor para baixo (corpo em cima)
motor("motorA", tr((XM, YM, ZA - POLIA_FACE)))
motor("motorB", R4(RMOT, (-XM, YM, ZB + POLIA_FACE)))
# pontas: rabo da correia (dentro da torre) -> volta no pino -> sai pelo lado
seqA = [((XC + 26, YS - 2 * RO), 0, 1), ((XC + PINX, YS - RO), RO, -1), (GI["A_D"][:2], RP, 1), ((XM, YM), RP, -1), (FI["A_D"][:2], RP, -1),
        (FI["A_E"][:2], RP, -1), (GI["A_E"][:2], RP, -1), ((XC - PINX, YS - RO), RO, -1), ((XC - 26, YS - 2 * RO), 0, 1)]
seqB = [((XC - 26, YS - 2 * RO), 0, 1), ((XC - PINX, YS - RO), RO, 1), (GI["B_E"][:2], RP, -1), ((-XM, YM), RP, 1), (FI["B_E"][:2], RP, 1),
        (FI["B_D"][:2], RP, 1), (GI["B_D"][:2], RP, 1), ((XC + PINX, YS - RO), RO, 1), ((XC + 26, YS - 2 * RO), 0, 1)]
COMP_CORREIA = {}
for nome, seq, z in (("correiaA", seqA, ZA), ("correiaB", seqB, ZB)):
    m, L = correia(seq, z); fn = f"{DER}/{nome}.stl"; m.export(fn); add(nome, fn, np.eye(4), "verm"); COMP_CORREIA[nome] = L

# ================= acessorios da Mulbot (display, extrusora EZR, caixa RAMPS, fonte, pes)
def grupo_mulbot(nomes, T, pref=""):
    for n in nomes:
        p, t, c = RI[n]; add(pref + n, p, T @ t, c)
grupo_mulbot(["displayBase", "displayTampa", "lcd_placa", "lcd_tela", "lcd_moldura", "botaoReset", "knobDisplay", "roboDisplay"],
             tr((0, YFR0 - (-156.6) - 0.5, 0)))
grupo_mulbot(["caixaRAMPS", "portaRAMPS", "roboGrande", "mega", "ramps_pcb", "ramps_comp"], tr((0, YFR1 - 117.66, 0)))
grupo_mulbot(["fonte", "protecaoFonte", "tomadaIEC"], tr((0, YFR1 - 117.66, 0)))
TEX = tr((208.75, YFR1 + 14 - 117.66, (ZBASE + 20) - 334.1))
EZR = ["ezr_corpo", "motorE", "motorE_corpo", "roboExtrusora"]
if EXTRUSORA == "bowden":
    grupo_mulbot(["suporteExtrusora"] + EZR, TEX)
else:
    # ================= extrusora direta: EZR + motor em cima da torre de presilhas, motor para tras (sobre o trilho X)
    # EZR (modelo vitaminas.py): filamento em x=-8, z=12, ao longo de y; saida no lado -y. Aqui: x->-X, y->+Z (saida p/ baixo), z->+Y
    ZPE = ZTP + 6.0                                    # topo do pe do suporte = fundo da EZR
    OE = np.array([-8.0, D_HOT - 12.0, ZPE + 21.0])    # origem da EZR (quadro do carro): filamento cai em (0, D_HOT)
    TE = R4(np.column_stack([[-1, 0, 0], [0, 0, 1], [0, 1, 0]]), OE)
    TEo = RI["ezr_corpo"][1]
    for n in EZR[:3]:                                  # roboExtrusora (enfeite do suporte antigo do quadro) sai
        p, t, c = RI[n]; add(n, p, QT["carro"] @ TE @ np.linalg.inv(TEo) @ t, c)
    def suporte_direta():
        yp = OE[1]                                     # face da placa da EZR (lado oposto ao motor)
        m = caixa((-30, yp - 6, ZTP), (30, -19, ZPE))                              # pe: apoia no topo da torre
        m += caixa((OE[0] - 21, yp - 6, ZTP), (OE[0] + 21, yp, OE[2] + 21))        # placa vertical (padrao NEMA17)
        for a in (-15.5, 15.5):
            for b in (-15.5, 15.5):                                                # M3x35: placa + EZR + motor
                m -= cil((OE[0] - a, yp - 7, OE[2] + b), (OE[0] - a, yp + 1, OE[2] + b), 1.7, 24)
        m -= furo_v(0, D_HOT, ZTP - 1, ZPE + 1, 4.4)                              # tubo PTFE ate o hotend
        for s in (-1, 1):                                                          # 2x M3x12 nos insertos da torre
            m -= furo_v(s * XI3, YI3, ZTP - 1, ZPE + 1, 3.4); m -= furo_v(s * XI3, YI3, ZTP + 2.5, ZPE + 1, 6.2)
        return m
    reg("suporteExtrusoraDireta", suporte_direta(), "verm", "carro")
for k, (x, y) in enumerate(((XR, YFR0 + 12), (-XR, YFR0 + 12), (XR, 0.0), (-XR, 0.0), (XR, YFR1 - 12), (-XR, YFR1 - 12))):
    add(f"pe_{k}", "DL1-01-08", place(rot("X", "-Y", "-Z"), (-58.32, 7.1, 0), (x, y, 0)), "verm")
from correia import tubo
_ht = np.array([XC, YG + D_HOT, ZBICO + 62.5])
if EXTRUSORA == "bowden":
    _ez = (TEX @ np.r_[-188.24 - 12, 146.61 - 8, 346.84 - 15.5 + 30, 1])[:3]
    _bt = tubo([_ez, _ez + [0, 0, 60], (_ez[0] * 0.5 + _ht[0] * 0.5, (_ez[1] + _ht[1]) / 2, ZTOP + 90), _ht + [0, 0, 70], _ht + [0, 0, 20], _ht + [0, 0, 1]], r=2.0)
    _bt.export(f"{DER}/bowden.stl"); add("bowden", f"{DER}/bowden.stl", np.eye(4), "azul")
else:   # PTFE curto: saida da EZR -> topo do hotend
    add("bowden", salva(cil((0, D_HOT, ZBICO + 62.5 + 1), (0, D_HOT, ZPE), 2.0, 24), "bowden_direta"), QT["carro"], "azul")
# ================= fins de curso (modelos Mulbot: placa + chave)
def fim_curso(nome, R, p):
    add(nome + "_pcb", f"{VT}/endstop_pcb.stl", R4(R, p), "verm"); add(nome, f"{VT}/endstop_chave.stl", R4(R, p), "preto")
# X: na face de dentro da parede do suporte do portico esquerdo, acima da aba; o braco do carro X aperta com XC = -101.5
fim_curso("fimCursoX", rot("Y", "Z", "X"), (-145.0, YG + 2.0, sum(ZBR) / 2))
# Y: na parede de tras da torre de tras esquerda (em pe, entre a porca da travessa e a borda); a lingueta da base do suporte aperta com YG = 152
fim_curso("fimCursoY", rot("Z", "-X", "-Y"), (-160.5, 208.0, ZBASE + TPL / 2))
# Z: embaixo do trilho Y esquerdo, o braco da mesa aperta no topo do curso
fim_curso("fimCursoZ", rot("X", "-Y", "-Z"), (-176.0, YZB - CARRO_TOPO - 4.74, Z0))

# ================= esteira porta-cabos da cabeca (scripts/esteira.py; ESTEIRA=0 volta o umbilical pela travessa de tras)
ESTEIRA = os.environ.get("ESTEIRA", "1") == "1"
if ESTEIRA:
    import esteira; esteira.aplica(globals())
# ================= quadro oco: passagem de cabos + menos filamento (scripts/cabos.py; CABOS=0 desliga)
if os.environ.get("CABOS", "1") == "1":
    import cabos; cabos.aplica(globals())
# ================= sem suporte: bico de 45 graus nos furos deitados (na posicao de impressao de cada peca, scripts/semsup.py)
import semsup
from juntas import GOTAS
print("sem suporte: furos em gota", semsup.aplica_gotas(PEC, GOTAS, FUROS_DESENHO))
for _d in PEC.values(): _d["m"] = semsup.limpa(_d["m"])

# ================= salva as pecas novas e os fixadores
for n, d in PEC.items():
    add(n, salva(d["m"], n), QT[d["q"]], d["cor"])
for n, f, T, c, q in FIX:
    add("fix_" + n, f, QT[q] @ T, c)

if __name__ == "__main__":
    a = sys.argv[1:]
    for k, v in COMP_CORREIA.items(): print(f"{k}: {v:.0f} mm")
    fn = export("/home/lucas/corexy/out/cxy.json", sem=("esfera",) if "semesf" in a else ())
    print("export", fn, len(P), "| pecas novas:", len(PEC), "| fixadores:", len(FIX))
