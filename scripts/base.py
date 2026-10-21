# Base da CoreXY estilo Mulbot: helpers de montagem, trilho extrudado, carro de esferas, polias, correia.
# Mundo: X direita, Y para tras, Z para cima, mm. Frente = -Y.
import sys, os, json, numpy as np, trimesh, manifold3d as mf
sys.path.insert(0, "/home/lucas/mulbot/scripts"); sys.path.insert(0, "/home/lucas/corexy/scripts")
from asm import rot, rotax, place, mesh, MD
from perfil import perfil_Y
import shapely.geometry as sg
VT = "/home/lucas/mulbot/vit"
DER = "/home/lucas/corexy/derived"; os.makedirs(DER, exist_ok=True)
REF = json.load(open(f"{DER}/mulbot_ref.json"))
RI = {n: (p, np.array(t), c) for n, p, t, c in REF["items"]}

P = []   # (nome, stl/peca, T, cor)
def add(nome, peca, T, cor): P.append((nome, peca, np.asarray(T, float), cor)); return T
def tr(v): T = np.eye(4); T[:3, 3] = v; return T
def R4(R, t=(0, 0, 0)): T = np.eye(4); T[:3, :3] = R; T[:3, 3] = t; return T

# ---------- manifold <-> trimesh
def M(t):
    return mf.Manifold(mf.Mesh(vert_properties=np.asarray(t.vertices, np.float32), tri_verts=np.asarray(t.faces, np.uint32)))
def Tm(m):
    g = m.to_mesh(); return trimesh.Trimesh(np.asarray(g.vert_properties)[:, :3], np.asarray(g.tri_verts), process=False)
def salva(m, nome):
    fn = f"{DER}/{nome}.stl"
    Tm(m.simplify(1e-3)).export(fn); return fn          # simplify: tira triangulo de area 0 que sobra de booleana (malha continua fechada)
def caixa(a, b):
    a = np.array(a, float); b = np.array(b, float); lo = np.minimum(a, b); hi = np.maximum(a, b)
    return mf.Manifold.cube((hi - lo).tolist()).translate(lo.tolist())
def cil(p0, p1, r, n=64, r1=None):
    p0 = np.array(p0, float); p1 = np.array(p1, float); d = p1 - p0; L = np.linalg.norm(d); z = d / L
    x = np.cross(z, [0, 0, 1.0]) if abs(z[2]) < 0.9 else np.cross(z, [1.0, 0, 0]); x /= np.linalg.norm(x); y = np.cross(z, x)
    Mx = np.column_stack([x, y, z, p0])
    return mf.Manifold.cylinder(L, r, r if r1 is None else r1, n).transform(Mx.tolist())
def peca_mf(peca, T):
    m = mesh(peca).copy(); m.apply_transform(T); return M(m)

# ---------- trilho de esferas (perfil Mulbot) extrudado
# Quadro do trilho (igual ao da Mulbot): x = transversal, y = ao longo, z = altura (cabeca em z 54..68.26 no topo)
H_TRILHO = 68.2625
def _perfil_cs(h=H_TRILHO):
    P = perfil_Y()
    cab = P.intersection(sg.box(-10, 45, 10, 70))
    dz = h - H_TRILHO
    import shapely.affinity as sa
    cab = sa.translate(cab, 0, dz)
    corpo = sg.box(-9.525, 0, 9.525, 46 + dz)
    U = cab.union(corpo).simplify(0.01)
    pts = np.array(U.exterior.coords)[:-1]
    if sg.Polygon(pts).exterior.is_ccw is False: pts = pts[::-1]
    return mf.CrossSection([pts.tolist()])
def trilho(L, h=H_TRILHO):
    """trilho reto de comprimento L no quadro do trilho: y de 0 a L"""
    e = _perfil_cs(h).extrude(L)            # (u, v, w)
    # (u,v,w) -> (x,y,z) = (-u, w, v)
    return e.transform([[-1, 0, 0, 0], [0, 0, 1, 0], [0, 1, 0, 0]])
