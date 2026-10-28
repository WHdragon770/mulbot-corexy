# Folhas de emenda da 200 impressa na 100: uma folha por peca cortada (partes afastadas + pinos/luvas no lugar,
# tabela das partes, como emendar) + capa com indice. Le o cortes.json do cortar_na_100.py.
# Uso: python3 emendas.py <saida do cortar_na_100> <pasta das folhas>
import sys, os, json, re, math, datetime, subprocess, numpy as np, trimesh
from PIL import Image, ImageDraw, ImageFont
SRC, DST = sys.argv[1], sys.argv[2]
AQUI = os.path.dirname(os.path.abspath(__file__)); TMP = os.path.join(DST, "_tmp")
BL = os.path.expanduser("~/.local/opt/blender-4.2.3-linux-x64/blender")
ENV = dict(os.environ, LD_LIBRARY_PATH=os.path.expanduser("~/.local/opt/blibs/root/usr/lib/x86_64-linux-gnu"))
F = "/usr/share/fonts/truetype/dejavu/DejaVuSans"
def fonte(t, b=False): return ImageFont.truetype(F + ("-Bold" if b else "") + ".ttf", t)
SW, SH, M0, CAR = 3508, 2480, 70, 150                 # A4 deitada 300 dpi, margem, faixa do carimbo
AZUL = "#1a5f8a"
INFO = json.load(open(f"{SRC}/cortes.json"))
REL = {}
for l in open(f"{SRC}/cortes.txt").read().splitlines()[1:]:
    n, t = l.strip().split(": ", 1); REL.setdefault(n, []).append(t)
FIC = {}

def pino_stl(d, L):
    k = (d, round(L, 1))
    if k not in FIC:
        fn = f"{TMP}/pino_{d}_{L:.1f}.stl"
        trimesh.creation.cylinder(radius=(4.6 if d == "D" else d / 2), height=L, sections=32).export(fn); FIC[k] = fn
    return FIC[k]

def Tmat(t, eixo=2):
    R = np.eye(4)
    if eixo == 0: R[:3, :3] = trimesh.transformations.rotation_matrix(math.pi / 2, [0, 1, 0])[:3, :3]
    if eixo == 1: R[:3, :3] = trimesh.transformations.rotation_matrix(math.pi / 2, [1, 0, 0])[:3, :3]
    R[:3, 3] = t; return R.tolist()

def renderiza(fid, itens, v):
    ij, vj, png = f"{TMP}/{fid}_itens.json", f"{TMP}/{fid}_vista.json", f"{TMP}/{fid}.png"
    json.dump(itens, open(ij, "w")); json.dump(v, open(vj, "w"))
    r = subprocess.run([BL, "-b", "--factory-startup", "-P", f"{AQUI}/render_folha.py", "--", ij, vj, png], env=ENV, capture_output=True, text=True)
    if not os.path.exists(png): sys.exit(r.stdout[-2000:] + r.stderr[-2000:])
    return png, json.load(open(png[:-4] + ".json"))

def carimbo(img, dr, fid, titulo):
    dr.rectangle((M0 / 2, M0 / 2, SW - M0 / 2, SH - M0 / 2), outline="black", width=3)
    x0 = SW - CAR - M0 / 2; dr.line((x0, M0 / 2, x0, SH - M0 / 2), fill="black", width=3)
    blocos = [("MULBOT COREXY 200³", 46, True, 760), ("impressa na CoreXY 100 (partes ≤ 95 mm)", 26, False, 640),
              (f"{datetime.date.today():%d/%m/%Y}", 26, False, 240), (f"FOLHA: {fid}", 34, True, 300), (f"TÍTULO: {titulo}", 30, True, 0)]
    y = M0 / 2
    for t, s, b, h in blocos:
        if h == 0: h = SH - M0 / 2 - y
        txt = Image.new("RGBA", (int(h), CAR - 10), (255, 255, 255, 0)); d2 = ImageDraw.Draw(txt)
        f = fonte(s, b); tw = d2.textlength(t, font=f)
        while tw > h - 30: s -= 2; f = fonte(s, b); tw = d2.textlength(t, font=f)
        d2.text(((h - tw) / 2, (CAR - 10 - s) / 2 - 4), t, font=f, fill="black")
        txt = txt.rotate(90, expand=True); img.paste(txt, (int(x0 + 5), int(y)), txt); y += h
        if y < SH - M0: dr.line((x0, y, SW - M0 / 2, y), fill="black", width=3)

def quebra(dr, t, f, w):
    ls, l = [], ""
    for p in t.split():
        if l and dr.textlength(l + " " + p, font=f) > w: ls.append(l); l = p
        else: l = (l + " " + p).strip()
    return ls + [l]

