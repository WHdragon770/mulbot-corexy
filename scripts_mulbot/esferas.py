# acha deslocamento do carrinho (ao longo da profundidade) onde cabem esferas de 4.5 nos 4 canais
import sys, trimesh, numpy as np
from shapely.geometry import Polygon, Point
from shapely.ops import unary_union
MD = "/home/lucas/mulbot/repo/MODELS"
def sec2d(part, ax, h, oc):
    m = trimesh.load(f"{MD}/{part}.stl"); o = np.zeros(3); o[ax] = h; n = np.zeros(3); n[ax] = 1
    s = m.section(plane_origin=o, plane_normal=n)
    polys = []
    for e in s.discrete:
        p = Polygon(e[:, oc]); 
        if p.is_valid and p.area > 0.5: polys.append(p)
    return polys
def rail_head(part, ax, h, oc, ztop_min):
    # poligono externo do trilho
    P = max(sec2d(part, ax, h, oc), key=lambda p: p.area)
    return Polygon(P.exterior)
def cavity(part, ax, h, oc):
    P = max(sec2d(part, ax, h, oc), key=lambda p: p.area)
    return P  # com buracos; usaremos material = P
if __name__ == "__main__":
    pass