# carro DL1-03-01 no quadro do trilho, centro do carro em y = s
def Tcarro(s): return place(rot("-Z", "X", "-Y"), (0, 44.07, 25.4), (0, s, 62.9))
T1c = tr((8.64, -9.08, -9.525)); T2c = R4(np.diag([1, -1, -1.]), (8.64, 97.23, 60.325))
CY = [((-5.64, 34.32), (-8.72, 25.39)), ((0.75, 34.32), (3.97, 25.39)), ((-5.64, 53.82), (-8.72, 62.76)), ((0.75, 53.82), (3.97, 62.76))]
def circuito(L, R, n=28, z0=0.0, z1=50.8):
    L = np.array(L, float); R = np.array(R, float); c = (L + R) / 2; r = np.linalg.norm(L - R) / 2; e = (L - R) / (2 * r)
    Ltot = 2 * (z1 - z0) + 2 * np.pi * r; pts = []
    for i in range(n):
        s_ = (i + 0.5) * Ltot / n
        if s_ < (z1 - z0): pts.append((L[0], L[1], z0 + s_)); continue
        s_ -= (z1 - z0)
        if s_ < np.pi * r:
            a_ = s_ / r; q = c + r * np.cos(a_) * e; pts.append((q[0], q[1], z1 + r * np.sin(a_))); continue
        s_ -= np.pi * r
        if s_ < (z1 - z0): pts.append((R[0], R[1], z1 - s_)); continue
        s_ -= (z1 - z0); a_ = s_ / r; q = c - r * np.cos(a_) * e; pts.append((q[0], q[1], z0 - r * np.sin(a_)))
    return pts
ESFERAS = os.environ.get("ESFERAS", "1") == "1"
def carro(nome, F, s, cor="azul"):
    """carro generico (DL1-03-01 + 2 tampas DL1-03-02 + 112 esferas) no trilho de quadro F, posicao s"""
    Tc = F @ Tcarro(s)
    add(nome, "DL1-03-01", Tc, cor)
    add(nome + "_tampa1", "DL1-03-02", Tc @ T1c, cor); add(nome + "_tampa2", "DL1-03-02", Tc @ T2c, cor)
    if ESFERAS:
        k = 0
        for L, R in CY:
            for p in circuito(L, R):
                add(f"esfera_{nome}_{k:03d}", f"{VT}/esfera45.stl", Tc @ tr(p), "aco"); k += 1
    return Tc
# furos M3 do topo do carro (no quadro do trilho, relativo ao centro s): x=+-20.64, y=+-17.46, topo z=85.61
CARRO_TOPO = 85.61; CARRO_FX = 20.64; CARRO_FY = 17.46

# ---------- polia louca Mulbot (DL1-06) com eixo em qualquer direcao
_IDL = [n for n in RI if n.startswith(("poliaLouca", "eixoLouca", "gaiolaLouca", "esferaLouca"))]
_Ci = R4(rot("X", "-Z", "Y"), (REF["XID"], REF["YBELT"], REF["MX"][2]))   # quadro da polia na Mulbot: z local = eixo (+Y mundo)
def _eixo_curto(peca, L):
    fn = f"{DER}/{peca}_L{L:.1f}.stl"
    if not os.path.exists(fn): salva(M(mesh(peca)) ^ caixa((-500, -500, -1), (500, 500, L)), os.path.basename(fn)[:-4])
    return fn
def polia_louca(nome, c, eixo=(0, 0, 1), Linf=None, Lsup=None):
    """centro da faixa da correia em c, eixo da polia ao longo de 'eixo'. Linf/Lsup: corta a ponta dos eixos (06-02 em baixo, 06-03 em cima)"""
    z = np.array(eixo, float); z /= np.linalg.norm(z)
    x = np.cross([0, 1.0, 0], z) if abs(z[1]) < 0.9 else np.array([1.0, 0, 0]); x /= np.linalg.norm(x); y = np.cross(z, x)
    Tn = R4(np.column_stack([x, y, z]), c) @ np.linalg.inv(_Ci)
    for n in _IDL:
        if n.startswith("esferaLouca") and not ESFERAS: continue
        p, t, cor = RI[n]
        if n == "eixoLoucaA" and Linf: p = _eixo_curto(p, Linf)
        if n == "eixoLoucaB" and Lsup: p = _eixo_curto(p, Lsup)
        add(nome + "_" + n, p, Tn @ t, cor)
# polia motora DL1-04-08 + motor: quadro do motor (z = eixo, face em z=0); centro da correia a 23.02 mm da face
_Tmx = R4(rot("X", "Z", "-Y"), REF["MX"])
def motor(nome, Tmot, polia=True):
    add(nome, f"{VT}/nema17.stl", Tmot, "aco"); add(nome + "_corpo", f"{VT}/nema17_corpo_preto.stl", Tmot, "preto")
    if polia:
        p, t, c = RI["poliaX"]; add(nome + "_polia", p, Tmot @ np.linalg.inv(_Tmx) @ t, "verm")
