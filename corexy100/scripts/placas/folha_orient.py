# Folha de conferencia: cada peca orientada vista de lado (frente e lateral), faces em balanco > 45 graus em vermelho, mesa em cinza
# python3 folha_orient.py <pasta_orient> <saida.png> [filtro...]
import sys, glob, os, numpy as np, trimesh, matplotlib
matplotlib.use("Agg"); import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d.art3d import Poly3DCollection
SRC, OUT, FIL = sys.argv[1], sys.argv[2], sys.argv[3:]
fs = [f for f in sorted(glob.glob(f"{SRC}/**/*.stl", recursive=True)) if not FIL or any(x in f for x in FIL)]
n = len(fs); c = 4; r = int(np.ceil(n / c))
fig = plt.figure(figsize=(c * 4.2, r * 3.6), dpi=70)
for i, f in enumerate(fs):
    m = trimesh.load(f)
    if len(m.faces) > 30000: m = m.submesh([np.random.default_rng(0).choice(len(m.faces), 30000, replace=False)], append=True)
    ax = fig.add_subplot(r, c, i + 1, projection="3d")
    nz = m.face_normals[:, 2]; z0 = m.bounds[0][2]
    zf = m.vertices[m.faces][:, :, 2].max(axis=1)
    sh = 0.35 + 0.6 * np.clip(m.face_normals @ np.array([0.3, -0.5, 0.8]), 0, 1)
    cor = np.c_[sh * 0.55, sh * 0.7, sh * 0.95, np.ones_like(sh)]
    cor[(nz < -0.707) & (zf > z0 + 0.3)] = [0.9, 0.15, 0.1, 1]
    ax.add_collection3d(Poly3DCollection(m.vertices[m.faces], facecolors=cor, linewidths=0))
    b = m.bounds; e = (b[1] - b[0]).max() / 2; cc = (b[0] + b[1]) / 2
    ax.set_xlim(cc[0] - e, cc[0] + e); ax.set_ylim(cc[1] - e, cc[1] + e); ax.set_zlim(0, 2 * e)
    xx, yy = np.meshgrid([cc[0] - e, cc[0] + e], [cc[1] - e, cc[1] + e]); ax.plot_surface(xx, yy, xx * 0, color="0.8", alpha=0.4)
    ax.view_init(elev=float(os.environ.get("ELEV", 18)), azim=float(os.environ.get("AZIM", -60))); ax.set_axis_off()
    ax.set_title(f"{os.path.basename(f)[:-4]}\n{m.extents[0]:.0f}x{m.extents[1]:.0f}x{m.extents[2]:.0f}", fontsize=9)
plt.tight_layout(); plt.savefig(OUT)
