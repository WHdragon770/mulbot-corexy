# Fatiador simples pro video: STL -> caminho do bico (paredes + preenchimento) com o tempo de cada ponto.
# Nao e G-code de verdade, so pra animar o bico e o filete saindo. Saida .npz:
#   P (N,3) pontos em mm (peca centrada em X/Y, Z = topo do filete), E (N,) 1 se o trecho que CHEGA no ponto extruda,
#   T (N,) tempo real em s, C (N,) camada; H, W = altura e largura do filete
# python3 fatia.py <stl> <saida.npz> [Z do giro: 0 = em pe como o STL]
import sys, numpy as np, trimesh
from shapely.geometry import LineString, MultiLineString
from shapely.ops import unary_union
from shapely import affinity

H, W = 0.2, 0.45
PAREDES, CHEIO, INFILL = 2, 3, 0.15              # paredes, camadas solidas em cima/embaixo, densidade do preenchimento
V_PAR, V_EXT, V_INF, V_1, V_AR = 40, 30, 60, 20, 150   # mm/s: parede interna, externa, preenchimento, 1a camada, sem extrudar
PASSO = 3.0                                      # trecho extrudando maior que isso e quebrado (o filete cresce aos poucos)

tm = trimesh.load(sys.argv[1], force='mesh')
tm.apply_translation([-tm.bounds.mean(0)[0], -tm.bounds.mean(0)[1], -tm.bounds[0][2]])
NC = int(tm.extents[2] // H)

def regiao(i):
    if i < 0 or i >= NC: return None
    s = tm.section(plane_origin=[0, 0, (i + 0.5) * H], plane_normal=[0, 0, 1])
    if s is None: return None
    pl, _ = s.to_2D(to_2D=np.eye(4))
    r = unary_union(pl.polygons_full).buffer(0)
    return None if r.is_empty else r
R = [regiao(i) for i in range(NC)]

def aneis(g):
    for p in getattr(g, 'geoms', [g]):
        if p.geom_type != 'Polygon' or p.is_empty: continue
        for c in [p.exterior, *p.interiors]:
            c = c.simplify(0.03)
            if c.length > 3 * W: yield np.array(c.coords)

def linhas(area, esp, ang):
    if area.is_empty: return []
    a = affinity.rotate(area, -ang, origin=(0, 0)); x0, y0, x1, y1 = a.bounds
    ys = np.arange(y0 + esp / 2 - (y0 % esp), y1, esp)
    out = []
    for k, y in enumerate(ys):
        g = a.intersection(LineString([(x0 - 1, y), (x1 + 1, y)]))
        segs = [s for s in getattr(g, 'geoms', [g]) if s.geom_type == 'LineString' and s.length > W]
        segs.sort(key=lambda s: s.coords[0][0], reverse=k % 2 == 1)
        for s in segs:
            c = np.array(affinity.rotate(s, ang, origin=(0, 0)).coords)
            out.append(c[::-1] if k % 2 else c)
    return out

P, E, V, C = [], [], [], []
def poe(pts, z, v, cam):
    pts = np.c_[pts, np.full(len(pts), z)]
    P.append(pts[0]); E.append(0); V.append(V_AR); C.append(cam)        # vai sem extrudar ate o comeco
    for a, b in zip(pts[:-1], pts[1:]):
        n = max(1, int(np.ceil(np.linalg.norm(b - a) / PASSO)))
        for t in np.arange(1, n + 1) / n: P.append(a + (b - a) * t); E.append(1); V.append(v); C.append(cam)

for i, r in enumerate(R):
    if r is None: continue
    z = (i + 1) * H; v1 = V_1 if i == 0 else None
    for k in reversed(range(PAREDES)):                              # de dentro pra fora
        for c in aneis(r.buffer(-(k + 0.5) * W, join_style=2)): poe(c, z, v1 or (V_EXT if k == 0 else V_PAR), i)
    dentro = r.buffer(-PAREDES * W + 0.1, join_style=2)
    miolo = dentro                                                  # solido onde falta peca ate CHEIO camadas acima/abaixo
    for j in range(i - CHEIO, i + CHEIO + 1):
        miolo = miolo.intersection(R[j]) if 0 <= j < NC and R[j] is not None else miolo.intersection(miolo.buffer(-1e4))
    cheio = dentro.difference(miolo)
    ang = 45 if i % 2 else -45
    for c in linhas(cheio, W, ang): poe(c, z, v1 or V_INF, i)
    for c in linhas(dentro.difference(cheio), W / INFILL, ang): poe(c, z, v1 or V_INF, i)

P = np.array(P); E = np.array(E, np.int8); C = np.array(C, np.int16)
d = np.r_[0, np.linalg.norm(np.diff(P, axis=0), axis=1)]
T = np.cumsum(d / np.array(V))
np.savez_compressed(sys.argv[2], P=P.astype(np.float32), E=E, T=T.astype(np.float64), C=C, H=H, W=W)
print(f"{NC} camadas, {len(P)} pontos, filete {d[E == 1].sum() / 1000:.1f} m, tempo real {T[-1] / 60:.0f} min")
