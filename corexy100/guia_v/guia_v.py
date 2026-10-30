# Exemplo: guia em V impressa + carro de 3 roldanas (625) com excentrico, pro eixo Z da CoreXY.
# Trilho corre em Z, pontas do V em +-X, espessura em Y. Gera STLs (montado, explodido, corte) p/ render.
import manifold3d as m3, numpy as np, trimesh, sys, os
from manifold3d import Manifold, CrossSection
OUT = os.path.expanduser("~/corexy/guia_v/stl"); L = 220; ZC = 110
TIP = 13.0          # meia-largura do V (ponta teorica)
XC = 23.5           # centro das roldanas (flanco da roldana encosta no flanco do trilho)
RG, RO, HG, HW = 10.5, 14.0, 3.5, 4.5   # raio fundo do canal, raio externo, altura do flanco, meia-largura roldana
EXC = 0.75          # excentricidade da bucha (ajuste de +-0,75 mm)

def box(x0, x1, y0, y1, z0, z1): return Manifold.cube([x1-x0, y1-y0, z1-z0]).translate([x0, y0, z0])
def cyl_y(r, y0, y1, x, z, n=64): return Manifold.cylinder(y1-y0, r, r, n).rotate([-90, 0, 0]).translate([x, y0, z])
def rev_y(prof, x, z, n=96):   # perfil (r, h) revolvido; eixo vira Y
    return CrossSection([prof]).revolve(n).rotate([-90, 0, 0]).translate([x, 0, z])

# trilho (faz parte do poste: uma peca so)
t = TIP - 0.5
sec = [(8.5, 6), (8.5, 4.5), (t, 0.5), (t, -0.5), (8.5, -4.5), (8.5, -6),
       (-8.5, -6), (-8.5, -4.5), (-t, -0.5), (-t, 0.5), (-8.5, 4.5), (-8.5, 6)]
trilho = CrossSection([sec[::-1]]).extrude(L)          # sec esta horario; inverte p/ area positiva
poste = trilho + box(-6, 6, 5.9, 14.1, 0, L) + box(-20, 20, 14, 54, -10, L + 10)

# roldana impressa (canal em V) e rolamento 625 (5x16x5)
perfil_rold = [(8.0, -HW), (RO, -HW), (RO, -HG), (RG, 0), (RO, HG), (RO, HW), (8.0, HW)]
def roldana(x, z): return rev_y(perfil_rold, x, z)
def rolamento(x, z): return cyl_y(8, -2.5, 2.5, x, z) - cyl_y(2.5, -3, 3, x, z)

# carro
PY0, PY1 = -13, -7
placa = box(-40, 40, PY0, PY1, ZC - 48, ZC + 48)
placa = placa + box(-16, 16, PY0 - 14, PY0, ZC - 30, ZC - 18)       # orelha p/ braco da mesa
placa -= cyl_y(2.65, PY0 - 15, PY0 + 1, -8, ZC - 24) + cyl_y(2.65, PY0 - 15, PY0 + 1, 8, ZC - 24)
placa -= cyl_y(7, -20, 0, 0, ZC + 22)                                 # passagem da porca do fuso / alivio
rodas = [(-XC, ZC - 32), (-XC, ZC + 32), (XC + 0.0, ZC)]
for x, z in rodas[:2]: placa -= cyl_y(2.65, PY0 - 1, PY1 + 1, x, z)
placa -= cyl_y(5.15, PY0 - 1, PY1 + 1, XC + EXC, ZC)                  # furo da bucha excentrica

def parafuso(x, z):   # M5: cabeca na frente da placa, porca nylock atras da roldana
    p = cyl_y(4.25, PY0 - 4, PY0, x, z) + cyl_y(2.5, PY0, HW + 6, x, z)
    porca = Manifold.cylinder(4, 4.6, 4.6, 6).rotate([-90, 0, 0]).translate([x, HW + 0.6, z])
    return p, porca
def espacador(x, z): return cyl_y(4.2, PY1, -HW, x, z) - cyl_y(2.6, PY1 - 1, -HW + 1, x, z)
def bucha(x, z):      # bucha excentrica impressa: sextavado 13 mm na frente, corpo D10 na placa, furo M5 deslocado
    sx = Manifold.cylinder(4, 7.5, 7.5, 6).rotate([-90, 0, 0]).translate([x + EXC, PY0 - 4, z])
    corpo = cyl_y(5.0, PY0, PY1, x + EXC, z) + cyl_y(4.2, PY1, -HW, x + EXC, z)
    return sx + corpo - cyl_y(2.6, PY0 - 5, 0, x, z)

grupos = {"poste": [poste], "placa": [placa], "roldana": [], "rolamento": [], "bucha": [], "parafuso": [], "porca": [], "espacador": []}
for i, (x, z) in enumerate(rodas):
    grupos["roldana"].append(roldana(x, z)); grupos["rolamento"].append(rolamento(x, z))
    p, n = parafuso(x, z); grupos["parafuso"].append(p); grupos["porca"].append(n)
    if i < 2: grupos["espacador"].append(espacador(x, z))
    else: grupos["bucha"].append(bucha(x - EXC * 0, z))

# checagem: roldana x trilho (tem que encostar, sem interferir)
for r in grupos["roldana"]:
    v = (r ^ trilho).volume(); print("interf roldana x trilho mm3:", round(v, 2))
    print("  encosto (roldana 0,2 mm pra dentro) mm3:", round((r.translate([0.2 if r.bounding_box()[0] < 0 else -0.2, 0, 0]) ^ trilho).volume(), 2))
print("interf placa x poste:", round((placa ^ poste).volume(), 2))

def salva(nome, mf, dy=0.0, dx=0.0, corte=None):
    if corte is not None: mf = mf ^ box(-200, 200, -200, 200, -50, corte)
    mf = mf.translate([dx, dy, 0])
    me = mf.to_mesh(); tm = trimesh.Trimesh(me.vert_properties[:, :3], me.tri_verts)
    if len(tm.faces): tm.export(f"{OUT}/{nome}.stl")

# explodido: tudo sai pra frente (-Y) na ordem de montagem
EXP = {"poste": 0, "porca": 60, "roldana": -55, "rolamento": -55, "espacador": -95, "placa": -130, "bucha": -175, "parafuso": -215}
for g, lst in grupos.items():
    u = Manifold.batch_boolean(lst, m3.OpType.Add) if len(lst) > 1 else lst[0]
    salva(f"mont_{g}", u); salva(f"exp_{g}", u, dy=EXP[g]); salva(f"corte_{g}", u, corte=ZC)
# chapas de impressao (roldana deitada) so pra referencia
salva("print_roldana", roldana(0, 0).rotate([90, 0, 0]))
salva("print_bucha", bucha(0, 0))
print("OK")
