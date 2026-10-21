# Colisao das esteiras porta-cabos (os elos mudam de forma em cada pose): elos x resto da maquina e elos x elos, nas poses do colisao.py
# python3 colisao_esteira.py   (rodar o cxy.py antes; env LIM = mm3 minimo reportado, padrao 0.5)
import sys, os, itertools; os.environ["ESFERAS"] = "0"; sys.argv = ["x"]
sys.path.insert(0, "/home/lucas/corexy/scripts")
exec(open("/home/lucas/corexy/scripts/cxy.py").read())
import esteira
LIM = float(os.environ.get("LIM", 0.5))
QFIX = {"fix_" + n_: q_ for n_, f_, T_, c_, q_ in FIX}
QPEC = {n_: d_["q"] for n_, d_ in PEC.items()}
def g(n):
    if n in QFIX: return {"portico": "portico", "carro": "carro", "mesa": "mesa"}.get(QFIX[n], "fixo")
    if n in QPEC and QPEC[n] != "mundo": return QPEC[n]
    if n.startswith(("rodaY", "buchaY", "suportePortico", "trilhoX", "loucaPortico", "fimCursoX", "pontaFixaX", "caboEsteira_XY")): return "portico"
    if n.startswith(("carroX", "rodaX", "buchaX", "hotend", "presilhaHotend", "dutoCoreXY", "ventoinha", "ezr", "motorE", "suporteExtrusoraDireta")): return "carro"
    if n.startswith(("mesa", "carroZ", "porcaZ", "bracoMesa", "rodaZ", "buchaZ")): return "mesa"
    if n.startswith(("correia", "bowden", "caboEsteira")): return "cabo"
    return "fixo"
def desloc(grp, dx, dy, dz): return {"portico": (0, dy, 0), "carro": (dx, dy, 0), "mesa": (0, 0, dz)}.get(grp, (0, 0, 0))
ENC = ("bandeja", "pontaFixa", "bracoEsteiraX", "suporteEsteiraY")      # o elo apoia/encaixa nessas (contato de projeto, so reporta se entrar mais que LIM)
MF, BB, PT = {}, {}, {n: (p, t) for n, p, t, c in P}
for n, p, t, c in P:
    if n.startswith(("eloX", "eloY")): continue
    lo, hi = mesh(p).bounds; k = np.array([[x, y, z, 1] for x in (lo[0], hi[0]) for y in (lo[1], hi[1]) for z in (lo[2], hi[2])]) @ t.T
    BB[n] = (k[:, :3].min(0), k[:, :3].max(0))
def mfl(n):
    if n not in MF: MF[n] = peca_mf(*PT[n])
    return MF[n]
G = {n: g(n) for n in BB}
ELO = peca_mf(f"{DER}/elo_esteira.stl", np.eye(4)); elo_bb = mesh(f"{DER}/elo_esteira.stl").bounds
def bb_T(T):
    lo, hi = elo_bb; k = np.array([[x, y, z, 1] for x in (lo[0], hi[0]) for y in (lo[1], hi[1]) for z in (lo[2], hi[2])]) @ T.T
    return k[:, :3].min(0), k[:, :3].max(0)
poses = []
for xc in (-104, 0, 104):
    for yg in (-60.9, 47.63, 156.1):
        for zm in (10, 200): poses.append((xc, yg, zm))
for xc in (-100, 100):
    for yg in (-52.37, 147.63): poses.append((xc, yg, 0))
achado = {}
for xc, yg, zm in poses:
    d = {k: np.array(desloc(k, xc - XC, yg - YG, -(zm - ZM))) for k in ("portico", "carro", "mesa", "fixo", "cabo")}
    els = [(f"eloX_{k}", tr((0, yg, 0)) @ T_) for k, T_ in enumerate(esteira.esteira_X(xc)[0])] + \
          [(f"eloY_{k}", T_) for k, T_ in enumerate(esteira.esteira_Y(yg)[0])]
    em = {n: ELO.transform(T_[:3].tolist()) for n, T_ in els}; eb = {n: bb_T(T_) for n, T_ in els}
    for a, _ in els:
        la, ha = eb[a]
        for b in BB:
            if G[b] == "cabo": continue
            lb, hb = BB[b][0] + d[G[b]], BB[b][1] + d[G[b]]
            if np.any(ha < lb) or np.any(hb < la): continue
            v = (em[a] ^ mfl(b).translate(d[G[b]].tolist())).volume()
            if v > (LIM * 4 if b.startswith(ENC) else LIM): achado[(a.split("_")[0], b)] = max(v, achado.get((a.split("_")[0], b), 0)); print("  ", (xc, yg, zm), a, "x", b, round(v, 2))
    for (a, _), (b, _) in itertools.combinations(els, 2):
        if a[:4] != b[:4]: continue
        la, ha = eb[a]; lb, hb = eb[b]
        if np.any(ha < lb) or np.any(hb < la): continue
        v = (em[a] ^ em[b]).volume()
        if v > LIM: achado[(a, b)] = max(v, achado.get((a, b), 0)); print("  ", (xc, yg, zm), a, "x", b, round(v, 2))
print(f"esteira: pares com interferencia: {len(achado)} | poses: {len(poses)} | elos: {len(els)}")
for k, v in sorted(achado.items(), key=lambda kv: -kv[1]): print("  ", k, round(v, 1), "mm3")