def tabela(dr, x0, y0, titulo, cols, linhas, hl=46, fs=26):
    W = sum(c[1] for c in cols); f, fb = fonte(fs), fonte(fs, True)
    dr.rectangle((x0, y0, x0 + W, y0 + hl), outline="black", width=2)
    dr.text((x0 + W / 2 - dr.textlength(titulo, font=fb) / 2, y0 + 9), titulo, font=fb, fill="black"); y = y0 + hl
    for row, fnt in [([c[0] for c in cols], fb)] + [(r, f) for r in linhas]:
        cel = [quebra(dr, str(t), fnt, c[1] - 16) for t, c in zip(row, cols)]; h = max(len(c) for c in cel) * (fs + 8) + 14
        x = x0
        for c, ls in zip(cols, cel):
            dr.rectangle((x, y, x + c[1], y + h), outline="black", width=2)
            for k, l in enumerate(ls): dr.text((x + 8, y + 7 + k * (fs + 8)), l, font=fnt, fill="black")
            x += c[1]
        y += h
    return y

def notas(dr, x0, y0, w, titulo, nts, fs=27):
    dr.text((x0, y0), titulo, font=fonte(fs + 2, True), fill="black"); y = y0 + fs + 16; f = fonte(fs)
    for i, n in enumerate(nts, 1):
        ls = quebra(dr, n, f, w - 46); dr.text((x0, y), f"{i}.", font=f, fill="black")
        for l in ls: dr.text((x0 + 40, y), l, font=f, fill="black"); y += fs + 9
        y += 6
    return y

def nome_pino(d, L): return "pino em D 9,2 x 24 mm (fuso)" if d == "D" else f"pino Ø{d:.0f} x {L:.1f} mm".replace(".", ",")

COMO = {"pino": "Pinos (pasta 00 Pinos): passar cola nos furos e na face de corte, encaixar o pino numa parte, fechar a outra por cima e prender até curar. Cola: cianoacrilato com ativador ou epóxi 5 min.",
        "luva": "Luva de emenda: entra por dentro da parede, metade em cada parte. Colar a luva numa parte, esperar firmar e colar a outra.",
        "macho": "Encaixe macho já impresso na parte de baixo: passar cola e encaixar a parte de cima.",
        "cola": "Corte só com cola (sem lugar pra pino): lixar as faces, colar de topo com epóxi e deixar curar 24 h antes de apertar parafuso.",
        "D": "Fuso: o pino em D entra no furo central das 2 metades e alinha a rosca. Colar o pino, encaixar e conferir a rosca com a porca antes da cola curar."}

def folha(fid, nome, inf):
    os.makedirs(TMP, exist_ok=True)
    pasta = os.path.join(SRC, inf["pasta"])
    partes = []
    for p in inf["partes"]:
        t = trimesh.load(os.path.join(pasta, p["arq"]), force="mesh"); off = np.array(p["off"])
        partes.append(dict(arq=p["arq"], off=off, ext=t.extents, c=off + t.extents / 2))
    C = np.mean([p["c"] for p in partes], 0)
    spread = np.ptp([p["c"] for p in partes], 0); eixos = spread > 15
    def desl(x): return np.where(eixos, (np.asarray(x) - C) * 0.45, 0)
    itens = []
    for i, p in enumerate(partes, 1):
        itens.append(dict(nome=f"parte{i}", stl=os.path.join(pasta, p["arq"]), T=Tmat(p["off"] + desl(p["c"])), cor="cinza" if i % 2 else "alu"))
    for k, q in enumerate(inf.get("pinos", [])):
        itens.append(dict(nome=f"pino{k}", stl=pino_stl(q["d"], q["L"]), T=Tmat(np.array(q["p"]) + desl(q["p"]), q["eixo"]), cor="verm"))
    for k, fl in enumerate(inf.get("luvas_stl", [])):
        c = trimesh.load(fl).bounds.mean(0); itens.append(dict(nome=f"luva{k}", stl=fl, T=Tmat(desl(c)), cor="azul"))
    png, anc = renderiza(fid, itens, dict(dir=[1, -1.3, 0.9], res=[2280, 2180], margem=1.12))
    img = Image.new("RGB", (SW, SH), "white"); dr = ImageDraw.Draw(img)
    r = Image.open(png); img.paste(r, (M0, M0 + 70), r)
    tit = DESCR.get(nome, nome)
    dr.text((M0 + 10, M0), f"{nome}  ·  {tit}", font=fonte(52, True), fill="black")
    for i in range(1, len(partes) + 1):                        # balao em cima de cada parte (ponto visivel mais central)
        a = anc.get(f"parte{i}")
        if not a: continue
        pts = np.array(a[1]); cx, cy = pts[np.argmin(np.linalg.norm(pts - pts.mean(0), axis=1))]
        x, y = M0 + cx, M0 + 70 + cy; R = 38
        dr.ellipse((x - R, y - R, x + R, y + R), fill="white", outline="black", width=4)
        s = str(i); f = fonte(40, True); dr.text((x - dr.textlength(s, font=f) / 2, y - 25), s, font=f, fill="black")
    x0 = M0 + 2330; wcol = SW - CAR - M0 / 2 - 40 - x0
    linhas = [[str(i), re.sub(r"^.* (parte \d+de\d+).*$", r"\1", p["arq"]), " x ".join(f"{v:.0f}" for v in sorted(p["ext"], reverse=True)) + " mm"] for i, p in enumerate(partes, 1)]
    y = tabela(dr, x0, M0, f"PARTES (imprimir {inf['qtd']}x cada)", [("Nº", 80), ("Arquivo", wcol - 80 - 330), ("Medidas", 330)], linhas)
    pin = {}
    for q in inf.get("pinos", []): k = nome_pino(q["d"], q["L"]); pin[k] = pin.get(k, 0) + 1
    lig = [[k, f"{v * inf['qtd']}"] for k, v in pin.items()] + [[l, f"{inf['qtd']}"] for l in [re.sub(r" \[\d+x\]\.stl$", "", x).replace(nome + " ", "") for x in inf.get("luvas", [])]]
    if lig: y = tabela(dr, x0, y + 40, "PEÇAS DE EMENDA", [("Item", wcol - 200), ("Qtd total", 200)], lig)
    cortes = [t[0].upper() + t[1:] for t in REL.get(nome, [])]
    y = notas(dr, x0, y + 50, wcol, "CORTES", cortes)
    tipos = {"pino" if "pino(s)" in t else "D" if "em D" in t else "luva" if "luva" in t else "macho" if "macho" in t else "cola" for t in REL.get(nome, [])}
    notas(dr, x0, y + 30, wcol, "COMO EMENDAR", [COMO[t] for t in ("pino", "D", "luva", "macho", "cola") if t in tipos] +
          [f"Pasta: 02b STL para imprimir na 100\\{inf['pasta']}. Peça inteira: " + " x ".join(f"{v:.0f}" for v in sorted(inf["ext"], reverse=True)) + " mm.",
           "Vermelho = pino, azul = luva. Conferir o encaixe a seco antes de colar."])
    carimbo(img, dr, fid, f"EMENDA: {nome}")
    return img

