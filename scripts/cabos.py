# Passagem de cabos por dentro do quadro + economia de filamento: barras ocas (parede W), anel de parede em volta
# de cada furo de junta (juntas.FUROS) e furos de passagem entre pecas. Tudo converge no poste de tras esquerdo,
# colado na janela de baixo da caixa da RAMPS (que ja existe na peca da Mulbot).
# Rotas: base (motores Z, fonte) -> anel das bases -> posteTras_E -> RAMPS
#        display -> baseFrente -> baseLatF_E -> posteFrente_E -> alma do trilhoY_E (+ fim de curso Z) -> posteTras_E
#        motor A -> parede da torreTras_D -> travTras (+ entrada do cabo da cabeca no meio) -> torreTras_E (+ motor B, fim de curso Y) -> posteTras_E
# Chamado pelo cxy.py antes de salvar as pecas (CABOS=0 desliga). Conferencia: scripts/cabos_check.py
import json, numpy as np, manifold3d as mf
from base import caixa, cil, salva, Tm, M, mesh, DER, P as ITENS
from juntas import PEC, FUROS, EMENDAS
import semsup

W = 2.0          # parede das barras ocas (5 perimetros de 0.4)
WB = 2.0         # anel de parede em volta de furo de parafuso / porca-barril
SEPTO = 1.5      # parede que cada metade de uma emenda ganha na face de contato (dentro da cavidade)
def bx(a, b): return caixa(a, b)
def esp(m): return m.mirror([1, 0, 0])
def cx(a, b): return (np.array(a, float), np.array(b, float))            # caixa guardada como cantos (o telhado depende da peca)
def espc(c): a, b = c; return (np.array([-b[0], a[1], a[2]]), np.array([-a[0], b[1], b[2]]))
def uniao(ms): return mf.Manifold.batch_boolean(ms, mf.OpType.Add)

def filhos(nome):
    """peca registrada -> pedacos depois das emendas (posteFrente_D -> Inf/Sup, baseFrente -> _E/_D)"""
    if "_" in nome:
        b, l = nome.rsplit("_", 1); cand = (nome, f"{b}Inf_{l}", f"{b}Sup_{l}")
    else:
        cand = (nome, nome + "_E", nome + "_D")
    return [k for k in cand if k in PEC]

