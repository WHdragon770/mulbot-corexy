# Manual completo da CoreXY 100, num PDF so: capa com indice e quantidades, paginas explicativas
# (antes de comecar, compras, como imprimir, roteiro de montagem, detalhes, ligacao e primeira ligada)
# + lista de impressao (02) + folhas de montagem (03). So junta o que ja foi gerado.
# Uso: python3 completo.py <raiz CoreXY 100 no Windows> <saida.pdf>
import sys, os, glob, csv, re, io, datetime, pypdf
from PIL import Image, ImageDraw, ImageFont
RAIZ, OUT = sys.argv[1:3]
STL, DES, DET = (f"{RAIZ}/{p}" for p in ("02 STL para imprimir", "03 Desenhos de montagem", "04 Detalhes (imagens)"))
F = "/usr/share/fonts/truetype/dejavu/DejaVuSans"
def fonte(t, b=False): return ImageFont.truetype(F + ("-Bold" if b else "") + ".ttf", t)
SW, SH, M0, CAR = 3508, 2480, 70, 150
X1 = SW - CAR - M0 / 2                                 # comeco da faixa do carimbo
VERM, AZUL, CINZA = "#b8282b", "#1a5f8a", "#e8eef2"

def carimbo(img, dr, fid, titulo):
    dr.rectangle((M0 / 2, M0 / 2, SW - M0 / 2, SH - M0 / 2), outline="black", width=3)
    dr.line((X1, M0 / 2, X1, SH - M0 / 2), fill="black", width=3)
    blocos = [("MULBOT COREXY 100³", 46, True, 760), ("mesa 120 aquecida 12 V", 26, False, 640),
              (f"{datetime.date.today():%d/%m/%Y}", 26, False, 240), (f"FOLHA: {fid}", 34, True, 300), (f"TÍTULO: {titulo}", 30, True, 0)]
    y = M0 / 2
    for t, s, b, h in blocos:
        if h == 0: h = SH - M0 / 2 - y
        txt = Image.new("RGBA", (int(h), CAR - 10), (255, 255, 255, 0)); d2 = ImageDraw.Draw(txt)
        f = fonte(s, b); tw = d2.textlength(t, font=f)
        while tw > h - 30: s -= 2; f = fonte(s, b); tw = d2.textlength(t, font=f)
        d2.text(((h - tw) / 2, (CAR - 10 - s) / 2 - 4), t, font=f, fill="black")
        txt = txt.rotate(90, expand=True); img.paste(txt, (int(X1 + 5), int(y)), txt); y += h
        if y < SH - M0: dr.line((X1, y, SW - M0 / 2, y), fill="black", width=3)

def quebra(dr, t, f, w):
    ls, l = [], ""
    for p in t.split():
        if l and dr.textlength(l + " " + p, font=f) > w: ls.append(l); l = p
        else: l = (l + " " + p).strip()
    return ls + [l]

def linha(dr, x, y, cols, vals, f, h, fundo=None):
    for (_, w), v in zip(cols, vals):
        dr.rectangle((x, y, x + w, y + h), outline="black", width=2, fill=fundo)
        dr.text((x + 8, y + (h - f.size) / 2 - 2), str(v), font=f, fill="black"); x += w

def tabela(dr, x, y, titulo, cols, rows, fs=26, h=46):
    W = sum(c[1] for c in cols); fb, f = fonte(fs, True), fonte(fs)
    if titulo:
        dr.rectangle((x, y, x + W, y + h), outline="black", width=2)
        dr.text((x + W / 2 - dr.textlength(titulo, font=fb) / 2, y + (h - fs) / 2 - 2), titulo, font=fb, fill="black"); y += h
    linha(dr, x, y, cols, [c[0] for c in cols], fb, h, CINZA); y += h
    for r in rows: linha(dr, x, y, cols, r, f, h); y += h
    return y

def notas(dr, x, y, w, titulo, nts, fs=27):
    dr.text((x, y), titulo, font=fonte(fs + 2, True), fill="black"); y += fs + 16; f = fonte(fs)
    for i, n in enumerate(nts, 1):
        dr.text((x, y), f"{i}.", font=f, fill="black")
        for l in quebra(dr, n, f, w - 46): dr.text((x + 40, y), l, font=f, fill="black"); y += fs + 9
    return y

