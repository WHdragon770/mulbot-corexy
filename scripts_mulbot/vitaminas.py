# Modelos simplificados das pecas compradas (medidas de catalogo)
import numpy as np, trimesh, manifold3d as mf, os
OUT = "/home/lucas/mulbot/vit"
def M(t): return mf.Manifold(mf.Mesh(vert_properties=np.asarray(t.vertices, np.float32), tri_verts=np.asarray(t.faces, np.uint32)))
def T(m):
    g = m.to_mesh(); return trimesh.Trimesh(np.asarray(g.vert_properties)[:, :3], np.asarray(g.tri_verts), process=False)
def box(a, b):  # cantos
    a, b = np.minimum(a, b).astype(float), np.maximum(a, b).astype(float); return mf.Manifold.cube((b-a).tolist()).translate(a.tolist())
def cyl(r, h, p=(0,0,0), n=48, r2=None):
    return mf.Manifold.cylinder(h, r, r if r2 is None else r2, n).translate(list(p))
def save(nome, m): T(m).export(f"{OUT}/{nome}.stl"); print(nome, np.round(T(m).bounds,1).tolist())
# NEMA17 42.3x42.3x40, boss 22x2, eixo 5x24, furos M3 31mm; origem = centro da face frontal, eixo +Z
def nema17(L=40, eixo=24):
    c = box((-21.15,-21.15,-L), (21.15,21.15,0))
    for sx in (1,-1):
        for sy in (1,-1):
            # chanfro dos cantos
            c = c - box((-3,-3,-L-1),(3,3,1)).rotate([0,0,45]).translate([sx*21.15, sy*21.15, 0])
            c = c - cyl(1.5, 4.5, (sx*15.5, sy*15.5, -4.5))
    corpo_meio = box((-21.2,-21.2,-L+9),(21.2,21.2,-9))
    c = c + cyl(11, 2, (0,0,0)) + cyl(2.5, eixo, (0,0,2))
    return c
save("nema17", nema17())
save("nema17_corpo_preto", box((-21.0,-21.0,-31),(21.0,21.0,-9)))
# fonte RS-150-12: 199 x 98 x 38 ; origem canto
ps = box((0,0,0),(38,98,199))
for i in range(12):
    for j in range(30):
        ps = ps - cyl(1.6, 3, (39, 8+i*7.4, 10+j*6.1), n=10).rotate([0,0,0]) if False else ps
ps_holes = None
save("fonte_rs150", ps)
# vidro 8"x8"x0.13" (203.2 x 203.2 x 3.3)
save("vidro", box((-101.6,-101.6,0),(101.6,101.6,3.3)))
# E3D Lite6 (simplificado): dissipador 22.3 dia x 26 aletas, garganta, bloco 16x20x11.5, bico
def lite6():
    # E3D Lite6 1.75: groove mount 12.7 (3.7/6/3), dissipador 25 aletas, heatbreak, bloco 16x20x11.5, bico -> ponta em -62.5
    m = cyl(8, 3.7, (0,0,-3.7)) + cyl(6, 6, (0,0,-9.7)) + cyl(8, 3, (0,0,-12.7))
    for k in range(9): m = m + cyl(11.15, 1.4, (0,0,-15.2-k*2.9))
    m = m + cyl(6.5, 28, (0,0,-40.7)) + cyl(2, 4, (0,0,-44.7))
    m = m + box((-8,-4.5,-56.2),(12,11.5,-44.7))
    m = m + cyl(3.5, 3, (0,0,-59.2)) + cyl(0.4, 3.3, (0,0,-62.5), 12, 3.5)
    return m
save("lite6", lite6())
save("lite6_bloco", box((-8,-4.5,-56.2),(12,11.5,-44.7)))
save("lite6_bico", cyl(3.5, 3, (0,0,-59.2)) + cyl(0.4, 3.3, (0,0,-62.5), 12, 3.5))
# ventoinha 5015
def f5015():
    m = box((-25,-25,0),(25,25,15)) - cyl(14, 13, (-3,-3,1)) + cyl(10, 15, (-3,-3,0))
    m = m + box((5,-25,0),(25,-45,15)) - box((8,-24,2),(22,-46,13))
    return m
save("ventoinha5015", f5015())
# RAMPS + Mega (101.6 x 53.3), placa com componentes
def ramps():
    m = box((0,0,0),(101.6,53.3,1.6)) + box((0,0,1.6),(101.6,60,3.2)).translate([0,-3.3,12])
    m = m + box((-6,30,1.6),(10,42,12.6)) + box((-2,3,1.6),(12,12,12.6))
    for i in range(5): m = m + box((20+i*14,10,16),(32+i*14,25,26))
    return m
save("ramps", ramps())
# Display Full Graphic Smart (placa 93x87, LCD 78x52 visivel)
save("lcd_placa", box((-46.5,-43.5,0),(46.5,43.5,1.6)) + box((-40,-26,1.6),(40,26,9)))
save("lcd_tela", box((-38,-24.5,9),(38,24.5,9.6)))
save("lcd_moldura", box((-40,-26,9),(40,26,9.4)) - box((-38,-24.5,8),(38,24.5,10)))
# mola 7.5 OD x 20 (aproximada por tubo)
save("mola", cyl(3.75, 20, (0,0,0), 24) - cyl(2.55, 22, (0,0,-1), 24))
# esfera 4.5
save("esfera45", mf.Manifold.sphere(2.25, 20))
# modulo fim de curso (placa 40x16 com micro switch)
save("endstop_pcb", box((-20,-8,0),(20,8,1.6)))
save("endstop_chave", box((-6,-3,1.6),(14,3,11.6)) + box((-6,-2.6,11.6),(16,-2.2,13.5)).rotate([0,0,0]) + box((-17,-4,1.6),(-9,4,8.6)))
# chave fim de curso 20x10x6 com alavanca
save("chave_fimdecurso", box((-10,-3,0),(10,3,10)) + box((-8,-0.5,10),(9,0.5,11)).rotate([0,0,0]))
# entrada IEC C14 com chave
save("iec_c14", box((-25,-14,0),(25,14,3)) + box((-14,-11,-22),(14,11,0)))
# extrusora EZR (simplificada) - corpo 45x30x45 + motor
save("ezr_corpo", box((-21,-21,0),(21,21,10)) + box((-21,-14,10),(15,21,25)) + cyl(5.5, 8, (8,-8,25)) + cyl(3, 6, (-14,10,25)))
save("ezr_tampa", box((-21,-21,12),(-9,21,30)))
# placa RAMPS + Mega (Mega 101.6 x 53.3; furos padrao)
save("mega", box((0,0,0),(101.6,53.3,1.6)) + box((-6.3,32,1.6),(9.7,44,12.5)) + box((-1.8,3.3,1.6),(12.2,12.2,12.5)))
save("ramps_pcb", box((0,0,13.5),(101.6,60.3,15.1)))
save("ramps_comp", box((25,8,15.1),(40,22,26)) + box((44,8,15.1),(59,22,26)) + box((63,8,15.1),(78,22,26)) + box((82,8,15.1),(97,22,26)) + box((3,40,15.1),(30,58,26)))
save("led_fita", box((0,-4,0),(240,4,1.5)))
# tubo bowden 4mm
save("bowden_seg", cyl(2, 1, (0,0,0), 16))