def aplica(G):
    XP0, XP1, YFR0, YFR1 = G["XP0"], G["XP1"], G["YFR0"], G["YFR1"]
    YY0, YY1, ZBASE, Z0, XR, XZ = G["YY0"], G["YY1"], G["ZBASE"], G["Z0"], G["XR"], G["XZ"]
    ZTOPO_POSTE_T = Z0 + G["H_TRILHO"]
    zv = G["zv"]; YFUSO = G["YFUSO"]
    vol0 = sum(PEC[k]["m"].volume() for k in PEC)

    def continua(p0, p1, r):
        """raio do furo coaxial mais fino que segue depois de p1 (escareado -> furo do parafuso), ou None"""
        u = (p1 - p0) / np.linalg.norm(p1 - p0)
        for q0, q1, rq in FUROS:
            v = q1 - q0; L = np.linalg.norm(v); v = v / L
            if rq >= r or np.linalg.norm(np.cross(u, v)) > 0.01: continue
            t = (p1 - q0) @ v
            if -0.5 < t < L - 1 and np.linalg.norm(np.cross(p1 - q0, v)) < 0.5: return rq
        return None
    def anel(p0, p1, r, up):
        u = (p1 - p0) / np.linalg.norm(p1 - p0)
        rc = continua(p0, p1, r)
        if rc is not None:      # escareado: anel passa WB do assento e afunila a 45 graus ate o anel do parafuso (sem degrau em balanco)
            fim = p1 + u * WB
            m = semsup.quilha(p0 - u * WB, fim, r + WB, up, 32) + cil(fim, fim + u * (r - rc), r + WB, 32, r1=rc + WB)
            return m
        if r > 5.5:             # porca-barril / furo grosso: anel inteiro com sobra
            return semsup.quilha(p0 - u * WB, p1 + u * WB, r + WB, up, 32)
        # furo de parafuso cego: o anel para logo depois da porca-barril que ele atravessa (a sobra ficava em balanco no vazio);
        # o fim do furo (folga da ponta do parafuso) fica aberto pra cavidade
        fim = p1
        for q0, q1, rq in FUROS:
            if rq <= r or abs((q1 - q0) @ u) > 1e-6 * np.linalg.norm(q1 - q0): continue
            v = (q1 - q0) / np.linalg.norm(q1 - q0); C = q0 + v * ((p1 - q0) @ v)       # eixo da barril mais perto do fim do furo
            t = (C - p0) @ u
            if np.linalg.norm(np.cross(C - p0, u)) < 1.0 and 0 < (p1 - p0) @ u - t < 12: fim = p0 + u * min((p1 - p0) @ u, t + 5.0)
        return semsup.quilha(p0 - u * WB, fim, r + WB, up, 32)
    _an = {}
    def aneis_de(peca, caixas):
        """aneis de parede dos furos que cruzam as caixas (cavidades/passagens) desta peca, com a quilha na impressao dela"""
        lo = np.min([c[0] for c in caixas], 0) - 12; hi = np.max([c[1] for c in caixas], 0) + 12
        up = semsup.cima(peca); sel = []
        for p0, p1, r in FUROS:
            a, b = np.minimum(p0, p1) - r, np.maximum(p0, p1) + r
            if np.all(b >= lo) and np.all(a <= hi): sel.append(anel(p0, p1, r, up))
        return uniao(sel) if sel else None
    def vazio(peca, caixas):
        """cavidade (uniao das caixas com telhado de 45 graus na impressao da peca) menos os aneis"""
        up = semsup.cima(peca)
        for _n, nA, nB, ax, p, Lp, t, ct in EMENDAS:              # septo de SEPTO na face da emenda: na sobreposicao a caixa
            if peca not in (nA, nB): continue                      # acaba antes da face (e ganha o telhado proprio)
            nov = []
            for a, b in caixas:
                z0, z1 = p - Lp / 2 - 1, p + Lp / 2 + 1
                for q0, q1, lap in ((a[ax], min(b[ax], z0), False), (max(a[ax], z0), min(b[ax], z1), True), (max(a[ax], z1), b[ax], False)):
                    if q1 - q0 < 0.01: continue
                    aa, bb = a.copy(), b.copy(); aa[ax], bb[ax] = q0, q1
                    if lap:
                        if peca == nA: bb[t] = min(bb[t], ct - SEPTO)
                        else: aa[t] = max(aa[t], ct + SEPTO)
                        if bb[t] - aa[t] < 0.5: continue
                    nov.append((aa, bb))
            caixas = nov
        # poste da frente: teto de 1 agua alta do lado de dentro (x perto de 0): o cabo passa por ali, acima dos escareados da viga Y
        alto = np.zeros(3) if peca.startswith("posteFrente") else None
        c = uniao([semsup.telhado(a, b, up, alto=alto) for a, b in caixas])
        an = aneis_de(peca, caixas)
        return c - an if an is not None else c

    # ---------- torre de tras: parede de tras desce ate y=198 entre o poste e a placa (ponte p/ o cabo descer sem cruzar o M10 torre-poste)
    ext = bx((158, 200, ZTOPO_POSTE_T), (206, 208, ZTOPO_POSTE_T + 17))   # y>=200 e z<=440: a lingueta do suporte do portico passa em y 198.6, z>440.6
    # sem suporte (torre imprime de cabeca pra baixo): rampa de 45 graus em cima da ponte (o topo dela era balanco de 8 mm);
    # fica em y >= 200, a lingueta do suporte do portico passa em y <= 198.6
    cs = mf.CrossSection([[(208.0, ZTOPO_POSTE_T + 17 - 0.01), (208.0, ZTOPO_POSTE_T + 25), (200.0, ZTOPO_POSTE_T + 17 - 0.01)]])   # (y, z)
    ar_ = sum(p[0] * q[1] - q[0] * p[1] for p, q in zip(cs.to_polygons()[0], np.roll(cs.to_polygons()[0], -1, 0)))
    rampa = cs.extrude(48).transform([[0, 0, 1, 158], [1, 0, 0, 0], [0, 1, 0, 0]])                  # (y, z, x) -> (x, y, z), destro
    ext += rampa
    PEC["torreTras_D"]["m"] += ext; PEC["torreTras_E"]["m"] += esp(ext)

    # ---------- cavidades (lado D; E = espelho). Barras: seccao encolhida W de cada lado
    OCO = {}                                                         # nome -> [caixas (cantos)]
    def oco(nome, partes, espelha=True):
        OCO[nome + ("_D" if espelha else "")] = partes
        if espelha: OCO[nome + "_E"] = [espc(c) for c in partes]
    a, b_ = XP0 + W, XP1 - W
    oco("baseLatF", [cx((a, YFR0 + W, W), (b_, -126 - W, 30 - W)), cx((a, -126 - W - 2, 15 + W), (b_, -96 - W, 30 - W))])   # lingueta so em z>15
    oco("baseLatT", [cx((a, 86 + W, W), (b_, YFR1 - W, 30 - W)), cx((a, 46 + W, 15 + W), (b_, 86 + W + 2, 30 - W))])
    oco("posteFrente", [cx((a, YFR0 + W, 30 + W), (b_, YY0 - W, ZBASE - W))])
    oco("posteTras", [cx((a, YY1 + W, 30 + W), (b_, YFR1 - W, ZTOPO_POSTE_T - W))])
    oco("baseFrente", [cx((-XP0 + W, YFR0 + W, W), (XP0 - W, YFR0 + 30 - W, 30 - W))], False)
    oco("baseTras", [cx((-XP0 + W, YFR1 - 30 + W, W), (XP0 - W, YFR1 - W, 30 - W))], False)
    oco("travFrente", [cx((-200 + W, YFR0 - 14 + W, ZBASE + W), (200 - W, YFR0 - W, ZBASE + 60 - W))], False)
    oco("travTras", [cx((-206 + W, YFR1 + W, ZBASE + W), (206 - W, YFR1 + 14 - W, ZBASE + 50 - W))], False)
    zalma = G["ZWY"] - zv.BK - W                                     # alma do trilho Y (abaixo da aba com V)
    oco("trilhoY", [cx((XR - 9.525 + W, YY0 + W, Z0 + W), (XR + 9.525 - W, YY1 - W, zalma))])
    oco("baseZ", [cx((XZ - 13, YFUSO + 21.6 - 0.1, 4), (XZ + 13, 46 - W, 30))])   # atras do alojamento do motor Z (abre nele)
    for lado, zp0 in (("D", G["ZA"] - G["POLIA_FACE"]), ("E", G["ZB"] + G["POLIA_FACE"] - 6.0)):
        # a caixa da parede de tras comeca 5 mm acima da ponte: imprimindo de cabeca pra baixo, os 2 tetos ficam separados (cada um < 10 mm)
        m = [cx((158 + W, 208 + W, ZTOPO_POSTE_T + W + 5), (206 - W, 222 - W, zp0)), cx((158 + W, 201.2, ZTOPO_POSTE_T + W), (206 - W, 212, ZTOPO_POSTE_T + 17 - W))]   # parede da frente da ponte 1.2 (so fecha)
        OCO["torreTras_" + lado] = m if lado == "D" else [espc(c) for c in m]

    # ---------- furos de passagem (lado D; espelhados quando o nome tem _D)
    PAS = []
    def pas(m, partes, espelha=True):
        PAS.append((m, partes))
        if espelha: PAS.append((espc(m), [p.replace("_D", "_E") for p in partes]))
    yfz = G["YZB"] - G["CARRO_TOPO"] - 4.74                         # fim de curso Z (embaixo do trilho Y esquerdo)
    pas(cx((XP0 + 2.5, 40, 17), (XP1 - 2.5, 52, 28)), ["baseZ_D", "baseLatT_D"])                 # base Z -> base lateral de tras
    pas(cx((164, 210.5, 22.9), (188, 218.5, 34)), ["baseLatT_D", "posteTras_D"])                 # base lateral -> poste de tras
    pas(cx((150, 195.5, 8), (166, 202, 23)), ["baseLatT_D", "baseTras"])                        # base lateral -> base de tras
    pas(cx((152, -160.6, 10), (166, -156.3, 25)), ["baseFrente", "baseLatF_D"])                 # base da frente -> base lateral
    pas(cx((164, -160.6, 23), (188, -156, 36)), ["baseLatF_D", "posteFrente_D"])                 # base lateral -> poste da frente
    pas(cx((170, YY0 - 4, 408), (182, YY0 + 4, 418)), ["posteFrente_D", "trilhoY_D"])            # poste da frente -> alma do trilho Y
    pas(cx((170, YY1 - 4, 406), (182, YY1 + 6, 418)), ["trilhoY_D", "posteTras_D"])              # alma do trilho Y -> poste de tras
    pas(cx((164, 202.6, ZTOPO_POSTE_T - 5), (188, 207.6, ZTOPO_POSTE_T + 4)), ["posteTras_D", "torreTras_D"])   # poste -> torre (para 1.4 antes da parede da frente: teto de ponte curta na impressao)
    pas(cx((181.5, 218, 444), (189.5, YFR1 + 4, 458)), ["torreTras_D", "travTras"])             # torre -> travessa de tras
    pas(cx((-180, yfz - 5, Z0 - 3), (-172, yfz + 5, Z0 + 5)), ["trilhoY_E"], False)              # fim de curso Z
    pas(cx((-178, YFR1 - 4, 60), (-164, YFR1 + 2, 80)), ["posteTras_E"], False)                  # -> janela de baixo da caixa da RAMPS
    pas(cx((164, YFR1 - 4, 60), (175, YFR1 + 2, 120)), ["posteTras_D"], False)                   # fonte (protecao aberta do lado do quadro)
    pas(cx((184, 205, 470), (196, 211, 482)), ["torreTras_D"], False)                            # motor A (corpo embaixo da placa)
    pas(cx((-190, 211, G["ZB"] + G["POLIA_FACE"] - 8), (-178, 219, G["ZB"] + G["POLIA_FACE"] + 1)), ["torreTras_E"], False)  # motor B (atravessa a placa)
    pas(cx((-166, 205, 438), (-160, 211, 452)), ["torreTras_E"], False)                         # fim de curso Y
    if G.get("ESTEIRA"):    # cabo da cabeca (esteira Y): entra pela parede de fora da torre de tras D, acima do M6 da travessa
        pas(cx((200, 210.5, 464), (208, 219.5, 474)), ["torreTras_D"], False)
    else:                   # cabo da cabeca (umbilical): a esquerda da emenda (M6 da emenda fecham o canal em x=+-15)
        pas(cx((-46, YFR1 + W + 0.5, ZBASE + 45), (-34, YFR1 + 14 - W - 0.5, ZBASE + 52)), ["travTras"], False)
    disp = cx((-10, YFR0 - 4, 8), (10, YFR0 + 4, 22))
    pas(disp, ["baseFrente"], False)                                                             # display

    cortes = []
    for nome, cav in OCO.items():
        for f in filhos(nome):
            c = vazio(f, cav); cortes.append(c); PEC[f]["m"] -= c
    def corredor(f, m):
        """caixa da passagem esticada (no eixo mais fino dela) ate o meio da cavidade da peca f que ela toca"""
        a, b = m; cav = None
        for nome, cs in OCO.items():
            if f in filhos(nome): cav = cs
        if not cav: return [m]
        k = int(np.argmin(b - a)); out = [m]
        for ca, cb in cav:
            o = [i for i in range(3) if i != k]
            if any(b[i] <= ca[i] or a[i] >= cb[i] for i in o) or b[k] < ca[k] - 3 or a[k] > cb[k] + 3: continue
            mid = (ca[k] + cb[k]) / 2; aa, bb = np.maximum(a, ca), np.minimum(b, cb)
            aa[k], bb[k] = min(a[k], mid), max(b[k], mid)
            aa[k], bb[k] = max(aa[k], ca[k]), min(bb[k], cb[k])
            if np.all(bb - aa > 0.5): out.append((aa, bb))
        return out
    for m, partes in PAS:
        for p in partes:
            for f in filhos(p):
                c = vazio(f, corredor(f, m)); cortes.append(c); PEC[f]["m"] -= c
    # display (peca da Mulbot): mesma janela na parede de tras da base do display
    for i, (n, peca, T, cor) in enumerate(ITENS):
        if n == "displayBase":
            mm = mesh(peca).copy(); mm.apply_transform(T); d = M(mm) - vazio("displayBase", [disp])
            fn = salva(d.transform(np.linalg.inv(T)[:3].tolist()), "DL1-05-01_cabo"); ITENS[i] = (n, fn, T, cor)
    # chave do fim de curso Y (em pe na frente da torre de tras esquerda): a ponte/rampa da torre nao pode ocupar o lugar dela
    PEC["torreTras_E"]["m"] -= caixa((-169.0, 194.0, ZTOPO_POSTE_T - 0.5), (-152.0, 208.0, ZTOPO_POSTE_T + 42))
    ar = uniao(cortes); salva(ar, "cabos_ar")
    pontos = {"RAMPS": (-171, YFR1 - 1, 70), "motorZ_E": (-176, YFUSO + 21.6 + 2, 15), "motorZ_D": (176, YFUSO + 21.6 + 2, 15),
              "fonte": (169.5, YFR1 - 1, 100), "display": (0, YFR0 + 1, 15), "fimCursoZ": (-176, yfz, Z0 + 1),
              "fimCursoY": (-163, 209, 445), "motorA": (190, 209, 476), "motorB": (-184, 215, G["ZB"] + G["POLIA_FACE"] - 3),
              **({"cabeca (esteira)": (205, 215, 469)} if G.get("ESTEIRA") else {"cabeca (umbilical)": (-40, YFR1 + 7, ZBASE + 48)})}
    json.dump(pontos, open("/home/lucas/corexy/out/cabos_pontos.json", "w"), indent=1)
    vol1 = sum(PEC[k]["m"].volume() for k in PEC)
    print(f"cabos: {len(OCO)} cavidades, {len(PAS)} passagens | pecas impressas novas {vol0 / 1000:.0f} -> {vol1 / 1000:.0f} cm3 (-{(vol0 - vol1) / 1000:.0f})")
