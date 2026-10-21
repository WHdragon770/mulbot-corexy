# Recupera a rotacao (montagem -> impressao) de cada peca comparando o STL da montagem (stl_impressao) com o orientado
# (mesma ordem de triangulos: o orienta.py so aplica transformacao). Salva scripts/impressao.json {peca: R 3x3 em linhas}
import sys, os, glob, re, json, numpy as np, trimesh
SRC, ORI, OUT = sys.argv[1], sys.argv[2], sys.argv[3]
res = {}
for f in sorted(glob.glob(f"{SRC}/**/*.stl", recursive=True)):
    if "Parafusos" in f or "Resina" in f or "07 Rold" in f: continue
    nome = re.match(r"(.*) \[\d+x\]\.stl", os.path.basename(f)).group(1)
    g = f"{ORI}/{os.path.relpath(os.path.dirname(f), SRC)}/{nome}.stl"
    a = trimesh.load(f, process=False).triangles.reshape(-1, 3); b = trimesh.load(g, process=False).triangles.reshape(-1, 3)
    if len(a) != len(b): print("??", nome); continue
    A = a - a.mean(0); B = b - b.mean(0)
    U, s, Vt = np.linalg.svd(A.T @ B); D = np.diag([1, 1, np.sign(np.linalg.det(U @ Vt))])
    R = (U @ D @ Vt).T                                      # b = R a
    Rr = np.round(R); ok = np.allclose(R, Rr, atol=1e-3) and abs(abs(np.linalg.det(Rr)) - 1) < 1e-6
    res[nome] = (Rr if ok else R).round(6).tolist()
    up = (np.linalg.inv(R) @ [0, 0, 1]).round(3)            # direcao do mundo que fica pra cima na impressao
    print(f"{nome:32s} {'eixos' if ok else 'OBLIQUA'} cima(mundo)={up}")
json.dump(res, open(OUT, "w"), indent=0)
