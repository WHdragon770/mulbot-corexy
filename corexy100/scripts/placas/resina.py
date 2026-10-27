# Pecas de RESINA da CoreXY (Photon Mono M7 Pro: 223,78 x 126,38 x 230): STL individual + 1 placa pronta com tudo nas quantidades
# Tudo SEM SUPORTE, direto na plataforma: roldana deitada (eixo em pe; roletes recuados 0,3 das faces e presos por pontes, a camada
# de base superexposta so pega as pistas), buchas no sextavado, fuso em pe.
# python3 resina.py <pasta_orient> <pasta_saida>
import sys, os, json, numpy as np, trimesh
SRC, DST = sys.argv[1], sys.argv[2]
INFO = json.load(open(f"{SRC}/orienta.json"))
LX, LY = 223.78, 126.38
ks = {k: v for k, v in INFO.items() if "Resina" in v["conj"]}
os.makedirs(f"{DST}/STL individuais", exist_ok=True); os.makedirs(f"{DST}/Alternativa - fuso Z em resina", exist_ok=True)
for k, v in ks.items():
    alt = "Resina (alternativa)" in v["conj"]
    d = f"{DST}/Alternativa - fuso Z em resina" if alt else f"{DST}/STL individuais"
    trimesh.load(f"{SRC}/{k}.stl").export(f"{d}/{v['nome']} [{v['qtd']}x].stl")
# placa: 15 roldanas em grade 5 x 3 (passo 39) + buchas numa coluna ao lado
rol = [k for k in ks if "roldana" in k][0]; buchas = [k for k in ks if "bucha" in k]
m_rol = trimesh.load(f"{SRC}/{rol}.stl"); pecas = []
n = ks[rol]["qtd"]; cols = 5
for i in range(n):
    c, r = i % cols, i // cols
    pecas.append(m_rol.copy().apply_translation([-LX / 2 + 4 + 17 + c * 39, -LY / 2 + 6 + 17 + r * 39, 0]))
y = -LY / 2 + 8; xb = -LX / 2 + 4 + 5 * 39 + 4
for k in buchas:
    m = trimesh.load(f"{SRC}/{k}.stl")
    for _ in range(ks[k]["qtd"]):
        pecas.append(m.copy().apply_translation([xb + m.extents[0] / 2, y + m.extents[1] / 2, 0])); y += m.extents[1] + 6
pl = trimesh.util.concatenate(pecas); b = pl.bounds
assert b[0][0] >= -LX / 2 and b[1][0] <= LX / 2 and b[0][1] >= -LY / 2 and b[1][1] <= LY / 2, b
pl.export(f"{DST}/PLACA PRONTA - 15 roldanas + 5 buchas (M7 Pro).stl")
print("placa resina", len(pecas), "pecas, ocupa", (b[1] - b[0]).round(1), "de", LX, LY)
