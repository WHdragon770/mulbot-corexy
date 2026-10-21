# Placas de impressao da CoreXY: 3MF da Anycubic Kobra X (formato Anycubic Slicer Next / Bambu) por conjunto, cada placa ja
# com as pecas na quantidade certa e na orientacao do orienta.py; pecas de resina saem a parte (STL solto + placa da Photon).
# python3 placas.py <pasta_orient> <pasta_saida>
import sys, os, json, uuid, zipfile, struct, numpy as np, trimesh

SRC, DST = (sys.argv[1], sys.argv[2]) if len(sys.argv) > 2 else (os.environ["SRC"], os.environ.get("DST", "."))
REF = "/mnt/c/Users/lucas/Downloads/ACE+GEN2+KobraX+Printhead+Jig+v1.03+KIT+Standing+Dock-new.3mf"   # projeto Kobra X 0.4 (Slicer Next 2.0)
W = H = 260.0                                   # mesa Kobra X
BORDA, ESP = 4.0, 10.0                          # margem da mesa e espaco entre pecas: brim de 4 mm de cada lado + 2 (brim encostado = conflito no fatiador)
ESP_PARAF = 5.0                                 # parafusos/porcas: sem brim (deitados na face chata)
PASSO_X = PASSO_Y = 260.0 * 1.2                 # distancia entre placas no projeto (Orca/Bambu: mesa + 1/5)
INFO = json.load(open(f"{SRC}/orienta.json"))

RESINA = ("07 Roldanas", "Resina (alternativa)")
TPU = ("DL1-01-08",)                            # pes da Mulbot
PETG = ("DL1-04-08", "elo_esteira")                         # polia motriz: o autor da Mulbot amoleceu em PLA com o calor do motor
PARAF = "08 Parafusos"
# perfil por objeto (cascas e preenchimento como o autor da Mulbot: 2 cascas/15 %, parafusos 4 cascas/25 %);
# o quadro aqui e oco (canal de cabos) -> 3 cascas
def perfil(chave):
    if chave.startswith(PARAF): return {"wall_loops": "4", "sparse_infill_density": "25%", "brim_type": "no_brim"}
    b = {"brim_type": "outer_only", "brim_width": "10" if "/fusoZ" in chave else "4"}   # fuso de 250 mm em pe: brim largo
    if chave.startswith("01 Quadro") or chave.startswith("02 Eixo Y") or chave.startswith("04 Eixo Z"): return {"wall_loops": "3", "sparse_infill_density": "20%", **b}
    return {"wall_loops": "3", "sparse_infill_density": "15%", **b}

# ---------------- empacotamento: MaxRects (melhor encaixe pelo lado curto), gira 90 graus se precisar
class Placa:
    def __init__(self, livres=None, nome=""):
        self.livres = [(BORDA, BORDA, W - 2 * BORDA, H - 2 * BORDA)] if livres is None else livres
        self.itens, self.nome = [], nome
    def coloca(self, w, h):
        melhor = None
        for (x, y, lw, lh) in self.livres:
            for (a, b, rot) in ((w, h, False), (h, w, True)):
                if a + ESP <= lw + ESP + 1e-6 and b + ESP <= lh + ESP + 1e-6 and a <= lw and b <= lh:
                    s = min(lw - a, lh - b)
                    if melhor is None or s < melhor[0]: melhor = (s, x, y, a, b, rot)
        if melhor is None: return None
        _, x, y, a, b, rot = melhor
        self._corta((x, y, a + ESP, b + ESP))
        return x, y, rot
    def _corta(self, r):
        rx, ry, rw, rh = r; nl = []
        for (x, y, w, h) in self.livres:
            if rx >= x + w or rx + rw <= x or ry >= y + h or ry + rh <= y: nl.append((x, y, w, h)); continue
            if rx > x: nl.append((x, y, rx - x, h))
            if rx + rw < x + w: nl.append((rx + rw, y, x + w - rx - rw, h))
            if ry > y: nl.append((x, y, w, ry - y))
            if ry + rh < y + h: nl.append((x, ry + rh, w, y + h - ry - rh))
        nl = [r for r in nl if r[2] > 1 and r[3] > 1]
        self.livres = [a for i, a in enumerate(nl) if not any(j != i and b[0] <= a[0] and b[1] <= a[1] and b[0] + b[2] >= a[0] + a[2]
                                                                and b[1] + b[3] >= a[1] + a[3] and (b != a or j < i) for j, b in enumerate(nl))]

def maxrects(curtas, nome, placas):
    for k, d in curtas:
        for pl in placas:
            r = pl.coloca(d[0], d[1])
            if r: break
        else:
            pl = Placa(nome=nome); placas.append(pl); r = pl.coloca(d[0], d[1])
            assert r, f"{k} nao cabe na mesa: {d}"
        x, y, rot = r
        a, b = (d[1], d[0]) if rot else (d[0], d[1])
        pl.itens.append((k, x + a / 2, y + b / 2, 90.0 if rot else 0.0))
    return placas

