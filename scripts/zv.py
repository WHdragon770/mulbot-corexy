# Eixo Z com guia em V impressa (substitui trilho de esferas + carro Z da Mulbot)
# - trilho V faz parte da viga Z; 3 roldanas no braco da mesa (2 fixas por fora, 1 excentrica por dentro)
# - roldana com rolamento de roletes impresso no lugar (print-in-place): roletes em barril prendem axialmente
# - fuso e porca com rosca trapezoidal parametrica (perfil medido do DL1-02-06: d 18.4, raiz 15.86, passo 4)
# Duas versoes de folga: MAT=fdm (padrao) ou MAT=resina
import os, numpy as np, trimesh, manifold3d as mf
from base import M, caixa, cil, mesh, DER, tr

TOL = {"fdm":    dict(g_rol=0.30, f_rosca=0.20, furo6=3.25, bucha=0.20),
       "resina": dict(g_rol=0.15, f_rosca=0.08, furo6=3.15, bucha=0.10)}
MAT = os.environ.get("MAT", "fdm")

# ---------- guia em V (secao no plano x/y; h = y - yw)
TIP = 13.0                       # meia-largura teorica do V (ponta truncada em 12.5)
RG, HG, HW = 13.5, 3.5, 4.5      # roldana: raio do fundo do canal, altura do flanco, meia-largura
RO = RG + HG                     # raio externo da roldana (17)
XCW = TIP + RG                   # distancia eixo do trilho -> eixo da roldana (26.5)
FR, BK = 5.0, 6.0                # trilho: espessura na frente / atras do plano das roldanas
def secao_v(x0, yw, ycorpo, larg_corpo=9.525):
    """trilho V + corpo da viga ate ycorpo (atras), poligono CCW"""
    t = TIP - 0.5
    meia = [(8.5, yw - FR), (8.5, yw - HW), (t, yw - 0.5), (t, yw + 0.5), (8.5, yw + HW), (8.5, yw + BK),
            (larg_corpo, yw + BK), (larg_corpo, ycorpo)]
    pts = [(x0 + x, y) for x, y in meia] + [(x0 - x, y) for x, y in meia[::-1]]
    p = np.array(pts); a = np.sum(p[:, 0] * np.roll(p[:, 1], -1) - np.roll(p[:, 0], -1) * p[:, 1])
    if a < 0: pts = pts[::-1]
    return mf.CrossSection([pts])
def viga_v(x0, yw, ycorpo, z0, z1): return secao_v(x0, yw, ycorpo).extrude(z1 - z0).translate([0, 0, z0])

# ---------- roldana com rolamento de roletes impresso (eixo = z local, centro na origem)
PR, RR0, RR1, NROL = 8.0, 2.0, 1.2, 10       # raio primitivo, raio do rolete no meio / nas pontas, n de roletes
def _rr(h): return RR0 - (RR0 - RR1) * abs(h) / HW
def _rev(prof, n=96):
    p = np.array(prof, float); a = np.sum(p[:, 0] * np.roll(p[:, 1], -1) - np.roll(p[:, 0], -1) * p[:, 1])
    return mf.CrossSection([prof if a > 0 else prof[::-1]]).revolve(n)
def roldana(mat=MAT, partes=False):
    g = TOL[mat]["g_rol"]; hs = np.linspace(-HW, HW, 13)
    ext = [(PR + _rr(h) + g, h) for h in hs]                                  # pista externa (furo da roldana)
    corpo = [(RO, -HW), (RO, -HG), (RG, 0.0), (RO, HG), (RO, HW)] + ext[::-1]
    pista_int = [(TOL[mat]["furo6"], -HW), (TOL[mat]["furo6"], HW)] + [(PR - _rr(h) - g, h) for h in hs[::-1]]
    rol = [(1e-3, -HW)] + [(_rr(h), h) for h in hs] + [(1e-3, HW)]
    rolete = _rev(rol, 32)
    roletes = [rolete.translate([PR * np.cos(a), PR * np.sin(a), 0]) for a in np.arange(NROL) * 2 * np.pi / NROL]
    R = dict(roda=_rev(corpo), pista=_rev(pista_int), roletes=mf.Manifold.batch_boolean(roletes, mf.OpType.Add))
    return R if partes else R["roda"] + R["pista"] + R["roletes"]

