# gera a correia X (TPU) no caminho polia motora -> polia louca, pontas na presilha do carro
import numpy as np, trimesh
def caminho(xd, xi, zc, xa, xb, rp=7.0, step=0.5):
    """pontos (x,z) e normais para dentro; inicio em xa (ponta esquerda na presilha), fim em xb"""
    P, N = [], []
    def seg(p0, p1, nrm):
        L = np.linalg.norm(np.subtract(p1, p0)); n = max(int(L/step), 1)
        for t in np.linspace(0, 1, n, endpoint=False): P.append(np.add(p0, np.multiply(t, np.subtract(p1, p0)))); N.append(nrm)
    def arco(c, a0, a1):
        n = max(int(abs(a1-a0)*rp/step), 2)
        for a in np.linspace(a0, a1, n, endpoint=False):
            P.append((c[0]+rp*np.cos(a), c[1]+rp*np.sin(a))); N.append((-np.cos(a), -np.sin(a)))
    seg((xa, zc-rp), (xd, zc-rp), (0, 1))
    arco((xd, zc), -np.pi/2, -3*np.pi/2)          # volta pela esquerda da polia motora
    seg((xd, zc+rp), (xi, zc+rp), (0, -1))
    arco((xi, zc), np.pi/2, -np.pi/2)             # volta pela direita da polia louca
    seg((xi, zc-rp), (xb, zc-rp), (0, 1))
    P.append((xb, zc-rp)); N.append((0, 1))
    return np.array(P), np.array(N)
def correia(xd, xi, zc, y0, xa, xb, larg=12.0, esp=1.8, passo=2.5, dente=0.9):
    P, N = caminho(xd, xi, zc, xa, xb)
    # comprimento acumulado p/ dentes
    s = np.r_[0, np.cumsum(np.linalg.norm(np.diff(P, axis=0), axis=1))]
    V, F = [], []
    n = len(P)
    for i in range(n):
        tooth = dente if (s[i] % passo) < passo*0.45 else 0.0
        inn = P[i] + N[i]*(esp/2 + tooth); out = P[i] - N[i]*(esp/2)
        for (x, z) in (inn, out):
            for y in (y0-larg/2, y0+larg/2):
                V.append((x, y, z))
    V = np.array(V)
    # quad strips: idx(i, k) com k = 0 in-y0,1 in-y1,2 out-y0,3 out-y1
    for i in range(n-1):
        a = 4*i; b = 4*(i+1)
        for (p, q) in ((0,1),(1,3),(3,2),(2,0)):
            F += [(a+p, b+p, b+q), (a+p, b+q, a+q)]
    for a, rev in ((0, False), (4*(n-1), True)):
        f = [(a+0, a+2, a+3), (a+0, a+3, a+1)]
        F += [tuple(reversed(t)) for t in f] if rev else f
    m = trimesh.Trimesh(V, np.array(F), process=True); m.fix_normals()
    return m, s[-1]
def tubo(pts, r=2.0, n=16, passos=200):
    """tubo ao longo de spline catmull-rom pelos pontos"""
    P = np.asarray(pts, float)
    P = np.vstack([P[0], P, P[-1]])
    C = []
    for i in range(1, len(P)-2):
        p0, p1, p2, p3 = P[i-1], P[i], P[i+1], P[i+2]
        for t in np.linspace(0, 1, passos//(len(P)-3), endpoint=False):
            C.append(0.5*((2*p1) + (-p0+p2)*t + (2*p0-5*p1+4*p2-p3)*t*t + (-p0+3*p1-3*p2+p3)*t**3))
    C.append(P[-2]); C = np.array(C)
    T = np.gradient(C, axis=0); T /= np.linalg.norm(T, axis=1)[:, None]
    a = np.array([0, 0, 1.0]) if abs(T[0][2]) < 0.9 else np.array([1.0, 0, 0])
    V = []
    for i, (c, t) in enumerate(zip(C, T)):
        u = np.cross(t, a); u /= np.linalg.norm(u); v = np.cross(t, u); a = v
        for k in range(n):
            th = 2*np.pi*k/n; V.append(c + r*(np.cos(th)*u + np.sin(th)*v))
    V = np.array(V); F = []
    for i in range(len(C)-1):
        for k in range(n):
            a0 = i*n+k; a1 = i*n+(k+1)%n; b0 = a0+n; b1 = a1+n
            F += [(a0, b0, b1), (a0, b1, a1)]
    V = np.vstack([V, C[0], C[-1]]); c0, c1 = len(V)-2, len(V)-1
    for k in range(n):
        F.append((c0, (k+1)%n, k)); F.append((c1, (len(C)-1)*n+k, (len(C)-1)*n+(k+1)%n))
    m = trimesh.Trimesh(V, np.array(F), process=True); m.fix_normals(); return m