def prateleiras(curtas, nome):
    """fileiras: peca de pe no sentido Y (lado maior em Y fica mais compacto p/ parafuso), ordenadas por nome p/ achar facil"""
    ps = sorted(curtas, key=lambda p: (-max(p[1][:2]), p[0]))
    placas, pl, x, y, hlin = [], None, BORDA, BORDA, 0.0
    for k, d in ps:
        a, b, r = (d[1], d[0], 90.0) if d[0] > d[1] else (d[0], d[1], 0.0)
        if pl is None or x + a > W - BORDA:
            x, y, hlin = BORDA, y + hlin + (ESP if pl and hlin else 0), 0.0
        if pl is None or y + b > H - BORDA:
            pl = Placa(nome=nome); placas.append(pl); x, y, hlin = BORDA, BORDA, 0.0
        pl.itens.append((k, x + a / 2, y + b / 2, r)); x += a + ESP; hlin = max(hlin, b)
    return placas

ALTA = 150.0                                    # peca mais alta que isso (fuso) vai sozinha na placa: se soltar nao leva as outras
def empacota(pecas, nome):
    """pecas: [(chave, ext)] uma por copia. Compridas (> mesa) vao na diagonal, 2 por placa, cantos livres p/ pecas pequenas."""
    altas = [p for p in pecas if p[1][2] > ALTA]
    pecas = [p for p in pecas if p[1][2] <= ALTA]
    placas = []
    if altas:
        pl = Placa([], nome); placas.append(pl)
        for i, (k, d) in enumerate(altas):         # em linha no meio da mesa, 40 mm entre eixos
            pl.itens.append((k, W / 2 + (i - (len(altas) - 1) / 2) * max(40.0, d[0] + 15), H / 2, 0.0))
    longas = [p for p in pecas if max(p[1][:2]) > W - 2 * BORDA]
    curtas = sorted([p for p in pecas if max(p[1][:2]) <= W - 2 * BORDA], key=lambda p: -p[1][0] * p[1][1])
    while longas:
        grupo = longas[:2]; longas = longas[2:]
        larg = sum(p[1][1] for p in grupo) + ESP * (len(grupo) - 1)
        # cantos livres (quadrados) fora da faixa diagonal de meia largura larg/2 + folga
        s = (W - 2 * BORDA - (larg / 2 + ESP) * np.sqrt(2)) / 2
        pl = Placa([(BORDA, H - BORDA - s, s, s), (W - BORDA - s, BORDA, s, s)] if s > 20 else [], nome)
        off = -larg / 2
        for k, d in grupo:
            off += d[1] / 2
            c = np.array([W / 2, H / 2]) + off * np.array([-1, 1]) / np.sqrt(2)
            pl.itens.append((k, c[0], c[1], 45.0)); off += d[1] / 2 + ESP
        placas.append(pl)
    if curtas and not placas:                      # so pecas pequenas: fileiras (prateleiras) ficam mais arrumadas que o MaxRects
        pf = prateleiras(curtas, nome)
        if len(pf) <= len(maxrects(curtas, nome, [])): curtas, placas = [], pf
    placas = maxrects(curtas, nome, placas)
    for pl in placas:                               # centra o conjunto na mesa (o MaxRects enche a partir do canto)
        if any(it[3] == 45.0 for it in pl.itens): continue
        bx = [(x - (INFO[k]["ext"][1] if r == 90 else INFO[k]["ext"][0]) / 2, x + (INFO[k]["ext"][1] if r == 90 else INFO[k]["ext"][0]) / 2,
               y - (INFO[k]["ext"][0] if r == 90 else INFO[k]["ext"][1]) / 2, y + (INFO[k]["ext"][0] if r == 90 else INFO[k]["ext"][1]) / 2)
              for k, x, y, r in pl.itens]
        dx = W / 2 - (min(b[0] for b in bx) + max(b[1] for b in bx)) / 2; dy = H / 2 - (min(b[2] for b in bx) + max(b[3] for b in bx)) / 2
        pl.itens = [(k, x + dx, y + dy, r) for k, x, y, r in pl.itens]
    return placas

# ---------------- 3MF (formato Anycubic Slicer Next / Bambu: objetos com componente, instancias = varios itens no build)
def malha(chave):
    m = trimesh.load(f"{SRC}/{chave}.stl", process=False); m.merge_vertices(digits_vertex=4)
    return m

