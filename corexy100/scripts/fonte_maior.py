# Fonte maior p/ mesa aquecida (MESA=220 ou 235): a RS-150-12 (150 W) nao segura mesa + motores + hotend.
#   MESA=220 -> 12 V 30 A (S-360-12) | MESA=235 -> 24 V 15 A (S-360-24). As duas: 215 x 115 x 50 mm.
# Mesmo lugar da RS-150 (atras do poste de tras direito, face +X alinhada), pe da fonte dentro de uma protecao nova
# (copo impresso no lugar da DL1-02-15, sem suporte: tomada IEC em pe na parede +X, passagem de cabos na -X, 2x M4 nas laterais da fonte)
# e modulo MOSFET da mesa (60 x 50) preso por fora na parede -X (o D8 da RAMPS so aguenta ~11 A).
import numpy as np, manifold3d as mf
from base import caixa, cil, salva, add, tr, R4, VT
import semsup
from juntas import reg

FL, FW, FH = 50.0, 115.0, 215.0           # fonte: x (espessura), y, z (de pe, bornes pra baixo)
X1 = 172.6                                 # face +X da fonte (= RS-150)
Y0 = 225.7; Z0F = 86.9                     # frente da fonte (atras da parede da protecao) e fundo
E, F, ZF = 3.0, 0.4, 44.0                  # parede, folga, fundo da protecao (4 mm abaixo da DL1-02-15: cabe a IEC em pe)
SOBE = 37.0                                # quanto a protecao abraca a fonte
MOS = (60.0, 50.0, 1.6, 22.0)              # modulo MOSFET: placa y, z, espessura, altura dos componentes (aprox.)

def aplica(G, tensao):
    x0, x1 = X1 - FL - F - E, X1 + F + E
    y0, y1 = Y0 - F - E, Y0 + FW + F + E
    zt = Z0F + SOBE
    add("fonte", salva(caixa((X1 - FL, Y0, Z0F), (X1, Y0 + FW, Z0F + FH)), f"fonte_s360_{tensao}"), np.eye(4), "alu")
    m = caixa((x0, y0, ZF), (x1, y1, zt)) - caixa((x0 + E, y0 + E, ZF + E), (x1 - E, y1 - E, zt + 1))
    # tomada IEC C14 em pe na parede +X (corpo 22 x 28), abaixo da fonte; topo do furo em telhado 45 (ponte 9) escondido pelo flange
    yi, zi = Y0 + 45.0, ZF + 26.0
    furo = caixa((x1 - E - 1, yi - 11.2, zi - 14.2), (x1 + 1, yi + 11.2, zi + 14.2))
    m -= mf.Manifold.batch_hull([furo, caixa((x1 - E - 1, yi - 4.5, zi), (x1 + 1, yi + 4.5, zi + 14.2 + 6.7))])
    add("tomadaIEC", f"{VT}/iec_c14.stl", R4(np.column_stack([[0, 0, 1], [0, -1, 0], [1, 0, 0]]), (x1, yi, zi)), "preto")
    # passagem dos cabos (RAMPS e mesa) na parede -X, embaixo do MOSFET (9 de largura: ponte)
    m -= caixa((x0 - 1, Y0 + 4, ZF + E + 1), (x0 + E + 1, Y0 + 13, ZF + E + 15))
    # 2x M4 nas laterais da fonte
    for x in (x0, x1 - E):
        m -= semsup.gota((x - 1, Y0 + FW / 2, Z0F + 18), (x + E + 1, Y0 + FW / 2, Z0F + 18), 2.2, (0, 0, 1), 24)
    # MOSFET: 4 colunas M3 (autoatarraxante) por fora da parede -X
    ym, zm = Y0 + 45.0, (ZF + zt) / 2
    for dy in (-26.0, 26.0):
        for dz in (-21.0, 21.0):
            c = caixa((x0 - 6, ym + dy - 3.5, zm + dz - 3.5), (x0 + 0.5, ym + dy + 3.5, zm + dz + 3.5))
            m += mf.Manifold.batch_hull([c, caixa((x0 - 0.01, ym + dy - 3.5, zm + dz - 9.5), (x0 + 0.5, ym + dy + 3.5, zm + dz))])   # 45 por baixo
            m -= semsup.gota((x0 + 1, ym + dy, zm + dz), (x0 - 7, ym + dy, zm + dz), 1.25, (0, 0, 1), 16)
    pl = caixa((x0 - 6 - MOS[2], ym - MOS[0] / 2, zm - MOS[1] / 2), (x0 - 6, ym + MOS[0] / 2, zm + MOS[1] / 2))
    comp = caixa((x0 - 6 - MOS[2] - MOS[3], ym - 20, zm - 15), (x0 - 6 - MOS[2], ym + 20, zm + 15))
    add("moduloMOSFET_pcb", salva(pl, "mosfet_pcb"), np.eye(4), "pcb")
    add("moduloMOSFET", salva(comp, "mosfet_comp"), np.eye(4), "preto")
    reg("protecaoFonte360", m, "azul")
