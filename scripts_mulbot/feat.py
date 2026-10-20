# extrai furos circulares (por eixo) e faces planas grandes de cada STL
import sys, trimesh, numpy as np, json, os
from shapely.geometry import Polygon
def holes(m, ax, step=1.0, dmax=40):
    lo, hi = m.bounds[0][ax], m.bounds[1][ax]
    n = np.zeros(3); n[ax] = 1
    levels = np.arange(lo+0.3, hi-0.2, step)
    found = []
    secs = m.section_multiplane(plane_origin=m.bounds[0]*n*0, plane_normal=n, heights=list(levels))
    for h, s in zip(levels, secs):
        if s is None: continue
        T = s.metadata.get('to_3D') if hasattr(s, 'metadata') else None
        for poly in s.polygons_full:
            for ring in poly.interiors:
                p = Polygon(ring)
                if p.area < 1: continue
                d = 2*np.sqrt(p.area/np.pi)
                if d > dmax: continue
                circ = 4*np.pi*p.area/(p.length**2)
                if circ < 0.85: continue
                c2 = np.array(p.centroid.coords[0])
                c3 = (s.metadata['to_3D'] @ np.array([c2[0], c2[1], 0, 1]))[:3]
                found.append((h, c3, d))
    # merge
    res = []
    for h, c, d in found:
        for r in res:
            oc = [i for i in range(3) if i != ax]
            if np.linalg.norm(r['c'][oc]-c[oc]) < 0.4 and abs(r['d']-d) < 0.6 and h - r['hi'] <= step*1.6:
                r['hi'] = h; r['ds'].append(d); break
        else:
            res.append({'c': c, 'd': d, 'lo': h, 'hi': h, 'ds': [d]})
    out = []
    for r in res:
        oc = [i for i in range(3) if i != ax]
        c = r['c'].copy(); c[ax] = np.nan
        out.append(dict(ax="XYZ"[ax], c=[None if np.isnan(v) else round(float(v),2) for v in c],
                        d=round(float(np.median(r['ds'])),2), lo=round(float(r['lo']-step/2),1), hi=round(float(r['hi']+step/2),1)))
    return out
def planes(m, minarea=150):
    out = []
    for ax in range(3):
        for sgn in (1, -1):
            sel = m.face_normals[:, ax]*sgn > 0.999
            if not sel.any(): continue
            pos = m.triangles_center[sel][:, ax]; ar = m.area_faces[sel]
            for v in np.unique(np.round(pos, 1)):
                a = ar[np.abs(pos-v) < 0.06].sum()
                if a > minarea: out.append(("+-"[sgn<0]+"XYZ"[ax], float(v), round(float(a))))
    return out
if __name__ == "__main__":
    f = sys.argv[1]
    m = trimesh.load(f)
    print(os.path.basename(f), "bounds", np.round(m.bounds, 2).tolist())
    for ax in range(3):
        for h in holes(m, ax):
            print("  hole", h)
    for p in planes(m): print("  plane", p)