# ---------- roldana p/ RESINA em 1 peca so (print-in-place): folga maior que lava bem, roletes recuados das faces
# (a 1a camada superexposta nao cola rolete na pista) e pontes de quebra ligando rolete -> pistas nas 2 pontas,
# para cada rolete nascer preso (nao sai flutuando nem gruda no FEP). Lavar, girar com forca (quebra as pontes), lavar de novo girando, curar.
G_RES, RECUO, PONTE = 0.20, 0.30, 0.40          # folga radial, recuo do rolete em cada face, lado da ponte (mm)
def roldana_resina(partes=False):
    g = G_RES; hs = np.linspace(-HW, HW, 13); hr = np.linspace(-HW + RECUO, HW - RECUO, 13)
    ext = [(PR + _rr(h) + g, h) for h in hs]
    corpo = [(RO, -HW), (RO, -HG), (RG, 0.0), (RO, HG), (RO, HW)] + ext[::-1]
    pista_int = [(TOL["resina"]["furo6"], -HW), (TOL["resina"]["furo6"], HW)] + [(PR - _rr(h) - g, h) for h in hs[::-1]]
    rolete = _rev([(0.0, hr[0])] + [(_rr(h), h) for h in hr] + [(0.0, hr[-1])], 32)
    ang = np.arange(NROL) * 2 * np.pi / NROL
    roletes = [rolete.translate([PR * np.cos(a), PR * np.sin(a), 0]) for a in ang]
    rmax = _rr(HW - RECUO) + g + 0.6                       # ponte entra 0.6 mm em cada pista
    pontes = []
    for a in ang:
        for z0 in (-HW + RECUO - 0.1, HW - RECUO - PONTE + 0.1):   # 0.1 fora da ponta do rolete (sem face coplanar no polo)
            b = mf.Manifold.cube([2 * rmax, PONTE, PONTE]).translate([PR - rmax, -PONTE / 2, z0])
            pontes.append(b.rotate([0, 0, float(np.degrees(a))]))
    R = dict(roda=_rev(corpo), pista=_rev(pista_int), roletes=mf.Manifold.batch_boolean(roletes, mf.OpType.Add),
             pontes=mf.Manifold.batch_boolean(pontes, mf.OpType.Add))
    return R if partes else R["roda"] + R["pista"] + R["roletes"] + R["pontes"]

# ---------- bucha excentrica tipo espacador (X e Y): sextavado de 6 mm entre a placa e a roldana (chave entra pelo lado)
# + ressalto que entra na placa. Eixo z local: ressalto z -Lb..0, sextavado z 0..ESP; furo M6 deslocado de EXC em +x
ESP = 6.0
def bucha_esp(Lb, mat=MAT):
    sx = mf.Manifold.cylinder(ESP - 0.6, 8.08, 8.08, 6)                       # sextavado 14 mm entre faces
    sx += mf.Manifold.cylinder(0.6, 5.5, 5.5, 48).translate([0, 0, ESP - 0.6])  # colar: aperta so a pista interna
    corpo = mf.Manifold.cylinder(Lb, 6.0, 6.0, 64).translate([0, 0, -Lb])
    return sx + corpo - mf.Manifold.cylinder(Lb + ESP + 10, TOL[mat]["furo6"], TOL[mat]["furo6"], 48).translate([EXC, 0, -Lb - 5])

# ---------- bucha excentrica (eixo z local: sextavado em z<0, corpo z 0..L)
EXC = 0.75
def bucha(L, mat=MAT):
    sx = mf.Manifold.cylinder(4.0, 8.08, 8.08, 6).translate([0, 0, -4.0])      # sextavado 14 mm entre faces
    corpo = mf.Manifold.cylinder(L, 6.0, 6.0, 64)
    return sx + corpo - mf.Manifold.cylinder(L + 10, TOL[mat]["furo6"], TOL[mat]["furo6"], 48).translate([EXC, 0, -5])

# ---------- rosca trapezoidal (campo de altura em coordenadas cilindricas)
RC, RRAIZ, PASSO = 9.2, 7.93, 4.0
def _perfil_tr(u):
    u = u % 1.0
    if u < 0.30: return 1.0
    if u < 0.50: return 1.0 - (u - 0.30) / 0.20
    if u < 0.80: return 0.0
    return (u - 0.80) / 0.20
