# Conferencia "sem suporte" de uma peca JA na posicao de impressao (z = 0 na mesa): fatia em camadas, rasteriza e acha
# o que fica no ar. Regra FDM: cada camada pode passar 45 graus da de baixo; regiao no ar so vale se for PONTE
# (largura <= PONTE mm e presa em >= 2 lados). O resto vira "ilha sem apoio" (componente 3D) e e reportado.
# python3 semsup_check.py arquivo.stl [...]   (env: PASSO=0.3 PONTE=20 JSON=saida.json)
import sys, os, json, numpy as np, trimesh
from PIL import Image, ImageDraw
from scipy import ndimage as nd

PASSO = float(os.environ.get("PASSO", 0.3))     # altura da camada (mm)
PX = float(os.environ.get("PX", PASSO / 2))      # pixel (mm): mais fino que a camada -> parede alinhada na borda do pixel nao "pisca"
K45 = PASSO / PX                                 # 45 graus = K45 pixels por camada
PONTE = float(os.environ.get("PONTE", 20.0))     # vao maximo de ponte aceito (mm)
MIN_MM3 = float(os.environ.get("MIN_MM3", 2.0))
TOL = float(os.environ.get("TOL", 0.6))         # degrau aceito (mm) alem dos 45 graus, sem acumular  # ignora ilha menor que isso (ruido de rasterizacao)

def _raster(secs, zs, m, lo, nx, ny, dz):
    """regra par-impar: cada contorno fechado inverte o que esta dentro dele (nao depende de montar poligonos com furos,
    que falha quando 2 contornos se tocam e faz a camada sumir)"""
    L = np.zeros((len(zs), ny, nx), bool)
    for i, s in enumerate(secs):
        if s is None: continue
        acc = np.zeros((ny, nx), bool)
        for e in s.discrete:
            if len(e) < 3: continue
            img = Image.new("1", (nx, ny), 0)
            ImageDraw.Draw(img).polygon([((x - lo[0]) / PX + 2, (y - lo[1]) / PX + 2) for x, y in e], fill=1)
            acc ^= np.array(img, bool)
        L[i] = acc
    return L

def camadas(m):
    """camadas pelo corte do manifold3d (contornos sempre validos; o corte do trimesh perde contorno em malha com lasca de area 0)"""
    import manifold3d as mf
    lo, hi = m.bounds; nx = int(np.ceil((hi[0] - lo[0]) / PX)) + 4; ny = int(np.ceil((hi[1] - lo[1]) / PX)) + 4
    zs = np.arange(PASSO / 2, hi[2], PASSO)
    M = mf.Manifold(mf.Mesh(vert_properties=np.asarray(m.vertices, np.float32), tri_verts=np.asarray(m.faces, np.uint32)))
    if M.status() != mf.Error.NoError or M.is_empty(): raise RuntimeError(f"malha invalida p/ o manifold: {M.status()}")
    L = np.zeros((len(zs), ny, nx), bool)
    for i, z in enumerate(zs):
        acc = np.zeros((ny, nx), bool)
        for e in M.slice(float(z)).to_polygons():
            e = np.asarray(e)
            if len(e) < 3: continue
            img = Image.new("1", (nx, ny), 0)
            ImageDraw.Draw(img).polygon([((x - lo[0]) / PX + 2, (y - lo[1]) / PX + 2) for x, y in e], fill=1)
            acc ^= np.array(img, bool)                              # par-impar: contorno de furo inverte
        L[i] = acc
    return L, lo

def checa(L):
    S = np.zeros_like(L); U = np.zeros_like(L); est = nd.generate_binary_structure(2, 1)
    est8 = np.ones((3, 3), bool)
    S[0] = L[0]
    for i in range(1, len(L)):
        ap = L[i] & (nd.distance_transform_edt(~S[i - 1]) <= K45 + 0.5)   # 45 graus + meio pixel de folga de rasterizacao
        livre = L[i] & ~ap
        ok = ap.copy()

        if livre.any():
            lab, n = nd.label(livre, est8)
            dt = nd.distance_transform_edt(livre)
            larg = nd.maximum(dt, lab, np.arange(1, n + 1)) * 2 * PX
            borda = nd.binary_dilation(livre, est8) & ap        # contato com o que esta apoiado
            for k in range(1, n + 1):
                c = lab == k
                if larg[k - 1] <= PONTE:
                    per = nd.binary_dilation(c, est8) & ~c                # contorno da regiao no ar
                    cont = per & nd.binary_dilation(ap, est8, iterations=int(round(2 * K45)))
                    _, nseg = nd.label(cont, est8)
                    if nseg >= 2 or cont.sum() >= 0.55 * per.sum(): ok |= c; continue   # ponte: presa em 2 lados (ou em volta)
                U[i] |= c
            # degrau de ate TOL mm alem dos 45 graus: aceito UMA vez (topo de furo pequeno), mas nao apoia a camada de cima
            if U[i].any(): U[i] &= nd.distance_transform_edt(~ap) > TOL / PX
        S[i] = ok
    return U

def relata(f):
    m = trimesh.load(f, process=True); m.merge_vertices()       # STL e sopa de triangulos: solda antes de cortar
    L, lo = camadas(m); U = checa(L)
    lab, n = nd.label(U, np.ones((3, 3, 3), bool)); out = []
    for k, sl in enumerate(nd.find_objects(lab), 1):
        v = (lab[sl] == k).sum() * PX * PX * PASSO
        if v < MIN_MM3: continue
        z0, z1 = sl[0].start * PASSO, sl[0].stop * PASSO
        y0, y1 = sl[1].start * PX - 2 * PX + lo[1], sl[1].stop * PX - 2 * PX + lo[1]
        x0, x1 = sl[2].start * PX - 2 * PX + lo[0], sl[2].stop * PX - 2 * PX + lo[0]
        out.append(dict(mm3=round(v, 1), x=(round(x0, 1), round(x1, 1)), y=(round(y0, 1), round(y1, 1)), z=(round(z0, 1), round(z1, 1))))
    out.sort(key=lambda o: -o["mm3"])
    return out

if __name__ == "__main__":
    tudo = {}
    for f in sys.argv[1:]:
        r = relata(f); tudo[f] = r
        tot = sum(o["mm3"] for o in r)
        print(f"{os.path.basename(f)}: {len(r)} ilha(s) sem apoio, {tot:.0f} mm3")
        for o in r[:8]: print("   ", o)
    if os.environ.get("JSON"): json.dump(tudo, open(os.environ["JSON"], "w"), indent=1)