# ---------- pagina de texto: blocos correm em 2 colunas
CW, GAP, YT = 1540, 90, M0 + 170
XC = (M0 + 30, M0 + 30 + CW + GAP)
FS = 30
def pagina(fid, titulo, sub, blocos, rodape_titulo=None):
    img = Image.new("RGB", (SW, SH), "white"); dr = ImageDraw.Draw(img)
    dr.text((M0 + 30, M0 + 30), titulo, font=fonte(64, True), fill=VERM)
    if sub: dr.text((M0 + 34, M0 + 112), sub, font=fonte(32), fill="#444")
    c, y, ymax = 0, YT, SH - M0 - 40
    f, fb, fh = fonte(FS), fonte(FS, True), fonte(38, True)
    def altura(b):
        k = b[0]
        if k == "h": return 38 + 34
        if k == "p": return len(quebra(dr, b[1], f, CW)) * (FS + 10) + 18
        if k in ("b", "n"): return sum(len(quebra(dr, t, f, CW - 50)) * (FS + 10) + 6 for t in b[1]) + 18
        if k == "t": return (len(b[2]) + 1) * 46 + 24
        if k == "img": return b[2] + 70
    meio = sum(altura(b) for b in blocos) / 2         # equilibra as 2 colunas: quebra num titulo depois da metade
    for b in blocos:
        h = altura(b)
        if c == 0 and (b[0] == "h" and y - YT + h / 2 > meio or b[0] == "h" and y + h + 120 > ymax or y + h > ymax):
            c += 1; y = YT
        if y + h > ymax: sys.exit(f"{fid}: texto nao coube")
        x = XC[c]
        if b[0] == "h":
            dr.text((x, y), b[1], font=fh, fill=AZUL); dr.line((x, y + 50, x + CW, y + 50), fill=AZUL, width=3)
        elif b[0] == "p":
            for k, l in enumerate(quebra(dr, b[1], f, CW)): dr.text((x, y + k * (FS + 10)), l, font=f, fill="black")
        elif b[0] in ("b", "n"):
            yy = y
            for i, t in enumerate(b[1], 1):
                dr.text((x + 6, yy), "•" if b[0] == "b" else f"{i}.", font=fb, fill=AZUL)
                for l in quebra(dr, t, f, CW - 50): dr.text((x + 50, yy), l, font=f, fill="black"); yy += FS + 10
                yy += 6
        elif b[0] == "t":
            tabela(dr, x, y, None, b[1], b[2], fs=25)
        elif b[0] == "img":
            im = b[1]() if callable(b[1]) else Image.open(b[1]).convert("RGB")
            im.thumbnail((CW, b[2])); img.paste(im, (int(x + (CW - im.width) / 2), int(y)))
            dr.rectangle((x + (CW - im.width) / 2, y, x + (CW + im.width) / 2, y + im.height), outline="#999", width=2)
            dr.text((x, y + im.height + 14), b[3], font=fonte(26), fill="#444")
        y += h
    carimbo(img, dr, fid, rodape_titulo or titulo.upper())
    return img

