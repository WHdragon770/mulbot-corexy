# Orientacao de impressao de cada STL do "02 STL" (saida do stl_impressao.py): escolhe a face que vai na mesa
# STL do repo Mulbot ja vem na posicao de impressao do projetista -> so assenta. Resto: candidatos = faces do casco convexo + eixos,
# nota = balanco (>45 graus, fora da mesa) - contato com a mesa + altura (bedslinger: peca alta balanca). FORCA = escolha manual.
# python3 orienta.py <pasta_stl> <pasta_saida>   -> <saida>/<conjunto>/<peca>.stl assentado em z=0 + orienta.json
import sys, os, glob, json, re, numpy as np, trimesh
from trimesh.geometry import align_vectors
SRC, DST = sys.argv[1], sys.argv[2]
REPO = "/home/lucas/mulbot/repo/MODELS"
MESA = 255.0                                     # Kobra X 260 x 260 x 260, 2,5 mm de margem
# forca.json: {"manual": {peca: [ax, ay, az]} aplicado ao STL como sai do stl_impressao.py, "depois": {peca: [ax, ay, az]} aplicado depois do automatico}
FJ = json.load(open(os.path.join(os.path.dirname(__file__), "forca.json")))
FORCA, DEPOIS, CUNHAS = FJ["manual"], FJ["depois"], FJ.get("cunhas", {})
SO = [x for x in os.environ.get("SO", "").split(",") if x]
# impressao_rot.json: rotacao fixa (montagem -> impressao) das pecas novas; o desenho sem suporte (scripts/semsup.py) depende dela
IMP = {k: np.array(v) for k, v in json.load(open(os.path.join(os.path.dirname(__file__), "impressao_rot.json"))).items()}        # SO=peca1,peca2 refaz so essas (mantem o resto do orienta.json)

def avalia(m):
    z0 = m.bounds[0][2]; n = m.face_normals; a = m.area_faces
    zf = m.vertices[m.faces][:, :, 2].max(axis=1)
    cont = a[(n[:, 2] < -0.985) & (zf < z0 + 0.05)].sum()
    bal = (a * -n[:, 2])[(n[:, 2] < -0.707) & (zf > z0 + 0.3)].sum()
    return cont, bal, m.extents[2]

def assenta(m):
    """gira em Z pra menor retangulo, centra em XY, z0 = 0; deixa o lado maior em X"""
    T2, ext = trimesh.bounds.oriented_bounds_2D(m.vertices[:, :2])
    R = np.eye(4); R[:2, :2] = T2[:2, :2]; R[:2, 3] = T2[:2, 2]
    m.apply_transform(R)
    if m.extents[1] > m.extents[0]: m.apply_transform(trimesh.transformations.rotation_matrix(np.pi / 2, [0, 0, 1]))
    b = m.bounds; m.apply_translation([-(b[0][0] + b[1][0]) / 2, -(b[0][1] + b[1][1]) / 2, -b[0][2]])
    return m

def cabe(m):
    x, y, z = m.extents
    return z <= MESA and (max(x, y) <= MESA or (x + y) / np.sqrt(2) <= MESA - 5)

def orienta(m, nome):
    if nome in IMP and not nome.startswith("DL1-"):
        T = np.eye(4); T[:3, :3] = IMP[nome]; m.apply_transform(T); return m, "fixa (impressao_rot)"
    if nome in FORCA:                            # [ax, ay, az] em graus (ordem X, Y, Z)
        a = np.radians(FORCA[nome]); m.apply_transform(trimesh.transformations.euler_matrix(*a, "sxyz")); return m, "manual"
    h = m.convex_hull
    cand = [h.facets_normal[i] for i in np.argsort(h.facets_area)[::-1][:24]] + list(np.vstack([np.eye(3), -np.eye(3)]))
    melhor = None
    for nv in cand:
        R = align_vectors(nv, [0, 0, -1]); mm = m.copy(); mm.apply_transform(R)
        if not cabe(assenta(mm.copy())): continue
        cont, bal, alt = avalia(mm)
        larg = min(mm.extents[0], mm.extents[1])
        nota = bal - 1.0 * cont + 0.5 * alt * min(larg, 30) + (2000 if alt > 3 * larg and alt > 60 else 0)
        if melhor is None or nota < melhor[0]: melhor = (nota, R, cont, bal)
    m.apply_transform(melhor[1]); return m, f"auto cont={melhor[2]:.0f} bal={melhor[3]:.0f}"

info = json.load(open(f"{DST}/orienta.json")) if SO else {}
for f in sorted(glob.glob(f"{SRC}/**/*.stl", recursive=True)):
    rel = os.path.relpath(f, SRC); conj = os.path.dirname(rel)
    nome, q = re.match(r"(.*) \[(\d+)x\]\.stl", os.path.basename(f)).groups()
    if SO and nome not in SO: continue
    m = trimesh.load(f, process=False)
    orig = os.path.exists(f"{REPO}/{nome}.stl") and nome not in FORCA
    if orig: modo = "repo Mulbot"
    else: m, modo = orienta(m, nome)
    if nome in CUNHAS:                           # remendo sem suporte em peca da Mulbot (quadro: girada e encostada em 0,0,0)
        m = trimesh.Trimesh(m.vertices, m.faces, process=True); m.apply_translation(-m.bounds[0])
        for x0, x1, yw, yt, zb in CUNHAS[nome]:
            h = yt - yw + 0.5
            c = trimesh.convex.convex_hull(np.array([[x0, yw - 0.5, zb - h], [x0, yw - 0.5, zb + 0.01], [x0, yt, zb + 0.01],
                                                     [x1, yw - 0.5, zb - h], [x1, yw - 0.5, zb + 0.01], [x1, yt, zb + 0.01]]))
            c.fix_normals(); m = trimesh.boolean.union([m, c], engine="manifold")
        modo += " +cunhas"
    if nome in DEPOIS and modo != "fixa (impressao_rot)":
        m.apply_transform(trimesh.transformations.euler_matrix(*np.radians(DEPOIS[nome]), "sxyz")); modo += " +giro"
    m = assenta(m)
    if not cabe(m): print("NAO CABE:", rel, m.extents)
    os.makedirs(f"{DST}/{conj}", exist_ok=True); m.export(f"{DST}/{conj}/{nome}.stl")
    cont, bal, alt = avalia(m)
    info[f"{conj}/{nome}"] = dict(conj=conj, nome=nome, qtd=int(q), ext=[round(v, 1) for v in m.extents], modo=modo,
                                  contato=round(cont), balanco=round(bal))
    print(f"{m.extents[0]:6.1f}{m.extents[1]:6.1f}{m.extents[2]:6.1f}  cont={cont:6.0f} bal={bal:6.0f}  {modo:22.22s} {rel}")
json.dump(info, open(f"{DST}/orienta.json", "w"), indent=1, ensure_ascii=False)
