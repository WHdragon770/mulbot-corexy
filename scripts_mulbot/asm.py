# Biblioteca de montagem: transforms, furos no mundo, checagem de coaxialidade
import numpy as np, trimesh, ast, os, functools
MD = "/home/lucas/mulbot/repo/MODELS"
FD = "/home/lucas/mulbot/feat"
AX = {"X": np.array([1.,0,0]), "Y": np.array([0,1.,0]), "Z": np.array([0,0,1.])}
def vec(s):
    s = s.upper(); return -AX[s[1]] if s[0] == "-" else AX[s[-1]]
def rot(lx, ly, lz):
    R = np.column_stack([vec(lx), vec(ly), vec(lz)])
    assert abs(np.linalg.det(R) - 1) < 1e-6, "rotacao invalida (espelhada)"
    return R
def rotax(axis, deg):
    return trimesh.transformations.rotation_matrix(np.radians(deg), vec(axis))[:3,:3]
def place(R, local, world):
    T = np.eye(4); T[:3,:3] = R; T[:3,3] = np.array(world, float) - R @ np.array(local, float); return T
@functools.lru_cache(None)
def holes(part):
    out = []
    fn = f"{FD}/{os.path.basename(part)[:-4]}.txt" if part.startswith("/") else f"{FD}/{part}.txt"
    if not os.path.exists(fn): return out
    for l in open(fn):
        if "hole " in l:
            h = ast.literal_eval(l.split("hole ",1)[1]); a = "XYZ".index(h["ax"])
            c = np.array([0 if v is None else v for v in h["c"]], float)
            p0 = c.copy(); p0[a] = h["lo"]; p1 = c.copy(); p1[a] = h["hi"]
            out.append((p0, p1, h["d"]))
    return out
@functools.lru_cache(None)
def mesh(part): return trimesh.load(part if part.startswith("/") else f"{MD}/{part}.stl")
def world_holes(part, T, dmax=9):
    r = []
    for p0, p1, d in holes(part):
        if d > dmax: continue
        a = (T @ np.r_[p0,1])[:3]; b = (T @ np.r_[p1,1])[:3]; r.append((a, b, d))
    return r
def coax(partA, TA, partB, TB, tol=0.6, dmax=9):
    """furos de A coaxiais com furos de B (mesmo eixo, linha a < tol)"""
    res = []
    for a0, a1, da in world_holes(partA, TA, dmax):
        ua = (a1-a0)/max(np.linalg.norm(a1-a0),1e-9)
        for b0, b1, db in world_holes(partB, TB, dmax):
            ub = (b1-b0)/max(np.linalg.norm(b1-b0),1e-9)
            if abs(abs(ua@ub)-1) > 1e-3: continue
            w = b0 - a0; off = np.linalg.norm(w - (w@ua)*ua)
            if off < tol:
                # gap axial entre segmentos
                ta = sorted([0, (a1-a0)@ua]); tb = sorted([(b0-a0)@ua, (b1-a0)@ua])
                gap = max(tb[0]-ta[1], ta[0]-tb[1])
                res.append((round(off,2), da, db, np.round(a0,1).tolist(), round(gap,1)))
    return res
def interf(partA, TA, partB, TB, pitch=None):
    """volume de interferencia aproximado (manifold)"""
    import manifold3d as mf
    def M(p, T):
        m = mesh(p).copy(); m.apply_transform(T)
        return mf.Manifold(mf.Mesh(vert_properties=np.asarray(m.vertices, np.float32), tri_verts=np.asarray(m.faces, np.uint32)))
    return (M(partA, TA) ^ M(partB, TB)).volume()
def touch(part, T, other, To, axis, lo, hi, iters=14, tol=0.05):
    """menor deslocamento s em [lo,hi] ao longo de axis tal que part(T+s) nao interfere com other;
    assume interferencia em lo e livre em hi (ou vice-versa) -> bisseccao"""
    a = "XYZ".index(axis)
    def v(s):
        TT = T.copy(); TT[a,3] += s; return interf(part, TT, other, To)
    vlo, vhi = v(lo), v(hi)
    if (vlo > tol) == (vhi > tol): return None, vlo, vhi
    for _ in range(iters):
        m = (lo+hi)/2
        if (v(m) > tol) == (vlo > tol): lo = m
        else: hi = m
    return (hi if vlo > tol else lo), vlo, vhi