def pagina_fotos(fid, titulo, texto, fotos):
    img = Image.new("RGB", (SW, SH), "white"); dr = ImageDraw.Draw(img)
    dr.text((M0 + 30, M0 + 30), titulo, font=fonte(64, True), fill=VERM); y = M0 + 130; f = fonte(FS)
    for l in quebra(dr, texto, f, X1 - M0 - 120): dr.text((M0 + 34, y), l, font=f, fill="black"); y += FS + 10
    y += 30; n = len(fotos); cols = 2 if n <= 4 else 3; rows = (n + cols - 1) // cols
    W = (X1 - M0 - 90 - (cols - 1) * 40) / cols; H = (SH - M0 - 60 - y - rows * 60) / rows
    for i, (p, leg) in enumerate(fotos):
        x0 = M0 + 30 + (i % cols) * (W + 40); y0 = y + (i // cols) * (H + 60)
        im = Image.open(p).convert("RGB"); im.thumbnail((int(W), int(H)))
        px, py = int(x0 + (W - im.width) / 2), int(y0 + (H - im.height) / 2); img.paste(im, (px, py))
        dr.rectangle((px, py, px + im.width, py + im.height), outline="#999", width=2)
        dr.text((x0 + W / 2 - dr.textlength(leg, font=fonte(26)) / 2, y0 + H + 10), leg, font=fonte(26), fill="#444")
    carimbo(img, dr, fid, "DETALHES: " + titulo.upper())
    return img

# ---------- dados
import trimesh
lista = list(csv.DictReader(open(f"{STL}/lista_de_impressao.csv", encoding="utf-8-sig"), delimiter=";"))
mont = sorted(p for p in glob.glob(f"{DES}/CXY-*.png") if not os.path.basename(p).startswith("CXY-00"))
resina = [r for r in lista if r["material"] == "Resina"]
fdm = [r for r in lista if r["material"] != "Resina"]
qt = lambda rs: sum(int(r["qtd"]) for r in rs)
def arq(r): return glob.glob(f"{STL}/{r['pasta']}/{glob.escape(r['peca'])} [[]*.stl")[0]
for r in lista:
    b = trimesh.load(arq(r)).bounds; r["medida"] = " x ".join(f"{v:.0f}" for v in b[1] - b[0])
vol = sum(abs(trimesh.load(arq(r)).volume) * int(r["qtd"]) for r in fdm)
fil = f"{vol * 0.45 * 1.24 / 1e6:.1f}".replace(".", ",")   # 3 paredes + 10% gyroid ~ 45% do volume solido, PLA 1,24 g/cm3
def compradas():                                       # itens "Comprada" das folhas de montagem (mesma regra do folhas.py)
    import collections
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__))); argv = sys.argv; sys.argv = ["x", "/tmp/_folhas_nada"]
    import folhas as FO
    sys.argv = argv; tot, onde = collections.Counter(), collections.defaultdict(set)
    for fd in FO.FOLHAS:
        if "pref" not in fd and "objetos" not in fd: continue
        obj = fd["objetos"]() if "objetos" in fd else [j for j in FO.J if FO.pref_de(j["nome"]) in fd["pref"] and not j["nome"].startswith("esfera")]
        for j in obj:
            if j.get("item") == 0 or isinstance(j.get("item"), int): continue
            k = FO.chave(j["stl"])
            if FO.origem(k, j["stl"]) == "Comprada" and FO.principal(j["stl"]): tot[FO.descricao(k)] += 1; onde[FO.descricao(k)].add(fd["id"])
        for d, o, q, p in fd.get("extra", []):
            if o == "Comprada": tot[d] += q; onde[d].add(fd["id"])
    return [(d, q, ", ".join(sorted(onde[d]))) for d, q in sorted(tot.items())]
COMPRA = compradas()

# ---------- lista de impressao: 2 colunas por folha, cabecalho por pasta
COLS = [("ITEM", 100), ("QTD", 100), ("PEÇA (pasta 02)", 640), ("MAT.", 160), ("MEDIDA (mm)", 300), ("OK", 180)]
TW, HL, FL = sum(c[1] for c in COLS), 44, 24
Y0, YMAX = M0 + 150, SH - M0 - 30
grupos = {}
for r in lista: grupos.setdefault(r["pasta"], []).append(r)
celulas, it = [], 0                                    # ("g", pasta) ou ("r", item, linha)
for p, rs in grupos.items():
    celulas.append(("g", f"{p}  ({len(rs)} arquivos, {qt(rs)} peças)"))
    for r in rs: it += 1; celulas.append(("r", it, r))
pags_li, k = [], 0
while k < len(celulas):
    pags_li.append([])
    for c in range(2):
        col, y = [], Y0 + 2 * HL
        while k < len(celulas) and y + HL <= YMAX:
            if celulas[k][0] == "g" and y + 3 * HL > YMAX: break      # nao deixa cabecalho de pasta sozinho no pe
            col.append(celulas[k]); k += 1; y += HL
        pags_li[-1].append(col)
