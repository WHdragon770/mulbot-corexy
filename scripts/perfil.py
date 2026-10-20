# Perfis 2D dos trilhos de esferas da Mulbot (cabeca com 4 canais), extraidos dos STLs originais.
# Quadro do perfil: u = transversal (centro do trilho em u=0), v = altura (base v=0, topo da cabeca v=H).
import sys, numpy as np, trimesh, shapely.geometry as sg, shapely.ops as so
sys.path.insert(0, "/home/lucas/mulbot/scripts")
from asm import mesh
def _sec(part, ax, t, uidx, vidx, uc):
    m = mesh(part); n = np.zeros(3); n[ax] = 1; o = np.zeros(3); o[ax] = t
    s = m.section(plane_origin=o, plane_normal=n)
    polys = [sg.Polygon(np.c_[e[:, uidx] - uc, e[:, vidx]]) for e in s.discrete]
    polys = [p.buffer(0) for p in polys]
    U = so.unary_union(polys)
    if U.geom_type == "MultiPolygon": U = max(U.geoms, key=lambda p: p.area)
    P = sg.Polygon(U.exterior)
    return P.intersection(sg.box(-9.6, -1, 9.6, 70))
def perfil_Y():
    # DL1-01-01 (trilho Y) - secao em plano y local onde a largura e 19.1 (sem aba)
    P = _sec("DL1-01-01", 1, 140.3, 0, 2, 17.56 - 0.0)
    return P
def perfil_X():
    # DL1-04-04 (trilho X) - x local = -61.5 (secao cheia)
    return _sec("DL1-04-04", 0, -61.5, 1, 2, 2.386)
if __name__ == "__main__":
    import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
    a, b = perfil_Y(), perfil_X()
    print("Y", a.bounds, a.area); print("X", b.bounds, b.area)
    fig, ax = plt.subplots(1, 2, figsize=(10, 9))
    for A in ax:
        for P, c in ((a, "k"), (b, "r")): x, y = P.exterior.xy; A.plot(x, y, c + "-", lw=.8)
        A.set_aspect("equal"); A.minorticks_on(); A.grid(True, which="both", alpha=.2)
    ax[1].set_ylim(50, 70); ax[1].set_xlim(-11, 11)
    plt.savefig("/home/lucas/corexy/ref/perfis.png", dpi=80)
