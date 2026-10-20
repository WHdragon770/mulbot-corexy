# Fixadores impressos: interferencia com tudo (exceto a propria porca/barril), na pose de referencia
import sys, os, itertools; os.environ["ESFERAS"] = "0"; sys.argv = ["x"]
sys.path.insert(0, "/home/lucas/corexy/scripts")
exec(open("/home/lucas/corexy/scripts/cxy.py").read())
# caixa envolvente pelos 8 cantos; solido so para pares candidatos (RAM do WSL = 3 GB)
MF = {}; BB = {}; PT = {}
for n, p, t, c in P:
    if n.startswith(("correia", "bowden")): continue
    lo, hi = mesh(p).bounds; k = np.array([[x, y, z, 1] for x in (lo[0], hi[0]) for y in (lo[1], hi[1]) for z in (lo[2], hi[2])]) @ t.T
    BB[n] = (k[:, :3].min(0), k[:, :3].max(0)); PT[n] = (p, t)
def mfl(n):
    if n not in MF: MF[n] = peca_mf(*PT[n])
    return MF[n]
fx = [n for n in BB if n.startswith("fix_")]
ruim = []
for a in fx:
    base = a[4:].replace("barril_", "").replace("porca_", "")
    for b_ in BB:
        if b_ == a: continue
        if b_.startswith("fix_") and b_[4:].replace("barril_", "").replace("porca_", "") == base: continue
        la, ha = BB[a]; lb, hb = BB[b_]
        if np.any(ha < lb) or np.any(hb < la): continue
        v = (mfl(a) ^ mfl(b_)).volume()
        if v > 1.0: ruim.append((round(v, 1), a, b_))
    MF.pop(a, None)                       # rosca pesa: descarta o fixador ja checado
for r in sorted(ruim, reverse=True): print(r)
print("problemas:", len(ruim), "de", len(fx), "fixadores")