NLI = len(pags_li)

def folha_lista(i, cols):
    img = Image.new("RGB", (SW, SH), "white"); dr = ImageDraw.Draw(img); fid = f"LI-{i + 1:02d}"
    dr.text((M0 + 20, M0 + 30), f"LISTA DE IMPRESSÃO  ·  folha {i + 1} de {NLI}", font=fonte(56, True), fill="black")
    fb, f = fonte(FL, True), fonte(FL)
    for c, col in enumerate(cols):
        x = M0 + 20 + c * (TW + 80); y = Y0
        dr.rectangle((x, y, x + TW, y + HL), outline="black", width=2)
        t = "PEÇAS PARA IMPRIMIR NA COREXY 100" + ("" if c == 0 else " (cont.)")
        dr.text((x + TW / 2 - dr.textlength(t, font=fb) / 2, y + (HL - FL) / 2 - 2), t, font=fb, fill="black"); y += HL
        linha(dr, x, y, COLS, [n for n, _ in COLS], fb, HL); y += HL
        for cel in col:
            if cel[0] == "g":
                dr.rectangle((x, y, x + TW, y + HL), outline="black", width=2, fill=CINZA)
                dr.text((x + 10, y + (HL - FL) / 2 - 2), cel[1], font=fb, fill=AZUL)
            else:
                r = cel[2]; linha(dr, x, y, COLS, [cel[1], r["qtd"], r["peca"], r["material"], r["medida"], ""], f, HL)
            y += HL
    carimbo(img, dr, fid, "LISTA DE IMPRESSÃO")
    return img

# ---------- paginas explicativas
def g_antes():
    return pagina("G-01", "Antes de começar", "o que é este manual e a ordem do trabalho", [
        ("h", "O que é"),
        ("p", "A Mulbot CoreXY 100³ é a versão compacta da Mulbot CoreXY 200³: mesmo desenho (quadro, guias em V, parafusos e porcas "
              "impressos), com o quadro 100 mm menor em cada eixo. Área de impressão 100 x 100 x 100 mm, mesa aquecida 120 x 120 12 V "
              "com vidro 135 x 135. Nenhuma peça precisa ser cortada nem colada."),
        ("h", "Como o manual está dividido"),
        ("t", [("SEÇÃO", 760), ("O QUE TEM", 780)], [
            ("G-01..03 Guia", "começar, compras, como imprimir"), ("LI Lista de impressão", "todas as peças, com QTD e medida"),
            ("G-04 Roteiro de montagem", "ordem e dicas de cada folha CXY"), ("CXY Montagem", "folhas com vista e lista de peças"),
            ("D Detalhes", "fotos de guia V, extrusora, cabos..."), ("G-05 Ligação", "RAMPS, mesa, firmware e 1ª ligada")]),
        ("h", "Ordem do trabalho"),
        ("n", ["Comprar o que não é impresso (folha G-02).",
               "Imprimir as peças da lista LI e as roldanas em resina (G-03). Marcar a coluna OK.",
               "Montar na ordem das folhas CXY-01 a CXY-11 (roteiro em G-04).",
               "Passar os cabos por dentro do quadro e ligar a RAMPS (CXY-09, CXY-10, G-05).",
               "Firmware, teste dos motores, ajustes e primeira impressão (G-05)."]),
        ("h", "Ferramentas e consumíveis"),
        ("b", ["Chave 14 (bucha excêntrica das roldanas) e chaves pros M3/M6.",
               "Ferro de solda (derreter a ponta dos pinos da esteira e fixar os insertos M3).",
               "Alicate de crimpar e conectores (os fios passam pelo quadro sem conector).",
               "IPA pra lavar as roldanas de resina.",
               "Lixa fina (rebarba de furo e do V dos trilhos)."]),
        ("h", "Quanto dá"),
        ("b", [f"{qt(fdm)} peças FDM em {len(fdm)} arquivos, ~{fil} kg de PLA (estimativa pelo volume das peças).",
               f"{qt(resina)} peças em resina em {len(resina)} arquivos (roldanas V, buchas, fuso alternativo).",
               "Correias A e B de 1044 mm, esteira com 17 elos (8 no X + 9 no Y)."])])

