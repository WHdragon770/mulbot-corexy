# Cabos 3D pro video: menor caminho de cada aparelho ate a janela da RAMPS PELO AR de dentro do quadro
# (derived/cabos_ar.stl, o mesmo da conferencia cabos_check.py), puxado pro centro do canal, alisado e virado tubo.
# Saida: out/anim/cabos/<nome>.stl + cabos.json (cor e ordem). python3 cabos_caminhos.py
import sys, os, json, numpy as np, trimesh
from scipy import ndimage, sparse
from scipy.sparse.csgraph import dijkstra
from matplotlib.path import Path
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
from base import M
CX = os.environ.get("CXY_DIR") or os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
VX, R_CABO = 1.5, 2.5                                      # voxel (mm) e raio do tubo (grosso pra aparecer no quadro translucido)
OUT = f"{CX}/out/anim/cabos"; os.makedirs(OUT, exist_ok=True)
ar = M(trimesh.load(f"{CX}/derived/cabos_ar.stl"))
P = json.load(open(f"{CX}/out/cabos_pontos.json"))
CABOS = [("motorA", "motorA", (0.95, 0.45, 0.05)), ("motorB", "motorB", (0.98, 0.80, 0.10)), ("motorZ_E", "motorZ_E", (0.20, 0.75, 0.25)),
         ("motorZ_D", "motorZ_D", (0.20, 0.75, 0.25)), ("fonte", "fonte", (0.85, 0.10, 0.10)), ("display", "display", (0.45, 0.55, 0.95)),
         ("fimCursoZ", "fimCursoZ", (0.95, 0.95, 0.95)), ("fimCursoY", "fimCursoY", (0.95, 0.95, 0.95)),
         ("cabeca", "cabeca (esteira)" if "cabeca (esteira)" in P else "cabeca (umbilical)", (0.70, 0.30, 0.90))]

# ---- voxeliza o ar
b = np.array(ar.bounding_box()); lo, hi = b[:3] - 3, b[3:] + 3
n = np.ceil((hi - lo) / VX).astype(int)
xs = lo[0] + (np.arange(n[0]) + 0.5) * VX; ys = lo[1] + (np.arange(n[1]) + 0.5) * VX
V = np.zeros(n, bool)
for k in range(n[2]):
    polys = ar.slice(lo[2] + (k + 0.5) * VX).to_polygons()
    if not polys: continue
    verts, codes = [], []
    for p in polys:
        p = np.asarray(p); verts += list(p) + [p[0]]; codes += [Path.MOVETO] + [Path.LINETO] * (len(p) - 1) + [Path.CLOSEPOLY]
    pa = Path(np.array(verts), codes); a = np.array(verts)
    i0, i1 = np.searchsorted(xs, a[:, 0].min()), np.searchsorted(xs, a[:, 0].max())
    j0, j1 = np.searchsorted(ys, a[:, 1].min()), np.searchsorted(ys, a[:, 1].max())
    gx, gy = np.meshgrid(xs[i0:i1], ys[j0:j1], indexing="ij")
    if gx.size: V[i0:i1, j0:j1, k] = pa.contains_points(np.c_[gx.ravel(), gy.ravel()]).reshape(gx.shape)
D = ndimage.distance_transform_edt(V) * VX                 # distancia ate a parede (mm)
livre = D >= 1.0                                          # 1 mm de ar em volta do centro (frestas de ~3,8 mm ao lado das porcas-barril)
idx = -np.ones(n, np.int64); pts = np.argwhere(livre); idx[tuple(pts.T)] = np.arange(len(pts))
# ---- grafo 6-vizinhos, custo maior perto da parede (caminho pelo meio do canal)
rows, cols, w = [], [], []
for d in ((1, 0, 0), (0, 1, 0), (0, 0, 1)):
    q = pts + d; ok = np.all(q < n, axis=1); a_, q = pts[ok], q[ok]
    j = idx[tuple(q.T)]; m = j >= 0; i = idx[tuple(a_[m].T)]; j = j[m]
    c = 1.0 + 6.0 / (0.5 + 0.5 * (D[tuple(a_[m].T)] + D[tuple(q[m].T)]))
    rows += [i, j]; cols += [j, i]; w += [c, c]
