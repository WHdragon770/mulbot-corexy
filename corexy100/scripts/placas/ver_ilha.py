# Cortes da peca (ja na posicao de impressao) pelo meio de cada ilha sem apoio: plano XZ (y do centro) e YZ (x do centro)
# python3 ver_ilha.py check.json saida.png peca1 [peca2 ...]  (ate 4 ilhas por peca)
import sys, json, os, numpy as np, trimesh, matplotlib
matplotlib.use("Agg"); import matplotlib.pyplot as plt
C = json.load(open(sys.argv[1])); OUT = sys.argv[2]; PEC = sys.argv[3:]
lin = []
for f, r in C.items():
    n = os.path.basename(f)[:-4]
    if n in PEC: lin += [(f, n, o) for o in r[:4] if o["mm3"] >= 5]
fig, axs = plt.subplots(len(lin), 2, figsize=(11, 3.6 * len(lin)), squeeze=False)
for (f, n, o), (a1, a2) in zip(lin, axs):
    m = trimesh.load(f); cx, cy = np.mean(o["x"]), np.mean(o["y"])
    for ax, nrm, c, i, j, ttl in ((a1, [0, 1, 0], [0, cy, 0], 0, 2, f"y={cy:.1f} (X x Z)"), (a2, [1, 0, 0], [cx, 0, 0], 1, 2, f"x={cx:.1f} (Y x Z)")):
        s = m.section(nrm, c)
        if s is not None:
            for e in s.discrete: ax.fill(e[:, i], e[:, j], fc="#9ab", ec="k", lw=0.5)
        b = (o["x"], o["y"], o["z"]); ax.add_patch(plt.Rectangle((b[i][0], b[j][0]), b[i][1] - b[i][0], b[j][1] - b[j][0], fc="none", ec="r", lw=1.5))
        ax.axhline(0, color="k", lw=1); ax.set_aspect("equal"); ax.set_title(f"{n} {o['mm3']:.0f} mm3  {ttl}", fontsize=8)
        lo, hi = m.bounds; ax.set_xlim(lo[i] - 2, hi[i] + 2); ax.set_ylim(-2, hi[j] + 2)
plt.tight_layout(); plt.savefig(OUT, dpi=60)