def g_compras():
    extra = [("Parafuso M3 x 10", 12, "braço fim de curso X (2) + esteira (10)"), ("Inserto M3 de latão 4,0 x 6", 8, "braço X (2) + esteira (6)"),
             ("Porca M3", 4, "pontas fixas da esteira"), ("Parafuso M3 x 18", 1, "troca o M3x12 da direita do suporte da extrusora"),
             ("Filamento 1,75 mm (sobra)", "-", "pinos das juntas da esteira")]
    mesa = [("Mesa aquecida 120 x 120, 12 V", 1, "alumínio 3 mm, com termistor 100k NTC 3950"),
            ("Vidro 135 x 135", 1, "vai em cima da placa, preso pelas 4 presilhas"),
            ("Fio da mesa", "-", "2 vias de 1 mm² + 2 vias finas do termistor")]
    mat = [("PLA", f"~{fil} kg", "quase tudo (3 paredes, 10% gyroid)"), ("PETG", "pouco", "polia motriz e os 17 elos da esteira"),
           ("TPU", "pouco", "6 pés de apoio"), ("Resina ABS-like / tough", "-", "15 roldanas V + buchas (Photon)")]
    return pagina("G-02", "O que comprar", "itens que não são impressos (tirados das folhas de montagem)", [
        ("h", "Peças compradas (aparecem nas folhas CXY)"),
        ("t", [("ITEM", 900), ("QTD", 120), ("FOLHA", 520)], [(d, q, o) for d, q, o in COMPRA]),
        ("h", "Mesa aquecida"),
        ("t", [("ITEM", 620), ("QTD", 120), ("OBS.", 800)], mesa),
        ("h", "Comprar a mais (braço do X e esteira)"),
        ("t", [("ITEM", 620), ("QTD", 120), ("ONDE VAI", 800)], extra),
        ("h", "Material de impressão"),
        ("t", [("MATERIAL", 520), ("QTD", 220), ("PRA QUÊ", 800)], mat),
        ("h", "Fora da lista"),
        ("b", ["Fios dos motores, fins de curso, termistores, ventoinhas e cabo de força: medir pelo caminho da CXY-10 (tudo desce pelo poste de trás esquerdo).",
               "Parafusos M10 e M6 do chassi não se compram: são impressos (pasta 08)."])])

def g_imprimir():
    return pagina("G-03", "Como imprimir", "pasta 02: separada pelos mesmos conjuntos das folhas CXY", [
        ("h", "Ajustes do fatiador"),
        ("b", ["PLA, 3 paredes, 10% gyroid. Parafusos e porcas impressos: 4 paredes.",
               "SEM SUPORTE. Tudo foi desenhado pra imprimir sem suporte (paredes até 45°, pontes até 10 mm). Não ligar suporte.",
               "Não girar as peças: os STL já estão na posição de impressão. O desenho sem suporte depende do lado de cima (furo em gota, teto inclinado)."]),
        ("h", "Como ler a lista LI"),
        ("b", ["QTD = quantas vezes imprimir aquele arquivo (também está no nome: [2x]).",
               "MAT. = FDM ou Resina. MEDIDA = tamanho da peça deitada na mesa (X x Y x Z).",
               "Fuso e porca: imprimir SÓ UMA das duas versões (FDM ou resina).",
               "Coluna OK em branco: marcar a caneta o que já saiu da mesa."]),
        ("h", "Materiais diferentes"),
        ("b", ["TPU: pés de apoio (DL1-01-08).", "PETG: polia motriz e os elos da esteira (imprimir os elos em pé).",
               "Resina: pasta 07 Roldanas V. Imprimir deitada, sem suporte, direto na plataforma."]),
        ("h", "Roldanas de resina (15 na máquina)"),
        ("n", ["Resina ABS-like ou tough (a padrão é quebradiça pra isso).",
               "Os 10 roletes nascem presos por pontes de 0,4 mm.",
               "Lavar no IPA, girar com força até soltar, lavar de novo girando, curar."]),
        ("h", "Ordem que economiza erro"),
        ("n", ["Imprimir primeiro 1 parafuso M10 e 1 porca-barril e testar a rosca antes do resto.",
               "Imprimir por conjunto (01 Quadro, 02 Eixo Y...), na ordem das folhas CXY: dá pra ir montando enquanto imprime.",
               "Trilhos X, Y e Z: imprimir com cuidado extra (sem fio de plástico no V), a roldana anda ali."])])

