# Fixadores impressos: rosca metrica ISO (perfil trapezoidal), parafuso, porca, porca-barril (cross dowel)
import numpy as np, trimesh, manifold3d as mf
def _M(t): return mf.Manifold(mf.Mesh(vert_properties=np.asarray(t.vertices, np.float32), tri_verts=np.asarray(t.faces, np.uint32)))
def _T(m):
    g = m.to_mesh(); return trimesh.Trimesh(np.asarray(g.vert_properties)[:, :3], np.asarray(g.tri_verts), process=False)
def perfil(u):
    """u em [0,1): 1 = crista, 0 = raiz (ISO: crista P/8, raiz P/4)"""
    u = u % 1.0
    if u < 0.125: return 1.0
    if u < 0.4375: return 1.0 - (u-0.125)/0.3125
    if u < 0.6875: return 0.0
    return (u-0.6875)/0.3125
def rosca(d, p, L, folga=0.0, interna=False, nseg=96, chanfro=True):
    """solido roscado (cilindro com rosca) de z=0 a z=L. externa: d-2*folga ; interna (para subtrair): d+2*folga"""
    H = 0.8660254*p
    if interna: rmaj = d/2 + folga; rmin = d/2 - 0.5413*p + folga     # furo da porca (macho imaginario com folga)
    else:       rmaj = d/2 - folga; rmin = d/2 - 0.6134*p - folga
    nz = max(int(L/(p/16)), 4)
    th = np.linspace(0, 2*np.pi, nseg, endpoint=False); zs = np.linspace(0, L, nz+1)
    V = []
    for z in zs:
        for t in th:
            r = rmin + (rmaj-rmin)*perfil((z - p*t/(2*np.pi))/p)
            if chanfro and not interna:          # chanfro de entrada nas pontas
                cz = min(z, L-z); r = min(r, rmin + max(cz, 0)*1.0 + 0.0) if cz < (rmaj-rmin) else r
            V.append((r*np.cos(t), r*np.sin(t), z))
    V = np.array(V); F = []
    for i in range(nz):
        for k in range(nseg):
            a = i*nseg+k; b = i*nseg+(k+1)%nseg; c = a+nseg; e = b+nseg
            F += [(a, b, e), (a, e, c)]
    V = np.vstack([V, (0,0,0), (0,0,L)]); c0, c1 = len(V)-2, len(V)-1
    for k in range(nseg):
        F.append((c0, (k+1)%nseg, k)); F.append((c1, nz*nseg+k, nz*nseg+(k+1)%nseg))
    m = trimesh.Trimesh(V, np.array(F), process=True); m.fix_normals()
    return _M(m)
def hexagono(af, h, z0=0.0, chanfro=0.8):
    r = af/np.sqrt(3)
    m = mf.Manifold.cylinder(h, r, r, 6).rotate([0,0,30]).translate([0,0,z0])
    if chanfro:
        cone = mf.Manifold.cylinder(h, af/2+chanfro*0.0+h*1.5, af/2 - 0.1, 64).translate([0,0,z0])   # cone de chanfro inferior
        m = m ^ (mf.Manifold.cylinder(h, af/2 + h, af/2*0.92, 64).translate([0,0,z0]).mirror([0,0,1]).translate([0,0,2*z0+h]) ^ mf.Manifold.cylinder(h, af/2*0.92, af/2+h, 64).translate([0,0,z0]))
    return m
TAB = {10: dict(p=1.5, af=16.0, cab=7.0, porca=8.0, furo=10.6), 6: dict(p=1.0, af=10.0, cab=4.5, porca=5.0, furo=6.5),
       8: dict(p=1.25, af=13.0, cab=5.5, porca=6.5, furo=8.5)}
FOLGA = 0.15     # folga radial de cada lado (parafuso -0.15, porca +0.15) -> 0.3 total, bom p/ FDM 0.4
def parafuso(d, L, achatado=True):
    """parafuso sextavado: cabeca em z<0, rosca de 0 a L. achatado: 2 faces planas p/ imprimir deitado (mais forte)"""
    t = TAB[d]
    m = rosca(d, t["p"], L, folga=FOLGA) + hexagono(t["af"], t["cab"], -t["cab"])
    if achatado:
        k = d*0.42
        m = m ^ mf.Manifold.cube([d*4, 2*k, L+t["cab"]+2], True).translate([0,0,(L-t["cab"])/2])
        # cabeca tambem achatada na mesma medida -> deita no plano y=-k
    return m
