# Interferencia parada (pose padrao) das pecas listadas contra TODAS as outras, inclusive do mesmo grupo
# (o colisao.py so cruza grupos moveis x quadro). Uso depois de mexer no desenho de uma peca.
# python3 estatica.py peca1 [peca2 ...]   (prefixo do nome na montagem)
import sys, os; os.environ["ESFERAS"] = "0"; ALVO = tuple(sys.argv[1:]); sys.argv = ["x"]
sys.path.insert(0, "/home/lucas/corexy/scripts")
import io, contextlib
with contextlib.redirect_stdout(io.StringIO()):
    exec(open("/home/lucas/corexy/scripts/cxy.py").read())
BB = {}
for n, p, t, c in P:
    lo, hi = mesh(p).bounds; k = np.array([[x, y, z, 1] for x in (lo[0], hi[0]) for y in (lo[1], hi[1]) for z in (lo[2], hi[2])]) @ t.T
    BB[n] = (k[:, :3].min(0), k[:, :3].max(0), p, t)
achou = 0
for a in [n for n in BB if n.startswith(ALVO)]:
    la, ha, pa, ta = BB[a]; ma = None
    for b, (lb, hb, pb, tb) in BB.items():
        if b == a or np.any(ha < lb) or np.any(hb < la): continue
        if ma is None: ma = peca_mf(pa, ta)
        v = (ma ^ peca_mf(pb, tb)).volume()
        if v > 1.0: print(f"{v:9.1f} mm3  {a}  x  {b}"); achou += 1
print("pares com interferencia:", achou)