ROT = [("CXY-01 Quadro", ["Montar bases, postes e travessas com os parafusos e porcas-barril M10 impressos.",
                          "Os postes vêm em 2 metades (Inf/Sup) com emenda sobreposta + 2 parafusos M10.",
                          "Antes de fechar, conferir que os canais ocos estão limpos (passagem de cabo, CXY-10)."]),
       ("CXY-02 Eixo Y e pórtico", ["Carro Y: 2 roldanas fixas por dentro + 1 excêntrica por fora (bucha espaçadora, chave 14).",
                                    "Fim de curso Y na torre de trás esquerda: a lingueta aperta com Y = +102."]),
       ("CXY-03 Eixo X e cabeça", ["Carro X: 2 roldanas fixas embaixo + 1 excêntrica em cima, atrás da torre das correias.",
                                   "Fim de curso X na parede do suporte esquerdo: o braço do carro aperta com X = -51,5."]),
       ("CXY-04 Eixo Z", ["O motor Z entra por baixo da base Z (na vista ele aparece descido).",
                          "Fim de curso Z embaixo da viga Y esquerda, com o calço de 3 mm (calcoFimCursoZ) por causa da placa aquecida."]),
       ("CXY-05 Mesa", ["Placa aquecida 120 x 120 nos 4 localizadores (localizador_aq120), vidro 135 x 135 por cima.",
                        "Presilha do vidro (presilha_disco_aq): meia volta solta. Risco em relevo apontando pro vidro = travado."]),
       ("CXY-06 Correias e polias", ["Correia A (de cima) no motor A, trás direito. Correia B (de baixo) no motor B, trás esquerdo.",
                                     "As 2 correias têm 1044 mm. As pontas prendem na torre do carro X, dando a volta no pino."]),
       ("CXY-07 Eletrônica", ["Os cabos entram na caixa da RAMPS pela janela de baixo, vindos do poste de trás esquerdo."]),
       ("CXY-08 Roldana V", ["15 roldanas: 3 no X, 6 no Y, 6 no Z. Excêntrica: girar a bucha até a roda encostar no V sem folga e apertar o M6."]),
       ("CXY-09/10 Ligação e cabos", ["Passar o fio sem conector ao lado das porcas-barril e crimpar depois. Ligações na página G-05."]),
       ("CXY-11 Esteira", ["Esteira X atrás da viga X (8 elos), esteira Y por fora do lado direito (9 elos).",
                           "Pino da junta: 2 pedaços de filamento de 4 mm, derreter a ponta. O M3 da direita do suporte da extrusora vira M3x18."])]
def g_roteiro():
    bl = [("p", "Montar na ordem das folhas. Cada folha CXY tem a vista com balões numerados e a LISTA DE PEÇAS (QTD, peça, "
                "descrição, origem: Nova, Mulbot, Impressa ou Comprada).")]
    for t, ps in ROT: bl += [("h", t), ("b", ps)]
    return pagina("G-04", "Roteiro de montagem", "o que olhar em cada folha CXY", bl)

LIG = [("X", "Motor A (trás direito)"), ("Y", "Motor B (trás esquerdo)"), ("Z (2 conectores)", "Motores Z esq. e dir."),
       ("E0", "Motor E (extrusora direta)"), ("D10", "Aquecedor do hotend 12 V"), ("D9", "Ventoinha 5015 (peça)"),
       ("D8", "Mesa aquecida 120 x 120 12 V"), ("T0", "Termistor do hotend"), ("T1", "Termistor da mesa"),
       ("12 V direto", "Ventoinha do dissipador (sempre ligada)"), ("X-MIN", "Fim de curso X"),
       ("Y-MAX", "Fim de curso Y"), ("Z-MIN", "Fim de curso Z"), ("EXP1 / EXP2", "Display (adaptador + 2 cabos flat)"),
       ("12 V", "Fonte 12 V 150 W"), ("Tomada", "IEC C14 com chave > fonte (L, N, terra)")]