G = sparse.csr_matrix((np.concatenate(w), (np.concatenate(rows), np.concatenate(cols))), shape=(len(pts),) * 2)
def tubo_ao_longo(c, r, nl):                              # tubo com aneis perpendiculares ao caminho (leve, sem booleana)
    t = np.gradient(c, axis=0); t /= np.linalg.norm(t, axis=1)[:, None] + 1e-9
    a = np.cross(t[0], [0, 0, 1.0] if abs(t[0][2]) < 0.9 else [1.0, 0, 0]); a /= np.linalg.norm(a)
    U = []                                                 # frame que "rola" junto (sem torcer)
    for ti in t:
        a = a - ti * (a @ ti); a /= np.linalg.norm(a) + 1e-9; U.append(a)
    U = np.array(U); W = np.cross(t, U); ang = np.linspace(0, 2 * np.pi, nl, endpoint=False)
    v = (c[:, None] + r * (np.cos(ang)[None, :, None] * U[:, None] + np.sin(ang)[None, :, None] * W[:, None])).reshape(-1, 3)
    f = []
    for i in range(len(c) - 1):
        for j in range(nl):
            a0, a1, b0, b1 = i * nl + j, i * nl + (j + 1) % nl, (i + 1) * nl + j, (i + 1) * nl + (j + 1) % nl
            f += [[a0, b0, a1], [a1, b0, b1]]
    v = np.vstack([v, c[0], c[-1]]); e0, e1 = len(v) - 2, len(v) - 1; k = (len(c) - 1) * nl
    f += [[e0, (j + 1) % nl, j] for j in range(nl)] + [[e1, k + j, k + (j + 1) % nl] for j in range(nl)]
    return trimesh.Trimesh(v, np.array(f), process=False)
def no(p):
    c = np.round((np.array(p) - lo) / VX - 0.5).astype(int)
    d2 = ((pts - c) ** 2).sum(1); return int(np.argmin(d2))
fonte = no(P["RAMPS"])
dist, pred = dijkstra(G, indices=fonte, return_predecessors=True)
info = []
for k, (nome, chave, cor) in enumerate(CABOS):
    alvo = no(P[chave]); cam = [alvo]
    while cam[-1] != fonte and pred[cam[-1]] >= 0: cam.append(pred[cam[-1]])
    if cam[-1] != fonte: print("AVISO sem caminho:", nome)
    xyz = lo + (pts[cam] + 0.5) * VX
    xyz = np.vstack([np.array(P[chave], float), xyz])       # comeca no aparelho
    for _ in range(6): xyz[1:-1] = (xyz[:-2] + 2 * xyz[1:-1] + xyz[2:]) / 4   # alisa
    off = (np.array([np.cos(k * 2.4), np.sin(k * 2.4), 0.0])) * 1.0             # feixe: cada cabo levemente deslocado
    xyz = xyz + off
    seg = np.linalg.norm(np.diff(xyz, axis=0), axis=1)
    s_ = np.r_[0, np.cumsum(seg)]; t_ = np.linspace(0, s_[-1], max(2, int(s_[-1] / 2.0)))   # reamostra a cada 2 mm
    xyz = np.c_[[np.interp(t_, s_, xyz[:, i]) for i in range(3)]].T
    tubo = tubo_ao_longo(xyz, R_CABO, 10)
    tubo.export(f"{OUT}/{nome}.stl")
    info.append(dict(nome=nome, cor=cor, comprimento=float(s_[-1]), ordem=k))
    print(f"{nome:10s} {s_[-1]:6.0f} mm  {len(tubo.faces)} faces", flush=True)
json.dump(info, open(f"{OUT}/cabos.json", "w"), indent=1)
