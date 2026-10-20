import numpy as np, itertools
from asm import holes, AX
def cls(d):
    if 2.3 <= d <= 2.8 or 3.3 <= d <= 3.65 or 4.6 <= d <= 5.15: return "M3"
    if 2.9 <= d <= 3.12 or 4.38 <= d <= 4.56 or 5.45 <= d <= 5.75: return "M4"
    return None
def lines(part, T=np.eye(4)):
    """eixos de furo: (ax_idx, ponto_perp(3), classes, lo, hi) em coords transformadas"""
    L = []
    for p0, p1, d in holes(part):
        c = cls(d)
        if not c: continue
        a = (T @ np.r_[p0,1])[:3]; b = (T @ np.r_[p1,1])[:3]
        ax = int(np.argmax(np.abs(b-a))) if np.linalg.norm(b-a) > 1e-6 else None
        if ax is None: continue
        lo, hi = sorted([a[ax], b[ax]]); pp = a.copy(); pp[ax] = 0
        for l in L:
            if l[0] == ax and np.linalg.norm(l[1]-pp) < 0.4 and c in l[2]:
                l[3] = min(l[3], lo); l[4] = max(l[4], hi); break
        else: L.append([ax, pp, {c}, lo, hi])
    return L
ROTS = []
for perm in itertools.permutations(range(3)):
    for s in itertools.product([1,-1], repeat=3):
        R = np.zeros((3,3))
        for i in range(3): R[perm[i], i] = s[i]
        if np.linalg.det(R) > 0: ROTS.append(R)
def match(part, world, minn=2, tol=0.35, top=8):
    """world: lista de (nome, ax, pp, cls, lo, hi). retorna candidatos"""
    res = []
    for ri, R in enumerate(ROTS):
        T = np.eye(4); T[:3,:3] = R
        B = lines(part, T)
        for ax in range(3):
            bs = [b for b in B if b[0] == ax]; ws = [w for w in world if w[1] == ax]
            if not bs or not ws: continue
            votes = {}
            for bi, b in enumerate(bs):
                for w in ws:
                    if not (b[2] & w[3]): continue
                    t = w[2] - b[1]; t[ax] = 0
                    key = tuple(np.round(t/tol).astype(int))
                    votes.setdefault(key, []).append((bi, w, t))
            for key, v in votes.items():
                nb = len({x[0] for x in v})
                if nb >= minn:
                    t = np.mean([x[2] for x in v], axis=0)
                    # refine: count all within tol
                    res.append((nb, ri, ax, t, sorted({x[1][0] for x in v}), v))
    res.sort(key=lambda r: -r[0])
    # dedupe
    out = []; seen = set()
    for r in res:
        k = (r[1], r[2], tuple(np.round(r[3]).astype(int)))
        if k in seen: continue
        seen.add(k); out.append(r)
    return out[:top]
