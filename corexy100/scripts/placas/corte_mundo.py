# Corte da peca no quadro da montagem (derived/<peca>.stl) com a seta de "pra cima na impressao"
# python3 corte_mundo.py saida.png peca eixo valor [peca eixo valor ...]   (eixo x|y|z = normal do plano)
import sys, json, numpy as np, trimesh, matplotlib
matplotlib.use("Agg"); import matplotlib.pyplot as plt
R = json.load(open("/home/lucas/corexy100/scripts/placas/impressao_rot.json"))
a = sys.argv[2:]; cs = [a[i:i + 3] for i in range(0, len(a), 3)]
fig, axs = plt.subplots(1, len(cs), figsize=(6 * len(cs), 6), squeeze=False)
for ax, (p, e, v) in zip(axs[0], cs):
    m = trimesh.load(f"/home/lucas/corexy100/derived/{p}.stl"); k = "xyz".index(e); n = np.eye(3)[k]
    s = m.section(n, n * float(v)); ij = [i for i in range(3) if i != k]
    for d in s.discrete: ax.fill(d[:, ij[0]], d[:, ij[1]], fc="#9ab", ec="k", lw=0.5)
    up = np.linalg.inv(np.array(R[p])) @ [0, 0, 1]
    c = m.bounds.mean(0); L = 0.15 * m.extents.max()
    ax.annotate("", xy=(c[ij[0]] + up[ij[0]] * L, c[ij[1]] + up[ij[1]] * L), xytext=(c[ij[0]], c[ij[1]]), arrowprops=dict(color="r", width=2))
    ax.set_aspect("equal"); ax.set_title(f"{p} {e}={v}  (seta = cima na impressao)", fontsize=9); ax.grid(alpha=.3)
    ax.set_xlabel("xyz"[ij[0]]); ax.set_ylabel("xyz"[ij[1]])
plt.tight_layout(); plt.savefig(sys.argv[1], dpi=60)
