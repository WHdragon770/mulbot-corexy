# Checa interferencia entre grupos moveis (portico, carro X, mesa) e o quadro em varias poses
import sys, os, itertools; os.environ["ESFERAS"] = "0"; sys.argv = ["x"]
sys.path.insert(0, "/home/lucas/corexy/scripts")
exec(open("/home/lucas/corexy/scripts/cxy.py").read())
QFIX = {"fix_" + n_: q_ for n_, f_, T_, c_, q_ in FIX}
QPEC = {n_: d_["q"] for n_, d_ in PEC.items()}
def g(n):
    if n in QFIX: return {"portico": "portico", "carro": "carro", "mesa": "mesa"}.get(QFIX[n], "fixo")
    if n in QPEC and QPEC[n] != "mundo": return QPEC[n]
    if n.startswith(("rodaY", "buchaY", "suportePortico", "trilhoX", "loucaPortico", "fimCursoX")): return "portico"
    if n.startswith(("carroX", "rodaX", "buchaX", "hotend", "presilhaHotend", "dutoCoreXY", "ventoinha", "ezr", "motorE", "suporteExtrusoraDireta")): return "carro"
    if n.startswith(("mesa", "carroZ", "porcaZ", "bracoMesa", "rodaZ", "buchaZ")): return "mesa"
    if n.startswith(("correia", "bowden")): return "correia"
    return "fixo"
# caixa envolvente pelos 8 cantos (barato); o solido so e montado para pares candidatos (RAM do WSL = 3 GB)
MF = {}; BB = {}; PT = {n: (p, t) for n, p, t, c in P}
for n, p, t, c in P:
    lo, hi = mesh(p).bounds; k = np.array([[x, y, z, 1] for x in (lo[0], hi[0]) for y in (lo[1], hi[1]) for z in (lo[2], hi[2])]) @ t.T
    BB[n] = (k[:, :3].min(0), k[:, :3].max(0))
def mfl(n):
    if n not in MF: MF[n] = peca_mf(*PT[n])
    return MF[n]
G = {n: g(n) for n in BB}
def desloc(grp, dx, dy, dz):
    return {"portico": (0, dy, 0), "carro": (dx, dy, 0), "mesa": (0, 0, dz)}.get(grp, (0, 0, 0))
# pares ignorados (contato proposital / montagem)
IGN = [("porcaZ", "fusoZ"), ("carroY", "trilhoY"), ("carroZ", "trilhoZ"), ("carroHotend", "trilhoX"), ("tampaX", "trilhoX"),
       ("loucaPortico", "suportePortico"), ("loucaFrente", "torreFrente"), ("motorA", "torreTras"), ("motorB", "torreTras"),
       ("motorZ", "baseZ"), ("fusoZ", "baseZ"), ("fimCursoX", "tampaX_chave"), ("fimCursoX", "suportePortico_E"), ("fimCursoY", "carroY_E"), ("fimCursoZ", "bracoMesa_E"), ("rodaZ", "trilhoZ"), ("rodaZ", "fix_M6"), ("buchaZ", "fix_M6"), ("rodaZ", "bracoMesa"), ("buchaZ", "bracoMesa"),
       ("rodaX", "trilhoX"), ("rodaY", "trilhoY"), ("rodaX", "carroX"), ("buchaX", "carroX"), ("rodaX", "buchaX"), ("buchaX", "fix_M6"),
       ("rodaY", "suportePortico"), ("buchaY", "suportePortico"), ("rodaY", "buchaY"), ("buchaY", "fix_M6"), ("rodaX", "fix_M6"), ("rodaY", "fix_M6"),
       ("fimCursoX", "carroX"), ("fimCursoY", "suportePortico_E")]
def ign(a, b):
    return any((a.startswith(x) or ("_" + x) in a) and (b.startswith(y) or ("_" + y) in b) or
               (b.startswith(x) or ("_" + x) in b) and (a.startswith(y) or ("_" + y) in a) for x, y in IGN)
X0 = XC; Y0g = YG; Z0m = ZM
poses = []
# sobrecurso (fora da area 200x200): mesa a >= 10 mm do bico (firmware: Z_SAFE_HOMING + Z_CLEARANCE_FOR_HOMING 10),
# porque as presilhas do vidro sobem 6.4 mm e o duto passa a 2 mm do bico
for xc in (-104, 0, 104):          # fim de curso X aperta em -101.5
    for yg in (-60.9, 47.63, 156.1):
        for zm in (10, 200): poses.append((xc, yg, zm))
for xc in (-100, 100):                       # cantos da area de impressao com o vidro no bico
    for yg in (-52.37, 147.63): poses.append((xc, yg, 0))
achado = {}
nomes = [n for n in BB if G[n] != "correia"]
FOCO = os.environ.get("FOCO")          # ex.: FOCO=rodaZ,buchaZ,bracoMesa -> so pares envolvendo esses prefixos
def foco(a, b): return not FOCO or any(x.startswith(tuple(FOCO.split(","))) or ("_" + FOCO) in x for x in (a, b))
if os.environ.get("POSE"): poses = [poses[int(os.environ["POSE"])]]
if os.environ.get("ZPOSES"): poses = [(0, 47.63, float(z)) for z in os.environ["ZPOSES"].split(",")]
for xc, yg, zm in poses:
    d = {k: np.array(desloc(k, xc - X0, yg - Y0g, -(zm - Z0m))) for k in ("portico", "carro", "mesa", "fixo")}
    for a, b in itertools.combinations(nomes, 2):
        ga, gb = G[a], G[b]
        if ga == gb: continue
        if ign(a, b) or not foco(a, b): continue
        da, db = d[ga], d[gb]
        la, ha = BB[a][0] + da, BB[a][1] + da; lb, hb = BB[b][0] + db, BB[b][1] + db
        if np.any(ha < lb) or np.any(hb < la): continue
        v = (mfl(a).translate(da.tolist()) ^ mfl(b).translate(db.tolist())).volume()
        if v > 1.0:
            k = (a, b)
            if k not in achado or v > achado[k][0]: achado[k] = (round(v, 1), (xc, yg, zm))
for (a, b), (v, ps) in sorted(achado.items(), key=lambda x: -x[1][0]): print(f"{v:9.1f} mm3  {a}  x  {b}   pose {ps}")
print("pares com interferencia:", len(achado), "| poses:", len(poses), "| solidos montados:", len(MF), "de", len(BB))
