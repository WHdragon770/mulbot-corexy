# Passagem de cabos por dentro do quadro + economia de filamento: barras ocas (parede W), anel de parede em volta
# de cada furo de junta (juntas.FUROS) e furos de passagem entre pecas. Tudo converge no poste de tras esquerdo,
# colado na janela de baixo da caixa da RAMPS (que ja existe na peca da Mulbot).
# Rotas: base (motores Z, fonte) -> anel das bases -> posteTras_E -> RAMPS
#        display -> baseFrente -> baseLatF_E -> posteFrente_E -> alma do trilhoY_E (+ fim de curso Z) -> posteTras_E
#        motor A -> parede da torreTras_D -> travTras (+ entrada do cabo da cabeca no meio) -> torreTras_E (+ motor B, fim de curso Y) -> posteTras_E
# Chamado pelo cxy.py antes de salvar as pecas (CABOS=0 desliga). Conferencia: scripts/cabos_check.py
import json, numpy as np, manifold3d as mf
from base import caixa, cil, salva, Tm, M, mesh, DER, P as ITENS
from juntas import PEC, FUROS

W = 2.0          # parede das barras ocas (5 perimetros de 0.4)
WB = 2.0         # anel de parede em volta de furo de parafuso / porca-barril
def bx(a, b): return caixa(a, b)
def esp(m): return m.mirror([1, 0, 0])
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

    aneis = uniao([cil(p0 - (p1 - p0) / np.linalg.norm(p1 - p0) * WB, p1 + (p1 - p0) / np.linalg.norm(p1 - p0) * WB, r + WB, 32)
                   for p0, p1, r in FUROS])

    # ---------- torre de tras: parede de tras desce ate y=198 entre o poste e a placa (ponte p/ o cabo descer sem cruzar o M10 torre-poste)
    ext = bx((158, 200, ZTOPO_POSTE_T), (206, 208, ZTOPO_POSTE_T + 17))   # y>=200 e z<=440: a lingueta do suporte do portico passa em y 198.6, z>440.6
    PEC["torreTras_D"]["m"] += ext; PEC["torreTras_E"]["m"] += esp(ext)

    # ---------- cavidades (lado D; E = espelho). Barras: seccao encolhida W de cada lado
    OCO = {}
    def oco(nome, partes, espelha=True):
        m = uniao(partes); OCO[nome + ("_D" if espelha else "")] = m
        if espelha: OCO[nome + "_E"] = esp(m)
    a, b_ = XP0 + W, XP1 - W
    oco("baseLatF", [bx((a, YFR0 + W, W), (b_, -126 - W, 30 - W)), bx((a, -126 - W - 2, 15 + W), (b_, -96 - W, 30 - W))])   # lingueta so em z>15
    oco("baseLatT", [bx((a, 86 + W, W), (b_, YFR1 - W, 30 - W)), bx((a, 46 + W, 15 + W), (b_, 86 + W + 2, 30 - W))])
    oco("posteFrente", [bx((a, YFR0 + W, 30 + W), (b_, YY0 - W, ZBASE - W))])
    oco("posteTras", [bx((a, YY1 + W, 30 + W), (b_, YFR1 - W, ZTOPO_POSTE_T - W))])
    oco("baseFrente", [bx((-XP0 + W, YFR0 + W, W), (XP0 - W, YFR0 + 30 - W, 30 - W))], False)
    oco("baseTras", [bx((-XP0 + W, YFR1 - 30 + W, W), (XP0 - W, YFR1 - W, 30 - W))], False)
    oco("travFrente", [bx((-200 + W, YFR0 - 14 + W, ZBASE + W), (200 - W, YFR0 - W, ZBASE + 60 - W))], False)
    oco("travTras", [bx((-206 + W, YFR1 + W, ZBASE + W), (206 - W, YFR1 + 14 - W, ZBASE + 50 - W))], False)
    zalma = G["ZWY"] - zv.BK - W                                     # alma do trilho Y (abaixo da aba com V)
    oco("trilhoY", [bx((XR - 9.525 + W, YY0 + W, Z0 + W), (XR + 9.525 - W, YY1 - W, zalma))])
    oco("baseZ", [bx((XZ - 13, YFUSO + 21.6 - 0.1, 4), (XZ + 13, 46 - W, 30))])   # atras do alojamento do motor Z (abre nele)
    for lado, zp0 in (("D", G["ZA"] - G["POLIA_FACE"]), ("E", G["ZB"] + G["POLIA_FACE"] - 6.0)):
        m = bx((158 + W, 208 + W, ZTOPO_POSTE_T + W), (206 - W, 222 - W, zp0)) + bx((158 + W, 201.2, ZTOPO_POSTE_T + W), (206 - W, 212, ZTOPO_POSTE_T + 17 - W))   # parede da frente da ponte 1.2 (so fecha)
        OCO["torreTras_" + lado] = m if lado == "D" else esp(m)

    # ---------- furos de passagem (lado D; espelhados quando o nome tem _D)
    PAS = []
    def pas(m, partes, espelha=True):
        PAS.append((m, partes))
        if espelha: PAS.append((esp(m), [p.replace("_D", "_E") for p in partes]))
    yfz = G["YZB"] - G["CARRO_TOPO"] - 4.74                         # fim de curso Z (embaixo do trilho Y esquerdo)
    pas(bx((XP0 + 2.5, 40, 17), (XP1 - 2.5, 52, 28)), ["baseZ_D", "baseLatT_D"])                 # base Z -> base lateral de tras
    pas(bx((164, 210.5, 22.9), (188, 218.5, 34)), ["baseLatT_D", "posteTras_D"])                 # base lateral -> poste de tras
    pas(bx((150, 195.5, 8), (166, 202, 23)), ["baseLatT_D", "baseTras"])                        # base lateral -> base de tras
    pas(bx((152, -160.6, 10), (166, -156.3, 25)), ["baseFrente", "baseLatF_D"])                 # base da frente -> base lateral
    pas(bx((164, -160.6, 23), (188, -156, 36)), ["baseLatF_D", "posteFrente_D"])                 # base lateral -> poste da frente
    pas(bx((170, YY0 - 4, 408), (182, YY0 + 4, 418)), ["posteFrente_D", "trilhoY_D"])            # poste da frente -> alma do trilho Y
    pas(bx((170, YY1 - 4, 406), (182, YY1 + 6, 418)), ["trilhoY_D", "posteTras_D"])              # alma do trilho Y -> poste de tras
    pas(bx((164, 201.2, ZTOPO_POSTE_T - 5), (188, 207.6, ZTOPO_POSTE_T + 4)), ["posteTras_D", "torreTras_D"])   # poste -> torre
    pas(bx((181.5, 218, 444), (189.5, YFR1 + 4, 458)), ["torreTras_D", "travTras"])             # torre -> travessa de tras
    pas(bx((-180, yfz - 5, Z0 - 3), (-172, yfz + 5, Z0 + 5)), ["trilhoY_E"], False)              # fim de curso Z
    pas(bx((-178, YFR1 - 4, 60), (-164, YFR1 + 2, 80)), ["posteTras_E"], False)                  # -> janela de baixo da caixa da RAMPS
    pas(bx((164, YFR1 - 4, 60), (175, YFR1 + 2, 120)), ["posteTras_D"], False)                   # fonte (protecao aberta do lado do quadro)
    pas(bx((184, 205, 470), (196, 211, 482)), ["torreTras_D"], False)                            # motor A (corpo embaixo da placa)
    pas(bx((-190, 211, G["ZB"] + G["POLIA_FACE"] - 8), (-178, 219, G["ZB"] + G["POLIA_FACE"] + 1)), ["torreTras_E"], False)  # motor B (atravessa a placa)
    pas(bx((-166, 205, 438), (-160, 211, 452)), ["torreTras_E"], False)                         # fim de curso Y
    pas(bx((-46, YFR1 + W + 0.5, ZBASE + 45), (-34, YFR1 + 14 - W - 0.5, ZBASE + 52)), ["travTras"], False)   # cabo da cabeca (umbilical): a esquerda da emenda (M6 da emenda fecham o canal em x=+-15)
    disp = bx((-10, YFR0 - 4, 8), (10, YFR0 + 4, 22))
    pas(disp, ["baseFrente"], False)                                                             # display

    cortes = []
    for nome, cav in OCO.items():
        c = cav - aneis; cortes.append(c)
        for f in filhos(nome): PEC[f]["m"] -= c
    for m, partes in PAS:
        c = m - aneis; cortes.append(c)
        for p in partes:
            for f in filhos(p): PEC[f]["m"] -= c
    # display (peca da Mulbot): mesma janela na parede de tras da base do display
    for i, (n, peca, T, cor) in enumerate(ITENS):
        if n == "displayBase":
            mm = mesh(peca).copy(); mm.apply_transform(T); d = M(mm) - (disp - aneis)
            fn = salva(d.transform(np.linalg.inv(T)[:3].tolist()), "DL1-05-01_cabo"); ITENS[i] = (n, fn, T, cor)
    ar = uniao(cortes); salva(ar, "cabos_ar")
    pontos = {"RAMPS": (-171, YFR1 - 1, 70), "motorZ_E": (-176, YFUSO + 21.6 + 2, 15), "motorZ_D": (176, YFUSO + 21.6 + 2, 15),
              "fonte": (169.5, YFR1 - 1, 100), "display": (0, YFR0 + 1, 15), "fimCursoZ": (-176, yfz, Z0 + 1),
              "fimCursoY": (-163, 209, 445), "motorA": (190, 209, 476), "motorB": (-184, 215, G["ZB"] + G["POLIA_FACE"] - 3),
              "cabeca (umbilical)": (-40, YFR1 + 7, ZBASE + 48)}
    json.dump(pontos, open("/home/lucas/corexy/out/cabos_pontos.json", "w"), indent=1)
    vol1 = sum(PEC[k]["m"].volume() for k in PEC)
    print(f"cabos: {len(OCO)} cavidades, {len(PAS)} passagens | pecas impressas novas {vol0 / 1000:.0f} -> {vol1 / 1000:.0f} cm3 (-{(vol0 - vol1) / 1000:.0f})")
