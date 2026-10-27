# confere a mesa (aquecida ou nao): interferencia entre as pecas da mesa e se a placa/vidro apoiam no localizador
import sys, json, itertools, numpy as np
sys.path.insert(0, "/home/lucas/corexy100/scripts")
from base import peca_mf, caixa
J = {j["nome"]: j for j in json.load(open(sys.argv[1] if len(sys.argv) > 1 else "/home/lucas/corexy100/out/cxy.json"))}
N = [n for n in J if n.startswith("mesa_") or n.startswith("bracoMesa")]
G = {n: peca_mf(J[n]["stl"], np.array(J[n]["T"])) for n in N}
ruim = 0
for a, b in itertools.combinations(N, 2):
    if a.startswith("mesa_mola") or b.startswith("mesa_mola") or "porcaPresilha" in a + b or "knob" in a + b: continue   # mola/rosca encaixadas
    v = (G[a] ^ G[b]).volume()
    if v > 0.05: print(f"  {a} x {b}: {v:.2f} mm3"); ruim += 1
for n in ("mesa_aquecida", "mesa_vidro"):
    if n not in G: continue
    z0 = G[n].bounding_box()[2]
    enc = [k for k in N if k != n and (G[k] ^ caixa((-200, -200, z0 - 0.3), (200, 200, z0))).volume() > 1 and k.startswith(("mesa_localizador", "mesa_aquecida"))]
    print(n, "apoia em:", enc)
print("interferencias:", ruim)
