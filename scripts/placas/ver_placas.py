# Desenha as placas lendo o proprio 3MF (confere o que o Slicer vai abrir): vista de cima, mesa 260 x 260, contorno de cada peca
# python3 ver_placas.py arquivo.3mf saida.png
import sys, zipfile, re, numpy as np, trimesh, matplotlib
matplotlib.use("Agg"); import matplotlib.pyplot as plt
from scipy.spatial import ConvexHull
z = zipfile.ZipFile(sys.argv[1]); top = z.read("3D/3dmodel.model").decode()
cfg = z.read("Metadata/model_settings.config").decode()
comp = dict(re.findall(r'<object id="(\d+)"[^>]*>\s*<components>\s*<component p:path="([^"]+)"', top))
nomes = dict(re.findall(r'<object id="(\d+)">\s*<metadata key="name" value="([^"]+)"', cfg))
casco = {}
for oid, path in comp.items():
    t = z.read(path.lstrip("/")).decode()
    v = np.array(re.findall(r'<vertex x="([^"]+)" y="([^"]+)" z="([^"]+)"', t), float)
    casco[oid] = (v[ConvexHull(v[:, :2]).vertices][:, :2], v[:, 2].max())
itens = [(o, np.array(t.split(), float)) for o, t in re.findall(r'<item objectid="(\d+)"[^>]*transform="([^"]+)"', top)]
placas = re.findall(r'<plate>(.*?)</plate>', cfg, re.S)
cols = int(np.ceil(np.sqrt(len(placas))))
fig, axs = plt.subplots(int(np.ceil(len(placas) / cols)), cols, figsize=(5 * cols, 5 * int(np.ceil(len(placas) / cols))), squeeze=False)
k = 0; erros = 0
for p, pl in enumerate(placas):
    ax = axs.flat[p]; ox, oy = (p % cols) * 312.0, -(p // cols) * 312.0
    nome = re.search(r'plater_name" value="([^"]*)"', pl).group(1)
    n = len(re.findall("<model_instance>", pl)); hmax = 0
    ax.add_patch(plt.Rectangle((0, 0), 260, 260, fc="0.92", ec="k"))
    for o, T in itens[k:k + n]:
        M = T[:9].reshape(3, 3); h, zt = casco[o]
        q = np.c_[h, np.zeros(len(h))] @ M + T[9:]; q = q[:, :2] - [ox, oy]
        if q.min() < 0 or q.max() > 260: erros += 1
        ax.fill(q[:, 0], q[:, 1], alpha=0.6); hmax = max(hmax, zt)
        c = q.mean(axis=0); ax.text(c[0], c[1], nomes[o][:14], fontsize=5, ha="center")
    k += n
    ax.set_title(f"{nome}: {n} pecas, alt. max {hmax:.0f} mm", fontsize=9); ax.set_xlim(-5, 265); ax.set_ylim(-5, 265); ax.set_aspect("equal"); ax.set_xticks([]); ax.set_yticks([])
for a in axs.flat[len(placas):]: a.axis("off")
plt.tight_layout(); plt.savefig(sys.argv[2], dpi=55)
print(sys.argv[1].split("/")[-1], "placas", len(placas), "fora da mesa:", erros)