def g_ligacao():
    return pagina("G-05", "Ligação, firmware e primeira ligada", "detalhe do diagrama na folha CXY-09", [
        ("h", "Onde liga cada coisa na RAMPS 1.4"),
        ("t", [("RAMPS", 380), ("APARELHO", 1160)], LIG),
        ("h", "Firmware (Marlin)"),
        ("b", ["#define COREXY. Motor A no driver X, motor B no driver Y.",
               "Área: X_BED_SIZE 100, Y_BED_SIZE 100, Z_MAX_POS 100.",
               "Fins de curso: X no MIN (X = -51,5), Y no MAX (Y = +102), Z no MIN (topo do curso da mesa).",
               "Os 2 motores Z vão nos 2 conectores do Z (em paralelo), sem driver extra.",
               "TEMP_SENSOR_0 1 e TEMP_SENSOR_BED 1 (100k NTC 3950)."]),
        ("h", "Primeira ligada"),
        ("n", ["Sem correia apertada ainda: ligar, ver o display e a temperatura ambiente do hotend e da mesa.",
               "Apertar cada fim de curso com a mão e conferir o estado (M119).",
               "G1 X+10 tem que andar só em X pra direita. Se andar em Y, trocar os cabos A e B. Se andar ao contrário, inverter INVERT_X_DIR / INVERT_Y_DIR.",
               "Ajustar as excêntricas: roda encostada no V, sem folga e sem travar. Mover cada eixo à mão em todo o curso.",
               "Tensionar as correias por igual e fazer o home (G28) com a mão perto da chave.",
               "Aquecer a mesa a 60 °C e conferir se sobe sem passar do valor (PID: M303 E-1 S60 C8).",
               "Nivelar o vidro, calibrar o extrusor e imprimir uma peça pequena de teste."]),
        ("h", "Mesa aquecida"),
        ("p", "A placa de 120 x 120 12 V puxa pouco (cerca de 3 A): vai direto na saída D8 da RAMPS, sem módulo MOSFET, e a fonte de 150 W segura tudo.")])

DETALHES = [("Guia em V (X, Y e Z)", "As roldanas de resina rodam nos trilhos impressos em V. Cada carro tem 2 roldanas fixas e 1 excêntrica: "
             "a bucha excêntrica gira com chave 14 até tirar a folga, depois aperta o M6."),
            ("Extrusora direta", "Extrusora EZR (Bondtech) em cima do hotend E3D Lite6, no carro X. O tubo PTFE é curto (~88 mm) entre a extrusora e o hotend."),
            ("Presilha do vidro (botao excentrico)", "Botão excêntrico nos 4 cantos do vidro de 135 mm, por cima da placa aquecida: meia volta solta o vidro. "
             "O risco em relevo apontando pro vidro indica travado. Imprimir de cabeça pra baixo (topo na mesa, pino pra cima)."),
            ("Passagem de cabos", "Bases, postes, travessas, alma das vigas Y e torres de trás são ocos (parede 2 mm). Tudo desce pelo poste de trás esquerdo "
             "e entra na caixa da RAMPS pela janela de baixo. Ao lado das porcas-barril sobram ~4 mm: passar fio a fio e crimpar depois."),
            ("Esteira porta-cabos", "O cabo da cabeça vai numa esteira impressa em PETG: X atrás da viga X (8 elos) e Y por fora do lado direito (9 elos). "
             "O cabo entra no quadro pela parede de fora da torre de trás direita.")]
