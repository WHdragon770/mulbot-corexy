# PDF completo da 200 impressa na 100: capa com indice e quantidades + folhas de montagem originais (CXY-01..)
# + lista de impressao (02b, com quantidades) + folhas de emenda (EM-01..). So junta o que ja foi gerado.
# Uso: python3 completo.py <pasta 02b> <pasta desenhos 03> <pasta emendas 03b> <saida.pdf>
import sys, os, glob, csv, re, datetime
from PIL import Image, ImageDraw, ImageFont
STL, DES, EMD, OUT = sys.argv[1:5]
F = "/usr/share/fonts/truetype/dejavu/DejaVuSans"
def fonte(t, b=False): return ImageFont.truetype(F + ("-Bold" if b else "") + ".ttf", t)
SW, SH, M0, CAR = 3508, 2480, 70, 150
X1 = SW - CAR - M0 / 2                                 # comeco da faixa do carimbo
VERM, AZUL, CINZA = "#b8282b", "#1a5f8a", "#e8eef2"

def carimbo(img, dr, fid, titulo):
    dr.rectangle((M0 / 2, M0 / 2, SW - M0 / 2, SH - M0 / 2), outline="black", width=3)
    dr.line((X1, M0 / 2, X1, SH - M0 / 2), fill="black", width=3)
    blocos = [("MULBOT COREXY 200³", 46, True, 760), ("impressa na CoreXY 100 (partes ≤ 95 mm)", 26, False, 640),
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

def linha(dr, x, y, cols, vals, f, h, fundo=None):
    for (_, w), v in zip(cols, vals):
        dr.rectangle((x, y, x + w, y + h), outline="black", width=2, fill=fundo)
        dr.text((x + 8, y + (h - f.size) / 2 - 2), str(v), font=f, fill="black"); x += w

def tabela(dr, x, y, titulo, cols, rows, fs=26, h=46):
    W = sum(c[1] for c in cols); fb, f = fonte(fs, True), fonte(fs)
    dr.rectangle((x, y, x + W, y + h), outline="black", width=2)
    dr.text((x + W / 2 - dr.textlength(titulo, font=fb) / 2, y + (h - fs) / 2 - 2), titulo, font=fb, fill="black"); y += h
    linha(dr, x, y, cols, [c[0] for c in cols], fb, h); y += h
    for r in rows: linha(dr, x, y, cols, r, f, h); y += h
    return y

def notas(dr, x, y, w, titulo, nts, fs=27):
    dr.text((x, y), titulo, font=fonte(fs + 2, True), fill="black"); y += fs + 16; f = fonte(fs)
    for i, n in enumerate(nts, 1):
        dr.text((x, y), f"{i}.", font=f, fill="black"); l = ""
        for p in n.split():
            if l and dr.textlength(l + " " + p, font=f) > w - 46: dr.text((x + 40, y), l, font=f, fill="black"); y += fs + 9; l = p
            else: l = (l + " " + p).strip()
        dr.text((x + 40, y), l, font=f, fill="black"); y += fs + 9
    return y

# ---------- dados
lista = list(csv.DictReader(open(f"{STL}/lista_de_impressao.csv", encoding="utf-8-sig"), delimiter=";"))
mont = sorted(p for p in glob.glob(f"{DES}/CXY-*.png") if not os.path.basename(p).startswith("CXY-00"))
emen = sorted(p for p in glob.glob(f"{EMD}/EM-*.png") if not os.path.basename(p).startswith("EM-00"))
leia = open(f"{STL}/00 LEIA-ME.txt", encoding="utf-8", errors="replace").read()
fil = re.search(r"FILAMENTO.*?~([\d,]+) kg", leia); fil = fil.group(1) if fil else "?"
resina = [r for r in lista if "Resina" in r["pasta"]]
fdm = [r for r in lista if "Resina" not in r["pasta"]]
qt = lambda rs: sum(int(r["qtd"]) for r in rs)
cort = [r for r in lista if " parte " in r["arquivo"]]
luvas = [r for r in lista if " luva " in r["arquivo"]]
pinos = [r for r in lista if r["pasta"] == "00 Pinos"]
nome = lambda a: a[:-4] if a.lower().endswith(".stl") else a

# ---------- lista de impressao: 2 colunas por folha, cabecalho por pasta
COLS = [("ITEM", 100), ("QTD", 100), ("ARQUIVO (pasta 02b)", 980), ("MEDIDA (mm)", 300)]
TW, HL, FS = sum(c[1] for c in COLS), 44, 24
Y0, YMAX = M0 + 150, SH - M0 - 30
grupos = {}
for r in lista: grupos.setdefault(r["pasta"], []).append(r)
celulas = []                                           # ("g", pasta) ou ("r", item, linha)
it = 0
for p, rs in grupos.items():
    celulas.append(("g", f"{p}  ({len(rs)} arquivos, {qt(rs)} peças)"))
    for r in rs: it += 1; celulas.append(("r", it, r))
pags_li, k = [], 0
while k < len(celulas):
    pags_li.append([]);
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
    fb, f = fonte(FS, True), fonte(FS)
    for c, col in enumerate(cols):
        x = M0 + 20 + c * (TW + 80); y = Y0
        dr.rectangle((x, y, x + TW, y + HL), outline="black", width=2)
        t = "PEÇAS PARA IMPRIMIR NA COREXY 100" + ("" if c == 0 else " (cont.)")
        dr.text((x + TW / 2 - dr.textlength(t, font=fb) / 2, y + (HL - FS) / 2 - 2), t, font=fb, fill="black"); y += HL
        linha(dr, x, y, COLS, [n for n, _ in COLS], fb, HL); y += HL
        for cel in col:
            if cel[0] == "g":
                dr.rectangle((x, y, x + TW, y + HL), outline="black", width=2, fill=CINZA)
                dr.text((x + 10, y + (HL - FS) / 2 - 2), cel[1], font=fb, fill=AZUL)
            else:
                r = cel[2]; linha(dr, x, y, COLS, [cel[1], r["qtd"], nome(r["arquivo"]), r["medida (mm)"].replace("x", " x ")], f, HL)
            y += HL
    carimbo(img, dr, fid, "LISTA DE IMPRESSÃO")
    return img

# ---------- capa
pg_mont, pg_li = 2, 2 + len(mont); pg_em = pg_li + NLI
def capa():
    img = Image.new("RGB", (SW, SH), "white"); dr = ImageDraw.Draw(img)
    dr.text((M0 + 20, M0 + 40), "MULBOT COREXY 200³", font=fonte(130, True), fill=VERM)
    dr.text((M0 + 30, M0 + 210), "impressa na CoreXY 100: montagem, lista de impressão com quantidades e emendas", font=fonte(40), fill="black")
    orig = Image.open(f"{DES}/CXY-00 - Capa e indice.png").convert("RGB")
    ren = orig.crop((40, 530, 2057, 2148)); ren.thumbnail((2000, 1500)); img.paste(ren, (M0, 560))
    xr = 2110
    y = tabela(dr, xr, M0 + 20, "ÍNDICE", [("SEÇÃO", 700), ("FOLHAS", 260), ("PÁG.", 140)], [
        ("Capa, índice e quantidades", "CAPA", 1),
        ("Desenhos de montagem (original)", f"CXY-01..{len(mont):02d}", pg_mont),
        ("Lista de impressão (02b)", f"LI-01..{NLI:02d}", pg_li),
        ("Desenhos de emenda", f"EM-01..{len(emen):02d}", pg_em)], fs=25, h=46)
    linhas = [("Arquivos STL na 02b", len(lista)), ("Peças FDM a imprimir (com pinos)", qt(fdm)),
              ("Peças originais cortadas", len(emen)), ("Partes das peças cortadas", qt(cort))]
    linhas += [(nome(p["arquivo"]).split(" [")[0].replace("pino", "Pino"), p["qtd"]) for p in pinos]
    linhas += [("Luvas de emenda", qt(luvas)), ("Peças em resina (roldanas V, fuso alt.)", qt(resina)),
               ("Filamento PLA estimado", f"~{fil} kg (5 rolos de 1 kg)")]
    y = tabela(dr, xr, y + 50, "QUANTIDADES", [("ITEM", 760), ("QTD", 340)], linhas, fs=25, h=46)
    notas(dr, xr, y + 50, 1100, "NOTAS", [
        "Folhas CXY: montagem igual à 200 original. As quantidades da LISTA DE PEÇAS valem para a peça inteira.",
        "Folhas LI: tudo o que vai na mesa da 100 (até 95 mm). QTD = quantas vezes imprimir aquele arquivo.",
        "Folhas EM: como colar cada peça cortada (pinos em vermelho, luvas em azul).",
        "Resina: roldanas V e fuso alternativo vão na impressora de resina, sem corte.",
        "Pinos impressos com sobra. Furo = pino + 0,4 mm. Cola: cianoacrilato com ativador ou epóxi 5 min."], fs=25)
    carimbo(img, dr, "CAPA", "CAPA, ÍNDICE E QUANTIDADES")
    return img

import pypdf, io                                      # uma pagina por vez (70 folhas A4 300 dpi nao cabem juntas na RAM)
fontes = [capa] + [lambda p=p: Image.open(p).convert("RGB") for p in mont] + \
         [lambda i=i, c=c: folha_lista(i, c) for i, c in enumerate(pags_li)] + [lambda p=p: Image.open(p).convert("RGB") for p in emen]
w = pypdf.PdfWriter()
for g in fontes:
    b = io.BytesIO(); im = g(); im.save(b, "PDF", resolution=300); im.close(); w.append(pypdf.PdfReader(b))
w.write(OUT)
print("PDF", len(fontes), "páginas:", len(mont), "CXY,", NLI, "LI,", len(emen), "EM")