def projeto(n_placas):
    d = json.loads(zipfile.ZipFile(REF).read("Metadata/project_settings.config"))
    # o projeto de referencia vinha com suporte em arvore ligado: desligado (README da Mulbot: nenhuma peca precisa; com suporte
    # o fatiador poe arvore embaixo da rosca dos parafusos deitados e as arvores de pecas vizinhas se cruzam = "conflito")
    d.update(enable_support="0", support_type="tree(auto)", support_on_build_plate_only="1",
             wall_loops="3", sparse_infill_density="15%", sparse_infill_pattern="gyroid", brim_type="outer_only", brim_width="4")
    d["different_settings_to_system"][0] = "brim_type;brim_width;sparse_infill_pattern;support_on_build_plate_only;wall_generator;wall_loops"
    return d

def escreve_3mf(path, placas, titulo, filamento=None):
    unicas = sorted({k for pl in placas for (k, *_r) in pl.itens})
    oid = {k: 2 * i + 2 for i, k in enumerate(unicas)}      # objeto de topo = 2i+2, malha = 2i+1 (no arquivo da malha)
    mods, rels, comps, nfaces = {}, [], [], {}
    for i, k in enumerate(unicas):
        m = malha(k); nfaces[k] = len(m.faces)
        arq = f"3D/Objects/obj_{i + 1}.model"
        v = "\n".join(f'     <vertex x="{x:.4f}" y="{y:.4f}" z="{z:.4f}"/>' for x, y, z in m.vertices)
        t = "\n".join(f'     <triangle v1="{a}" v2="{b}" v3="{c}"/>' for a, b, c in m.faces)
        mods[arq] = (f'<?xml version="1.0" encoding="UTF-8"?>\n<model unit="millimeter" xml:lang="en-US" '
                     f'xmlns="http://schemas.microsoft.com/3dmanufacturing/core/2015/02" xmlns:BambuStudio="http://schemas.bambulab.com/package/2021" '
                     f'xmlns:p="http://schemas.microsoft.com/3dmanufacturing/production/2015/06" requiredextensions="p">\n'
                     f' <metadata name="BambuStudio:3mfVersion">1</metadata>\n <resources>\n  <object id="{oid[k] - 1}" p:UUID="{uuid.uuid4()}" type="model">\n'
                     f'   <mesh>\n    <vertices>\n{v}\n    </vertices>\n    <triangles>\n{t}\n    </triangles>\n   </mesh>\n  </object>\n </resources>\n <build/>\n</model>\n')
        rels.append(f' <Relationship Target="/{arq}" Id="rel-{i + 1}" Type="http://schemas.microsoft.com/3dmanufacturing/2013/01/3dmodel"/>')
        comps.append(f'  <object id="{oid[k]}" p:UUID="{uuid.uuid4()}" type="model">\n   <components>\n'
                     f'    <component p:path="/{arq}" objectid="{oid[k] - 1}" p:UUID="{uuid.uuid4()}" transform="1 0 0 0 1 0 0 0 1 0 0 0"/>\n'
                     f'   </components>\n  </object>')
    itens, inst, ident = [], {k: 0 for k in unicas}, 1000
    cols = int(np.ceil(np.sqrt(len(placas))))
    plates_xml = []
    for p, pl in enumerate(placas):
        ox, oy = (p % cols) * PASSO_X, -(p // cols) * PASSO_Y
        mi = []
        for (k, x, y, ang) in pl.itens:
            a = np.radians(ang); c, s = np.cos(a), np.sin(a)
            itens.append(f'  <item objectid="{oid[k]}" p:UUID="{uuid.uuid4()}" transform="{c:.9f} {s:.9f} 0 {-s:.9f} {c:.9f} 0 0 0 1 '
                         f'{ox + x:.4f} {oy + y:.4f} 0" printable="1"/>')
            mi.append(f'    <model_instance>\n      <metadata key="object_id" value="{oid[k]}"/>\n'
                      f'      <metadata key="instance_id" value="{inst[k]}"/>\n      <metadata key="identify_id" value="{ident}"/>\n    </model_instance>')
            inst[k] += 1; ident += 1
        plates_xml.append(f'  <plate>\n    <metadata key="plater_id" value="{p + 1}"/>\n    <metadata key="plater_name" value="{pl.nome}"/>\n'
                          f'    <metadata key="locked" value="false"/>\n' + "\n".join(mi) + '\n  </plate>')
    modelo = (f'<?xml version="1.0" encoding="UTF-8"?>\n<model unit="millimeter" xml:lang="en-US" xmlns="http://schemas.microsoft.com/3dmanufacturing/core/2015/02" '
              f'xmlns:BambuStudio="http://schemas.bambulab.com/package/2021" xmlns:p="http://schemas.microsoft.com/3dmanufacturing/production/2015/06" requiredextensions="p">\n'
              f' <metadata name="Application">BambuStudio-2.0.0.3</metadata>\n <metadata name="BambuStudio:3mfVersion">1</metadata>\n'
              f' <metadata name="Title">{titulo}</metadata>\n <resources>\n' + "\n".join(comps) + f'\n </resources>\n <build p:UUID="{uuid.uuid4()}">\n'
              + "\n".join(itens) + '\n </build>\n</model>\n')
    objs = []
    for k in unicas:
        nome = INFO[k]["nome"]
        extra = "\n".join(f'    <metadata key="{a}" value="{b}"/>' for a, b in perfil(k).items())
        objs.append(f'  <object id="{oid[k]}">\n    <metadata key="name" value="{nome}"/>\n    <metadata key="extruder" value="1"/>\n{extra}\n'
                    f'    <part id="{oid[k] - 1}" subtype="normal_part">\n      <metadata key="name" value="{nome}"/>\n'
                    f'      <metadata key="matrix" value="1 0 0 0 0 1 0 0 0 0 1 0 0 0 0 1"/>\n      <metadata key="source_object_id" value="0"/>\n'
                    f'      <metadata key="source_volume_id" value="0"/>\n'
                    f'      <mesh_stat face_count="{nfaces[k]}" edges_fixed="0" degenerate_facets="0" facets_removed="0" facets_reversed="0" backwards_edges="0"/>\n'
                    f'    </part>\n  </object>')
    settings = '<?xml version="1.0" encoding="UTF-8"?>\n<config>\n' + "\n".join(objs) + "\n" + "\n".join(plates_xml) + '\n</config>\n'
    ct = ('<?xml version="1.0" encoding="UTF-8"?>\n<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">\n'
          ' <Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>\n'
          ' <Default Extension="model" ContentType="application/vnd.ms-package.3dmanufacturing-3dmodel+xml"/>\n'
          ' <Default Extension="png" ContentType="image/png"/>\n <Default Extension="gcode" ContentType="text/x.gcode"/>\n</Types>\n')
    rel0 = ('<?xml version="1.0" encoding="UTF-8"?>\n<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">\n'
            ' <Relationship Target="/3D/3dmodel.model" Id="rel-1" Type="http://schemas.microsoft.com/3dmanufacturing/2013/01/3dmodel"/>\n</Relationships>\n')
    rel1 = ('<?xml version="1.0" encoding="UTF-8"?>\n<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">\n'
            + "\n".join(rels) + '\n</Relationships>\n')
    proj = projeto(len(placas))
    with zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED) as z:
        z.writestr("[Content_Types].xml", ct); z.writestr("_rels/.rels", rel0)
        z.writestr("3D/3dmodel.model", modelo); z.writestr("3D/_rels/3dmodel.model.rels", rel1)
        for arq, txt in mods.items(): z.writestr(arq, txt)
        z.writestr("Metadata/model_settings.config", settings)
        z.writestr("Metadata/project_settings.config", json.dumps(proj, indent=4, ensure_ascii=False))