def capa(lst):
    img = Image.new("RGB", (SW, SH), "white"); dr = ImageDraw.Draw(img)
    dr.text((M0 + 30, M0 + 20), "MULBOT COREXY 200³", font=fonte(100, True), fill="#b3261e")
    dr.text((M0 + 36, M0 + 150), "Desenhos de emenda: peças da 200 cortadas pra imprimir na CoreXY 100", font=fonte(40), fill="black")
    tp = {}
    for v in REL.values():
        for t in v:
            k = "pino" if "pino(s)" in t else "D" if "em D" in t else "luva" if "luva" in t else "macho" if "macho" in t else "cola"; tp[k] = tp.get(k, 0) + 1
    notas(dr, M0 + 30, M0 + 260, 1500, "RESUMO", [f"{len(lst)} peças maiores que 95 mm foram cortadas; as outras imprimem inteiras (pasta 02b, mesma divisão da 02).",
          f"Cortes: {tp.get('pino', 0)} com pino, {tp.get('luva', 0)} com luva, {tp.get('macho', 0)} com encaixe macho, {tp.get('D', 0)} com pino em D (fuso), {tp.get('cola', 0)} só com cola.",
          "Pinos impressos em 00 Pinos (furo = pino + 0,4 mm). Imprimir os pinos em PETG ou PLA, 100% de preenchimento.",
          "Cada folha mostra as partes afastadas na direção do corte, com os pinos e luvas no lugar, a lista das partes e como emendar."] +
          [f"{k.capitalize() if k != 'D' else 'Pino em D'}: {COMO[k]}" for k in ("pino", "D", "luva", "macho", "cola") if k in tp])
    meio = (len(lst) + 1) // 2
    for c, parte in enumerate((lst[:meio], lst[meio:])):
        tabela(dr, M0 + 1620 + c * 790, M0 + 30, "ÍNDICE" if c == 0 else "ÍNDICE (cont.)", [("Folha", 160), ("Peça", 600)],
               [[f, n] for f, n in parte], hl=44, fs=22)
    carimbo(img, dr, "EM-00", "CAPA E ÍNDICE")
    return img

_src = open(f"{AQUI}/folhas.py").read()       # nomes descritivos das pecas, os mesmos das folhas de montagem
DESC = eval(re.search(r"DESC = (\{.*?\})\n", _src, re.S).group(1)); LADO = {"D": "lado direito", "E": "lado esquerdo"}
class _D(dict):
    def get(self, n, d=None):
        b, _, l = n.partition("_"); t = DESC.get(b) or next((v for k, v in DESC.items() if b.startswith(k)), None)
        return (t + (", " + LADO[l] if l in LADO else "")) if t else d
DESCR = _D()
os.makedirs(DST, exist_ok=True); os.makedirs(TMP, exist_ok=True)
nomes = sorted(INFO, key=lambda n: (INFO[n]["pasta"], n)); lst, pags = [], []
for i, n in enumerate(nomes, 1):
    fid = f"EM-{i:02d}"; lst.append((fid, n)); print(fid, n, flush=True)
    im = folha(fid, n, INFO[n]); im.save(f"{DST}/{fid} - {n}.png"); pags.append(im)
cp = capa(lst); cp.save(f"{DST}/EM-00 - Capa e indice.png")
cp.save(f"{DST}/Mulbot CoreXY 200 na 100 - desenhos de emenda.pdf", save_all=True, append_images=pags, resolution=300)
print("PDF", len(pags) + 1, "folhas")
