# Etapa 1: uniao trilhos Y <-> conectores frontal/traseiro com M10 impresso + porca-barril
import sys, os, json; os.environ.setdefault("ZX","215"); sys.argv=[sys.argv[0]]; sys.path.insert(0,"/home/lucas/mulbot/scripts")
exec(open("/home/lucas/mulbot/scripts/montagem.py").read())
import manifold3d as mf
from fixadores import parafuso_botao, barril, salvar, rosca, TAB
OUT = "/home/lucas/mulbot/mod"; os.makedirs(f"{OUT}/stl", exist_ok=True)
def MW(n):
    m = mesh(PART[n]).copy(); m.apply_transform(T[n])
    return mf.Manifold(mf.Mesh(vert_properties=np.asarray(m.vertices, np.float32), tri_verts=np.asarray(m.faces, np.uint32)))
def cil(p0, p1, r, n=64):
    p0 = np.array(p0, float); p1 = np.array(p1, float); d = p1-p0; L = np.linalg.norm(d); z = d/L
    x = np.cross(z, [0,0,1.0]) if abs(z[2]) < 0.9 else np.cross(z, [1.0,0,0]); x /= np.linalg.norm(x); y = np.cross(z, x)
    M = np.column_stack([x, y, z, p0])
    return mf.Manifold.cylinder(L, r, r, n).transform(M.tolist())
def caixa(a, b):
    a = np.minimum(a, b); b = np.maximum(a, b) if False else b
    return mf.Manifold.cube((np.array(b)-np.array(a)).tolist()).translate(list(a))
OPS = {}     # nome -> {"add": [...], "sub": [...]}
FIX = []     # (nome, stl, T, cor)
def op(n, k, m): OPS.setdefault(n, {"add": [], "sub": []})[k].append(m)
def Tlocal(n): return np.linalg.inv(T[n])
D = 10; FURO = 10.6; BAR_D = 14.0; BAR_FURO = 14.4
def junta_barril(cab, nut, P, u, e, barril_dir, barril_ini, barril_comp, L):
    """P: ponto no plano da face de apoio da cabeca (na peca cab); u: direcao do parafuso (para dentro);
    e: distancia da face de contato (cab|nut) ate o centro do barril, medida a partir de Pc = P + u*esp_cab"""
    P = np.array(P, float); u = np.array(u, float)
    op(cab, "sub", cil(P - u*1, P + u*(L+1), FURO/2))
    op(nut, "sub", cil(P - u*1, P + u*(L+3), FURO/2))
    C = P + u*(L - 6.0)                       # centro do barril: 6 mm antes da ponta do parafuso
    bd = np.array(barril_dir, float)
    op(nut, "sub", cil(C + bd*barril_ini, C + bd*(barril_ini+barril_comp+1), BAR_FURO/2))
    # parafuso: cabeca no ponto P (apoiada na face), eixo u
    z = u; x = np.cross(z, bd); x /= np.linalg.norm(x); y = np.cross(z, x)
    Tb = np.eye(4); Tb[:3,:3] = np.column_stack([-x, -y, z]); Tb[:3,3] = P    # fase da rosca casada com o barril
    FIX.append((f"M10x{L}_{cab}_{nut}_{len(FIX)}", f"parafuso_M10x{L}", Tb, "azul"))
    # barril: eixo ao longo de bd, rosca ao longo de u
    zb = bd; xb = u; yb = np.cross(zb, xb)
    Tr = np.eye(4); Tr[:3,:3] = np.column_stack([zb, yb, xb]) @ np.array([[0,0,1],[0,1,0],[1,0,0.]]).T if False else np.eye(3)
    # modelo do barril: cilindro ao longo de X local, rosca ao longo de Z local -> X->bd, Z->u
    Xl = bd; Zl = u; Yl = np.cross(Zl, Xl)
    Tr = np.eye(4); Tr[:3,:3] = np.column_stack([Xl, Yl, Zl]); Tr[:3,3] = C + bd*(barril_ini + barril_comp/2)
    FIX.append((f"barril_{nut}_{len(FIX)}", "barril_M10x%d" % round(barril_comp), Tr, "azul"))
# ---------------- G1: trilhos <-> conectores
YF_, YB_ = -137.5, 137.5
for xr, tr in ((-RX, "trilhoY_E"), (RX, "trilhoY_D")):
    inward = 1 if xr < 0 else -1          # da face interna do trilho (barril entra por dentro)
    xin = xr + inward*9.5                # face interna (x8 local) -> lado de dentro
    for z in (9.53, 41.27):
        # frontal: cabeca na face frontal do conector (Y=-156.55), parafuso para +Y
        junta_barril("conectorY_frente", tr, (xr, -156.55, z), (0,1,0), 16, (-inward,0,0), -9.5*(-inward)*0 - 9.5, 19.0, 40)
        junta_barril("conectorY_tras", tr, (xr, 156.55, z), (0,-1,0), 16, (-inward,0,0), -9.5, 19.0, 40)
    # preenche o ultimo bolsao do trilho na ponta frontal (barril precisa de material)
    yl0, yl1 = -165.5, -139.5      # mundo: ponta frontal Y -137.5 ; bolsao local y 140..165 -> mundo
    if tr == "trilhoY_E": op(tr, "add", caixa((-78.88, -128.0, 8.5), (-63.0, -101.5, 38.0)))
    else:                 op(tr, "add", caixa((63.0, -128.0, 8.5), (78.94, -101.5, 38.0)))
# ---------------- aplicar
res = {}
for n, o in OPS.items():
    m = MW(n)
    for a in o["add"]: m = m + a
    for s_ in o["sub"]: m = m - s_
    Ti = Tlocal(n); m = m.transform(Ti[:3,:4].tolist())
    fn = f"{OUT}/stl/{os.path.basename(PART[n])[:-4] if PART[n].startswith('/') else PART[n]}.stl"
    salvar(m, fn); res[n] = fn; print("modificada", n, "->", fn, round(m.volume()/1000,1), "cm3")
# fixadores unicos
os.makedirs(f"{OUT}/fixadores", exist_ok=True)
salvar(parafuso_botao(10, 40), f"{OUT}/fixadores/parafuso_M10x40.stl")
salvar(barril(10, BAR_D, 19.0), f"{OUT}/fixadores/barril_M10x19.stl")
json.dump(dict(pecas=res, fix=[(a, f"{OUT}/fixadores/{b}.stl", np.asarray(c).tolist(), d) for a, b, c, d in FIX]), open(f"{OUT}/etapa1.json","w"))
print(len(FIX), "fixadores")