POLIA_FACE = REF["MX"][1] - REF["YBELT"]   # 23.02
RP = 7.0          # raio primitivo usado p/ correia (polia motora e louca)

# ---------- correia plana (TPU impressa) no plano z = zc
def _left(t): return np.array([-t[1], t[0]])
def _tang(c1, r1, d1, c2, r2, d2):
    c1 = np.array(c1, float); c2 = np.array(c2, float); D = c2 - c1; L = np.linalg.norm(D); e = D / L
    k = d2 * r2 - d1 * r1; sa = -k / L; ca = np.sqrt(max(1 - sa * sa, 0))
    t = ca * e + sa * _left(e)
    p1 = c1 - d1 * r1 * _left(t); p2 = c2 - d2 * r2 * _left(t)
    return p1, p2, t
def caminho(seq, step=0.6):
    """seq: [(c, r, d)], primeiro e ultimo com r=0 (pontas presas). d=+1 polia a esquerda do sentido (giro anti-horario)"""
    pts = []; tans = []
    for i in range(len(seq) - 1):
        (c1, r1, d1), (c2, r2, d2) = seq[i], seq[i + 1]
        p1, p2, t = _tang(c1, r1, d1, c2, r2, d2); tans.append((p1, p2, t))
    for i, (p1, p2, t) in enumerate(tans):
        if i > 0:   # arco na polia i
            c, r, d = seq[i]; c = np.array(c, float)
            a0 = np.arctan2(*(pts[-1] - c)[::-1]); a1 = np.arctan2(*(p1 - c)[::-1])
            da = (a1 - a0) % (2 * np.pi) if d > 0 else -((a0 - a1) % (2 * np.pi))
            n = max(int(abs(da) * r / step), 2)
            for a in np.linspace(a0, a0 + da, n)[1:]: pts.append(c + r * np.array([np.cos(a), np.sin(a)]))
        n = max(int(np.linalg.norm(p2 - p1) / step), 1)
        for u in np.linspace(0, 1, n + 1)[(1 if i > 0 else 0):]: pts.append(p1 + u * (p2 - p1))
    return np.array(pts)
def correia(seq, zc, larg=12.0, esp=1.8):
    P2 = caminho(seq); n = len(P2)
    T = np.gradient(P2, axis=0); T /= np.linalg.norm(T, axis=1)[:, None]; N = np.c_[-T[:, 1], T[:, 0]]
    V = []
    for p, nn in zip(P2, N):
        for o in (-esp / 2, esp / 2):
            for z in (zc - larg / 2, zc + larg / 2): V.append((p[0] + o * nn[0], p[1] + o * nn[1], z))
    V = np.array(V); F = []
    for i in range(n - 1):
        a = 4 * i; b = 4 * (i + 1)
        for (p, q) in ((0, 1), (1, 3), (3, 2), (2, 0)): F += [(a + p, b + p, b + q), (a + p, b + q, a + q)]
    for a, rev in ((0, False), (4 * (n - 1), True)):
        f = [(a + 0, a + 2, a + 3), (a + 0, a + 3, a + 1)]; F += [tuple(reversed(t)) for t in f] if rev else f
    m = trimesh.Trimesh(V, np.array(F), process=True); m.fix_normals()
    L = float(np.sum(np.linalg.norm(np.diff(P2, axis=0), axis=1)))
    return m, L

# ---------- export p/ render (render_asm.py da Mulbot) e checagem
def grupo(n, p):
    b = os.path.basename(p)
    for k, g in (("trilho", "Trilhos"), ("carro", "Carros"), ("esfera", "Esferas"), ("Louca", "Polias"), ("motor", "Motores"),
                 ("correia", "Correias"), ("mesa", "Mesa"), ("quadro", "Quadro")):
        if k in n: return g
    return "Outros"
def export(fn, so=None, sem=()):
    L = []
    for n, p, t, c in P:
        if so and not any(s in n for s in so): continue
        if any(s in n for s in sem): continue
        f = p if p.startswith("/") else f"{MD}/{p}.stl"
        L.append(dict(nome=n, stl=f, T=np.asarray(t).tolist(), cor=c, grupo=grupo(n, f), peca=os.path.basename(f)[:-4]))
    json.dump(L, open(fn, "w")); return fn
def bounds(nome):
    for n, p, t, c in P:
        if n == nome:
            m = mesh(p).copy(); m.apply_transform(t); return m.bounds