def rosca_tr(cx, cy, z0, z1, folga, interna=False, nseg=128, chanfro=True):
    """macho (interna=False: raio -folga) ou cavidade da porca (interna=True: raio +folga) entre z0 e z1.
    Fase pela cota z do mundo -> fuso e porca gerados no lugar sempre casam"""
    s = 1 if interna else -1
    rc, rr = RC + s * folga, RRAIZ + s * folga
    if interna: rc += 0.05                                      # alivio na crista da porca
    nz = max(int((z1 - z0) / (PASSO / 40)), 4)
    th = np.linspace(0, 2 * np.pi, nseg, endpoint=False); zs = np.linspace(z0, z1, nz + 1)
    Z, T = np.meshgrid(zs, th, indexing="ij")
    u = (Z - PASSO * T / (2 * np.pi)) / PASSO
    R = rr + (rc - rr) * np.vectorize(_perfil_tr)(u)
    if chanfro and not interna:
        cz = np.minimum(Z - z0, z1 - Z); R = np.minimum(R, rr + np.maximum(cz, 0) * 1.0)
    V = np.c_[(cx + R * np.cos(T)).ravel(), (cy + R * np.sin(T)).ravel(), Z.ravel()]
    i = np.arange(nz)[:, None] * nseg; k = np.arange(nseg)[None, :]
    a = (i + k).ravel(); b = (i + (k + 1) % nseg).ravel(); c = a + nseg; e = b + nseg
    F = np.r_[np.c_[a, b, e], np.c_[a, e, c]]
    V = np.vstack([V, (cx, cy, z0), (cx, cy, z1)]); c0, c1 = len(V) - 2, len(V) - 1
    kk = np.arange(nseg)
    F = np.r_[F, np.c_[np.full(nseg, c0), (kk + 1) % nseg, kk], np.c_[np.full(nseg, c1), nz * nseg + kk, nz * nseg + (kk + 1) % nseg]]
    m = trimesh.Trimesh(V, F, process=True); m.fix_normals()
    return M(m)

RBORE = 3.96                     # furo central do fuso Mulbot
ZHUB = 23.0                      # trecho do cubo (acoplamento no eixo do motor) mantido do DL1-02-06
def fuso(Tw, mat=MAT):
    """fuso no mundo: cubo da Mulbot (DL1-02-06_longo transformado por Tw) + rosca nova. Devolve (manifold, eixo)"""
    m = trimesh.load(f"{DER}/DL1-02-06_longo.stl", process=True).copy(); m.merge_vertices(); m.apply_transform(Tw)
    lo, hi = m.bounds; cx, cy = (lo[:2] + hi[:2]) / 2
    cubo = M(m) ^ caixa((cx - 30, cy - 30, lo[2] - 1), (cx + 30, cy + 30, lo[2] + ZHUB))
    r = rosca_tr(cx, cy, lo[2] + ZHUB - 0.5, hi[2], TOL[mat]["f_rosca"])
    r -= cil((cx, cy, lo[2] + ZHUB - 2), (cx, cy, hi[2] + 1), RBORE, 48)
    return cubo + r, (cx, cy, lo[2], hi[2])
def porca(Tw, eixo, mat=MAT):
    """porca DL1-04-06 (furos/flange originais) com a rosca refeita no lugar"""
    m = mesh("DL1-04-06").copy(); m.apply_transform(Tw); lo, hi = m.bounds
    cx, cy = eixo[:2]
    p = M(m) + cil((cx, cy, lo[2]), (cx, cy, hi[2]), RC + 0.6, 96)
    return p - rosca_tr(cx, cy, lo[2] - 1, hi[2] + 1, TOL[mat]["f_rosca"], interna=True)

# ---------- fuso em 2 metades p/ resina (cabe numa Photon Mono M7 Pro: Z 230): pino D no furo central
PINO_L = 24.0
def furo_d(cx, cy, z0, z1, r, folga):
    """furo/pino em D (raio r, chato a 0.7 r) ao longo de z"""
    c = cil((cx, cy, z0), (cx, cy, z1), r + folga, 48)
    return c - caixa((cx + 0.7 * r + folga, cy - 20, z0 - 1), (cx + 20, cy + 20, z1 + 1))
def divide_fuso(f, eixo, zcorte, mat="resina"):
    cx, cy, z0, z1 = eixo; fo = TOL[mat]["bucha"]
    a = f ^ caixa((cx - 40, cy - 40, z0 - 1), (cx + 40, cy + 40, zcorte))
    b = f ^ caixa((cx - 40, cy - 40, zcorte), (cx + 40, cy + 40, z1 + 1))
    sd = furo_d(cx, cy, zcorte - PINO_L / 2 - 1, zcorte + PINO_L / 2 + 1, 4.6, fo)
    a, b = a - sd, b - sd
    pino = furo_d(cx, cy, zcorte - PINO_L / 2, zcorte + PINO_L / 2, 4.6, 0.0)
    return a, b, pino