ACENTO = {"tras": "trás", "lado": "lado", "iso": "isométrica", "topo": "topo", "visao": "visão", "e": "e"}
def legenda(p): return " ".join(ACENTO.get(w, w) for w in os.path.splitext(os.path.basename(p))[0].split("_"))
def g_detalhes():
    out = []
    for i, (pasta, txt) in enumerate(DETALHES, 1):
        fotos = sorted(glob.glob(f"{DET}/{pasta}/*.png"))[:6]
        out.append(lambda i=i, pasta=pasta, txt=txt, fotos=fotos:
                   pagina_fotos(f"D-{i:02d}", pasta.replace("botao excentrico", "botão excêntrico"), txt, [(p, legenda(p)) for p in fotos]))
    VIS = sorted(glob.glob(f"{RAIZ}/01 Montagem 3D/*.png"))
    if VIS: out.insert(0, lambda: pagina_fotos("D-00", "A máquina montada", "Renders da CoreXY 100 montada (modelo completo em 01 Montagem 3D: .blend, .glb e .3mf).",
                                               [(p, legenda(p).replace("heroi", "vista").replace("carro ", "carro do ")) for p in VIS[:6]]))
    return out

# ---------- ordem do PDF
secoes = [("Antes de começar", [g_antes]), ("O que comprar", [g_compras]), ("Como imprimir", [g_imprimir]),
          ("Lista de impressão (LI)", [lambda i=i, c=c: folha_lista(i, c) for i, c in enumerate(pags_li)]),
          ("Roteiro de montagem", [g_roteiro]),
          ("Folhas de montagem (CXY)", [lambda p=p: Image.open(p).convert("RGB") for p in mont]),
          ("Detalhes em imagens (D)", g_detalhes()),
          ("Ligação, firmware e 1ª ligada", [g_ligacao])]
pg, indice = 2, []
for t, fs in secoes: indice.append((t, len(fs), pg)); pg += len(fs)

def capa():
    img = Image.new("RGB", (SW, SH), "white"); dr = ImageDraw.Draw(img)
    dr.text((M0 + 20, M0 + 40), "MULBOT COREXY 100³", font=fonte(130, True), fill=VERM)
    dr.text((M0 + 30, M0 + 210), "manual completo de impressão e montagem (mesa 120 aquecida)", font=fonte(40), fill="black")
    orig = Image.open(f"{DES}/CXY-00 - Capa e indice.png").convert("RGB")
    ren = orig.crop((40, 530, 2057, 2148)); ren.thumbnail((2000, 1500)); img.paste(ren, (M0, 560))
    xr = 2110
    y = tabela(dr, xr, M0 + 20, "ÍNDICE", [("SEÇÃO", 760), ("FOLHAS", 180), ("PÁG.", 160)],
               [(t, n, p) for t, n, p in indice], fs=25, h=44)
    linhas = [("Arquivos STL na pasta 02", len(lista)), ("Peças FDM a imprimir", qt(fdm)),
              ("Peças em resina (roldanas V, fuso alt.)", qt(resina)), ("Elos da esteira (PETG)", 17),
              ("Correias A e B", "1044 mm cada"), ("Filamento PLA estimado", f"~{fil} kg")]
    y = tabela(dr, xr, y + 40, "QUANTIDADES", [("ITEM", 760), ("QTD", 340)], linhas, fs=25, h=44)
    notas(dr, xr, y + 40, 1100, "NOTAS", [
        "Comece pela página 2 (Antes de começar): ela explica a ordem do trabalho.",
        "Área de impressão 100 x 100 x 100 mm. Quadro, guias e fixadores impressos (M10 no chassi, M6 nas médias).",
        "Mesma família da CoreXY 200³, 100 mm menor em cada eixo.",
        "Mulbot DL1 original: 3D Printing World. Esta versão CoreXY muda quadro, eixos, mesa e cabos."], fs=25)
    carimbo(img, dr, "CAPA", "CAPA, ÍNDICE E QUANTIDADES")
    return img

w = pypdf.PdfWriter()                                  # uma pagina por vez (A4 300 dpi nao cabe tudo junto na RAM)
for g in [capa] + [f for _, fs in secoes for f in fs]:
    b = io.BytesIO(); im = g(); im.save(b, "PDF", resolution=300); im.close(); w.append(pypdf.PdfReader(b))
w.write(OUT)
print("PDF", pg - 1, "páginas:", ", ".join(f"{t} {n}" for t, n, _ in indice))