# ---------------- monta os arquivos
def main():
    os.makedirs(f"{DST}/Kobra X (3MF)", exist_ok=True)
    conjs = sorted({v["conj"].split("/")[0] for v in INFO.values()})
    resumo = []
    def copias(chaves): return [(k, INFO[k]["ext"]) for k in chaves for _ in range(INFO[k]["qtd"])]
    lotes = []                                     # (arquivo, titulo, [chaves])
    for c in conjs:
        ks = [k for k, v in INFO.items() if v["conj"].split("/")[0] == c and not any(r in v["conj"] for r in RESINA)]
        if not ks: continue
        esp = [k for k in ks if INFO[k]["nome"] in TPU + PETG]
        ks = [k for k in ks if k not in esp]
        if ks: lotes.append((f"{c} - PLA.3mf", c, ks))
        for k in esp:
            mat = "TPU" if INFO[k]["nome"] in TPU else "PETG"
            lotes.append((f"{c} - {INFO[k]['nome']} - {mat}.3mf", f"{c} {mat}", [k]))
    global ESP
    for arq, tit, ks in lotes:
        ESP = ESP_PARAF if tit.startswith(PARAF) else 10.0
        pl = empacota(copias(ks), tit)
        for i, p in enumerate(pl): p.nome = f"{tit.split(' ', 1)[1] if tit[:2].isdigit() else tit} {i + 1}/{len(pl)}"
        escreve_3mf(f"{DST}/Kobra X (3MF)/{arq}", pl, tit)
        n = sum(len(p.itens) for p in pl)
        resumo.append((arq, len(pl), n))
        print(f"{arq}: {len(pl)} placa(s), {n} pecas", flush=True)
    json.dump(resumo, open(f"{DST}/resumo_kobra.json", "w"), ensure_ascii=False, indent=1)

if __name__ == "__main__": main()
