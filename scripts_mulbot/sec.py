# python3 sec.py part axis level [level...] -> png com seções
import sys, trimesh, numpy as np, matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
p, ax = sys.argv[1], "XYZ".index(sys.argv[2])
lv = [float(v) for v in sys.argv[3:]]
m = trimesh.load(f"/home/lucas/mulbot/repo/MODELS/{p}.stl")
oc = [i for i in range(3) if i != ax]
fig, axs = plt.subplots(1, len(lv), figsize=(7*len(lv), 7))
axs = np.atleast_1d(axs)
for a, h in zip(axs, lv):
    o = np.zeros(3); o[ax] = h; n = np.zeros(3); n[ax] = 1
    s = m.section(plane_origin=o, plane_normal=n)
    if s is not None:
        for e in s.discrete:
            a.plot(e[:, oc[0]], e[:, oc[1]], "k-", lw=0.8)
    a.set_aspect("equal"); a.grid(True, lw=0.3); a.minorticks_on(); a.grid(True, which="minor", lw=0.1)
    a.set_title(f"{p} {sys.argv[2]}={h}"); a.set_xlabel("XYZ"[oc[0]]); a.set_ylabel("XYZ"[oc[1]])
plt.tight_layout(); out = f"/home/lucas/mulbot/sec_{p}_{sys.argv[2]}.png"; plt.savefig(out, dpi=80); print(out)