def parafuso_botao(d, L, cab_d=None, cab_h=None, chave=None, achatado=True):
    """parafuso cabeca botao (redonda) com sextavado interno; cabeca em z<0, rosca 0..L"""
    t = TAB[d]; cab_d = cab_d or {10: 16.0, 6: 10.5, 8: 13.0}[d]; cab_h = cab_h or {10: 6.0, 6: 4.0, 8: 5.0}[d]
    chave = chave or {10: 8.0, 6: 5.0, 8: 6.0}[d]
    cab = mf.Manifold.cylinder(cab_h, cab_d/2, cab_d/2 - 1.0, 96).translate([0,0,0]).mirror([0,0,1])   # chanfro em cima
    sx = mf.Manifold.cylinder(cab_h*0.75, chave/np.sqrt(3), chave/np.sqrt(3), 6).translate([0,0,-cab_h-0.01])
    m = rosca(d, t["p"], L, folga=FOLGA) + (cab - sx)
    if achatado:   # uma face plana (y = -0.42d) p/ imprimir deitado: camadas ao longo do parafuso = bem mais forte
        k = d*0.42
        m = m ^ mf.Manifold.cube([cab_d+2, cab_d+2, L+cab_h+2], True).translate([0, -k + (cab_d+2)/2, (L-cab_h)/2])
    return m
def porca(d, af=None, h=None):
    t = TAB[d]; af = af or t["af"]; h = h or t["porca"]
    return hexagono(af, h) - rosca(d, t["p"], h+0.02, folga=FOLGA, interna=True).translate([0,0,-0.01])
def barril(d, diam, comp):
    """porca-barril (cross dowel): cilindro de diametro diam ao longo de X, rosca d no centro ao longo de Z, fenda p/ chave"""
    t = TAB[d]
    c = mf.Manifold.cylinder(comp, diam/2, diam/2, 96).rotate([0,90,0]).translate([-comp/2,0,0])
    c = c - rosca(d, t["p"], diam+2, folga=FOLGA, interna=True).translate([0,0,-diam/2-1])
    c = c - mf.Manifold.cube([1.6, diam*0.6, diam+2], True).translate([comp/2-1.5, 0, 0])   # fenda de orientacao/chave
    return c
def salvar(m, fn): _T(m).export(fn); return fn
if __name__ == "__main__":
    import sys
    out = "/home/lucas/mulbot/mod/teste_fixadores"; import os; os.makedirs(out, exist_ok=True)
    for d, L in ((10, 40), (6, 20)):
        b = parafuso(d, L); print(f"M{d}x{L}", round(b.volume()/1000, 2), "cm3", salvar(b, f"{out}/parafuso_M{d}x{L}.stl"))
        n = porca(d); print(f"porca M{d}", round(n.volume()/1000, 2), salvar(n, f"{out}/porca_M{d}.stl"))
        print("interf parafuso x porca:", round((b ^ n.translate([0,0,10])).volume(), 3))
    br = barril(10, 15, 19); salvar(br, f"{out}/barril_M10.stl"); print("barril", round(br.volume()/1000,2))
def chave_allen(af, longo, curto, folga=0.25):
    """chave Allen em L impressa: sextavado (af - folga) entre faces, braco longo em X, curto em Z; deita sobre face plana"""
    a = af - folga; r = a/np.sqrt(3)
    def braco(L):   # prisma sextavado ao longo de +Z, com chanfro na ponta
        p = mf.Manifold.cylinder(L, r, r, 6).rotate([0,0,30])        # faces planas em y = +-a/2
        ponta = mf.Manifold.cylinder(1.2, r, r*0.8, 6).rotate([0,0,30]).translate([0,0,L])
        return p + ponta
    curto_b = braco(curto).rotate([0,0,0])                            # ao longo de +Z
    longo_b = braco(longo).rotate([0,90,0]).rotate([180,0,0]) if False else braco(longo).rotate([0,90,0])   # ao longo de +X
    canto = mf.Manifold.sphere(r*0.98, 48) ^ mf.Manifold.cube([2*r, a, 2*r], True)
    m = curto_b + longo_b + canto
    # recorta p/ ficar exatamente entre os planos y=+-a/2 (face plana pra deitar na mesa)
    m = m ^ mf.Manifold.cube([longo*3, a, curto*3], True)
    return m
