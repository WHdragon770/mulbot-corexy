# Confere se cada ponto de cabo chega na caixa da RAMPS por dentro do quadro: voxeliza o ar cortado pelo cabos.py
# (derived/cabos_ar.stl), exige folga para uma sonda de diametro SONDA e propaga a partir da janela da RAMPS.
# python3 cabos_check.py [sonda_mm=3] [voxel_mm=1]
import sys, json, numpy as np, trimesh, manifold3d as mf
from matplotlib.path import Path
from scipy import ndimage
sys.path.insert(0, "/home/lucas/corexy/scripts")
from base import M

SONDA = float(sys.argv[1]) if len(sys.argv) > 1 else 3.0
VX = float(sys.argv[2]) if len(sys.argv) > 2 else 1.0
ar = M(trimesh.load("/home/lucas/corexy/derived/cabos_ar.stl"))
pts = json.load(open("/home/lucas/corexy/out/cabos_pontos.json"))
b = np.array(ar.bounding_box()); lo, hi = b[:3] - 2, b[3:] + 2
n = np.ceil((hi - lo) / VX).astype(int)
xs = lo[0] + (np.arange(n[0]) + 0.5) * VX; ys = lo[1] + (np.arange(n[1]) + 0.5) * VX
V = np.zeros(n, bool)
for k in range(n[2]):
    z = lo[2] + (k + 0.5) * VX
    polys = ar.slice(z).to_polygons()
    if not polys: continue
    verts, codes = [], []
    for p in polys:
        p = np.asarray(p); verts += list(p) + [p[0]]; codes += [Path.MOVETO] + [Path.LINETO] * (len(p) - 1) + [Path.CLOSEPOLY]
    path = Path(np.array(verts), codes)
    a = np.array(verts); i0, i1 = np.searchsorted(xs, a[:, 0].min()), np.searchsorted(xs, a[:, 0].max())
    j0, j1 = np.searchsorted(ys, a[:, 1].min()), np.searchsorted(ys, a[:, 1].max())
    gx, gy = np.meshgrid(xs[i0:i1], ys[j0:j1], indexing="ij")
    if gx.size: V[i0:i1, j0:j1, k] = path.contains_points(np.c_[gx.ravel(), gy.ravel()]).reshape(gx.shape)
r = SONDA / 2 / VX                                   # centro da sonda precisa de r de ar em volta
g = np.ogrid[-int(r):int(r) + 1, -int(r):int(r) + 1, -int(r):int(r) + 1]
bola = (g[0] ** 2 + g[1] ** 2 + g[2] ** 2) <= r * r
livre = ndimage.binary_erosion(V, bola)
def idx(p): return tuple(np.clip(((np.array(p) - lo) / VX).astype(int), 0, n - 1))
def perto(p, R=4.0):
    """voxel livre mais perto do ponto (ate R mm)"""
    c = np.array(idx(p)); k = int(R / VX)
    sl = tuple(slice(max(c[i] - k, 0), c[i] + k + 1) for i in range(3))
    w = np.argwhere(livre[sl])
    if not len(w): return None
    w = w + [s.start for s in sl]; return tuple(w[np.argmin(((w - c) ** 2).sum(1))])
s0 = perto(pts["RAMPS"])
if s0 is None: sys.exit("janela da RAMPS sem folga para a sonda")
semente = np.zeros_like(livre); semente[s0] = True
ok = ndimage.binary_propagation(semente, mask=livre)
print(f"ar {V.sum() * VX ** 3 / 1000:.0f} cm3 | sonda {SONDA} mm | voxel {VX} mm")
falhou = 0
for nome, p in pts.items():
    q = perto(p)
    est = "OK" if q is not None and ok[q] else ("sem folga no ponto" if q is None else "NAO CHEGA")
    falhou += est != "OK"; print(f"  {nome:20s} {est}")

q = perto(pts["display"]); sd = np.zeros_like(livre); sd[q] = True
cd_ = ndimage.binary_propagation(sd, mask=livre)
w = np.argwhere(cd_); print("display alcanca:", (w.min(0) * VX + lo).round(1), (w.max(0) * VX + lo).round(1), "voxels", len(w))
w = np.argwhere(ok); print("RAMPS alcanca:", (w.min(0) * VX + lo).round(1), (w.max(0) * VX + lo).round(1))
# sem a sonda (so ar): conecta?
s1 = np.zeros_like(V); s1[idx(pts["RAMPS"])] = True; a1 = ndimage.binary_propagation(s1, mask=V)
print("so ar, display ligado:", bool(a1[idx(pts["display"])]))
