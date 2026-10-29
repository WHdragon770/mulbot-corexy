# Ficha tecnica: vistas ortograficas (ficha_render.py) viram pranchas cotadas com texto e carimbo, no padrao das pranchas de conferencia.
# Uso: python3 ficha_monta.py <100|200> <pasta dos renders> <saida> [pasta dos renders da outra maquina, pro comparativo]
import sys, os, json, math, datetime
from PIL import Image, ImageDraw, ImageFont
MAQ, SRC, DST = sys.argv[1], sys.argv[2], sys.argv[3]; OUTRA = sys.argv[4] if len(sys.argv) > 4 else None
F = "/usr/share/fonts/truetype/dejavu/DejaVuSans"
def fonte(t, b=False): return ImageFont.truetype(F + ("-Bold" if b else "") + ".ttf", t)
AZUL, CINZA, VOL = "#1a5f8a", "#5a5f66", (0, 120, 215)
J = {v: json.load(open(f"{SRC}/{v}.json")) for v in ("frente", "lado", "topo", "iso")}
lo, hi = J["frente"]["lo"], J["frente"]["hi"]; A = int(J["frente"]["area"])
L, P_, H_ = (round(hi[i] - lo[i]) for i in range(3))
VID = round(J["frente"]["vhi"][0] - J["frente"]["vlo"][0]); SOB = (VID - A) / 2
ESP = {"200": [("Cinemática", "CoreXY"), ("Volume de impressão", f"{A} x {A} x {A} mm"), ("Dimensões externas", f"{L} x {P_} x {H_} mm"),
               ("Vidro da mesa", f"{VID} x {VID} mm"), ("Mesa aquecida", "220 x 220 mm, 12 V (opcional)"), ("Guias", "em V impressas, roldanas de resina"),
               ("Eixo Z", "2 fusos, 2 motores"), ("Extrusora", "direta, sobre o carro"), ("Eletrônica", "RAMPS 1.4 + Arduino Mega"),
               ("Fonte", "12 V 150 W"), ("Peças impressas", "338 peças, ~4 kg (20 placas)")],
       "100": [("Cinemática", "CoreXY"), ("Volume de impressão", f"{A} x {A} x {A} mm"), ("Dimensões externas", f"{L} x {P_} x {H_} mm"),
               ("Vidro da mesa", f"{VID} x {VID} mm"), ("Mesa aquecida", "120 x 120 mm, 12 V"), ("Guias", "em V impressas, roldanas de resina"),
               ("Eixo Z", "2 fusos, 2 motores"), ("Extrusora", "direta, sobre o carro"), ("Eletrônica", "RAMPS 1.4 + Arduino Mega"),
               ("Fonte", "12 V 150 W"), ("Peças impressas", "11 placas na Kobra X")]}[MAQ]
TXT = {
 "frente": ("Vista frontal", f"Vista ortográfica de frente, sem perspectiva. As cotas pretas são as medidas externas, tomadas nas partes mais salientes (pés, display, motores e caixa da eletrônica). Em azul, o volume útil de impressão de {A} x {A} x {A} mm: o espaço varrido pela peça enquanto a mesa desce do bico até o fim do curso Z."),
 "lado": ("Vista lateral", f"Vista ortográfica do lado direito. A profundidade total vai do display, na frente, até a caixa da eletrônica, atrás. O curso Z é feito pela mesa, que desce pelos 2 fusos; o bico fica sempre na mesma altura e só se move em X e Y."),
 "topo": ("Vista superior", f"Vista de cima. O quadrado azul é a área de impressão de {A} x {A} mm, centrada no vidro de {VID} x {VID} mm (tracejado cinza). A sobra de {SOB:.1f} mm por lado acomoda as presilhas do vidro sem invadir a área útil.".replace(".0 mm", " mm").replace(".5 mm", ",5 mm")),
 "iso": ("Vista isométrica", f"Vista axonométrica com as 3 medidas externas e o volume útil de {A} x {A} x {A} mm destacado em azul, na posição em que a peça fica ao fim de uma impressão de altura máxima (mesa no ponto mais baixo)."),
 "comp": ("Comparativo 100 x 200", "As duas máquinas lado a lado na mesma escala, com o volume de impressão de cada uma em azul. Mesmo projeto e mesmas peças de guia, carro e eletrônica; muda o tamanho do quadro, dos trilhos, da mesa e das correias."),
}
W, H, M, CW = 1700, 1500, 40, 820
SW, SH = W + CW + 3 * M, H + 2 * M
def quebra(dr, t, f, w):
    ls, l = [], ""
    for p in t.split():
        if dr.textlength((l + " " + p).strip(), font=f) > w: ls.append(l); l = p
        else: l = (l + " " + p).strip()
    return ls + [l]
def fundo(w, h):
    fu = Image.new("RGB", (w, h)); fd = ImageDraw.Draw(fu)
    for yy in range(h): t = yy / h; fd.line((0, yy, w, yy), fill=tuple(int(a + (b - a) * t) for a, b in zip((246, 247, 249), (214, 219, 225))))
    return fu
def rotulo(im, xy, txt, cor, ang=0, tam=30):                      # texto com fundo branco, girado no angulo da cota
    f = fonte(tam, True); d0 = ImageDraw.Draw(im); w = int(d0.textlength(txt, font=f)) + 20; h = tam + 16
    t = Image.new("RGBA", (w, h), (255, 255, 255, 235)); ImageDraw.Draw(t).text((10, 5), txt, font=f, fill=cor)
    ang = ((ang + 90) % 180) - 90; t = t.rotate(-ang, expand=True, resample=Image.BICUBIC)
    im.paste(t, (int(xy[0] - t.width / 2), int(xy[1] - t.height / 2)), t)
def seta(dr, p, q, cor, s=18):
    a = math.atan2(q[1] - p[1], q[0] - p[0])
    for da in (0.38, -0.38): dr.line((p[0], p[1], p[0] + s * math.cos(a + da), p[1] + s * math.sin(a + da)), fill=cor, width=3)
def cota(im, p1, p2, n, dist, txt, cor="black"):                 # n = direcao (unitaria) pra fora da peca
    dr = ImageDraw.Draw(im); a = (p1[0] + n[0] * dist, p1[1] + n[1] * dist); b = (p2[0] + n[0] * dist, p2[1] + n[1] * dist)
    for p, q in ((p1, a), (p2, b)): dr.line((p[0] + n[0] * 8, p[1] + n[1] * 8, q[0] + n[0] * 14, q[1] + n[1] * 14), fill=cor, width=2)
    dr.line((*a, *b), fill=cor, width=3); seta(dr, a, b, cor); seta(dr, b, a, cor)
    rotulo(im, ((a[0] + b[0]) / 2, (a[1] + b[1]) / 2), txt, cor, math.degrees(math.atan2(b[1] - a[1], b[0] - a[0])))
def tracejado(dr, pts, cor, w=3, tr=16, gap=10):
    for p, q in zip(pts, pts[1:] + pts[:1]):
        d = math.dist(p, q); n = int(d // (tr + gap)) + 1
        for k in range(n):
            t0, t1 = k * (tr + gap) / d, min((k * (tr + gap) + tr) / d, 1)
            dr.line((p[0] + (q[0] - p[0]) * t0, p[1] + (q[1] - p[1]) * t0, p[0] + (q[0] - p[0]) * t1, p[1] + (q[1] - p[1]) * t1), fill=cor, width=w)
def bb(pts): xs, ys = [p[0] for p in pts], [p[1] for p in pts]; return min(xs), min(ys), max(xs), max(ys)
def vista(v):
    j = J[v]; im = fundo(W, H).convert("RGBA"); r = Image.open(f"{SRC}/{v}.png").convert("RGBA"); im.alpha_composite(r)
    ov = Image.new("RGBA", (W, H)); od = ImageDraw.Draw(ov); vp = j["volume"]
    if v == "iso":                                                  # faces do cubo do volume (indice = xi*4 + yi*2 + zi)
        for f in ((0, 2, 6, 4), (1, 3, 7, 5), (0, 1, 5, 4), (2, 3, 7, 6), (0, 1, 3, 2), (4, 5, 7, 6)): od.polygon([tuple(vp[i]) for i in f], fill=(*VOL, 28))
        im.alpha_composite(ov); dr = ImageDraw.Draw(im)
        for i in range(8):
            for b in (1, 2, 4):
                if not i & b: dr.line((*vp[i], *vp[i | b]), fill=VOL, width=3)
        c = j["caixa"]; cx = sum(p[0] for p in c) / 8; cy = sum(p[1] for p in c) / 8
        def fora(i, k, dist):                                       # cota na aresta i -> k, empurrada pra longe do centro
            mx, my = (c[i][0] + c[k][0]) / 2 - cx, (c[i][1] + c[k][1]) / 2 - cy; ex, ey = c[k][0] - c[i][0], c[k][1] - c[i][1]
            nx, ny = -ey, ex; s = math.hypot(nx, ny); nx, ny = nx / s, ny / s
            if nx * mx + ny * my < 0: nx, ny = -nx, -ny
            return (nx, ny)
        for i, k, txt in ((0, 4, f"{L} mm"), (4, 6, f"{P_} mm"), (6, 7, f"{H_} mm")):
            cota(im, c[i], c[k], fora(i, k, 0), 70, txt)
        x0, y0, x1, y1 = bb(vp); rotulo(im, ((x0 + x1) / 2, y1 + 40), f"Volume de impressão {A} x {A} x {A} mm", VOL, 0, 28)
        return im
    hx, vy = {"frente": (0, 2), "lado": (1, 2), "topo": (0, 1)}[v]
    md = {0: L, 1: P_, 2: H_}
    x0, y0, x1, y1 = bb(j["caixa"]); X0, Y0, X1, Y1 = bb(vp)
    od.rectangle((X0, Y0, X1, Y1), fill=(*VOL, 34)); im.alpha_composite(ov); dr = ImageDraw.Draw(im)
    tracejado(dr, [(X0, Y0), (X1, Y0), (X1, Y1), (X0, Y1)], VOL, 4)
    if v == "topo":
        tracejado(dr, [tuple(p) for p in j["vidro"]], (90, 95, 102), 3, 10, 8); g = bb(j["vidro"])
        cota(im, (g[0], g[3]), (g[2], g[3]), (0, 1), 46, f"vidro {VID} mm", (90, 95, 102))
    cota(im, (x0, y1), (x1, y1), (0, 1), 80, f"{md[hx]} mm")
    cota(im, (x0, y0), (x0, y1), (-1, 0), 80, f"{md[vy]} mm")
    cota(im, (X0, Y0), (X1, Y0), (0, -1), 40, f"{A} mm", VOL)          # fora da caixa: na 100 ela e pequena e os rotulos se cruzavam
    cota(im, (X1, Y0), (X1, Y1), (1, 0), 40, f"{A} mm", VOL)
    return im
def comparativo():
    jo = json.load(open(f"{OUTRA}/iso.json")); ja = J["iso"]; k = jo["mm_px"] / ja["mm_px"]   # mesma escala (mm por pixel)
    a = Image.open(f"{SRC}/iso.png").convert("RGBA"); o = Image.open(f"{OUTRA}/iso.png").convert("RGBA")
    if k > 1: o = o.resize((int(o.width / k), int(o.height / k)), Image.LANCZOS)
    else: a = a.resize((int(a.width * k), int(a.height * k)), Image.LANCZOS)
    a, o = a.crop(a.getchannel("A").getbbox()), o.crop(o.getchannel("A").getbbox())
    peq, gra = (a, o) if a.height < o.height else (o, a)
    s = min((W - 160) / (peq.width + gra.width), (H - 260) / gra.height); peq = peq.resize((int(peq.width * s), int(peq.height * s)), Image.LANCZOS)
    gra = gra.resize((int(gra.width * s), int(gra.height * s)), Image.LANCZOS)
    im = fundo(W, H).convert("RGBA"); base = H - 170; x = (W - peq.width - gra.width - 80) // 2
    im.alpha_composite(peq, (x, base - peq.height)); im.alpha_composite(gra, (x + peq.width + 80, base - gra.height))
    dr = ImageDraw.Draw(im); dr.line((60, base + 4, W - 60, base + 4), fill=CINZA, width=2)
    j1 = json.load(open(f"{OUTRA}/iso.json")) if MAQ == "200" else ja; j2 = ja if MAQ == "200" else json.load(open(f"{OUTRA}/iso.json"))
    for (xc, jj, nm) in ((x + peq.width / 2, j1, "CoreXY 100³"), (x + peq.width + 80 + gra.width / 2, j2, "CoreXY 200³")):
        d = [round(jj["hi"][i] - jj["lo"][i]) for i in range(3)]; ar = int(jj["area"])
        f = fonte(40, True); dr.text((xc - dr.textlength(nm, font=f) / 2, base + 24), nm, font=f, fill="black")
        for n, t in enumerate((f"{d[0]} x {d[1]} x {d[2]} mm (externo)", f"impressão {ar} x {ar} x {ar} mm")):
            f = fonte(26); dr.text((xc - dr.textlength(t, font=f) / 2, base + 76 + n * 34), t, font=f, fill=CINZA if n == 0 else VOL)
    return im
FOL = ["frente", "lado", "topo", "iso"] + (["comp"] if OUTRA else [])
os.makedirs(DST, exist_ok=True); pags = []
for i, v in enumerate(FOL, 1):
    sh = Image.new("RGB", (SW, SH), "white"); dr = ImageDraw.Draw(sh)
    sh.paste((comparativo() if v == "comp" else vista(v)).convert("RGB"), (M, M)); dr.rectangle((M, M, M + W, M + H), outline="black", width=2)
    x = 2 * M + W; xr = SW - M; tit, txt = TXT[v]
    dr.rectangle((x, M, x + 150, M + 150), fill=AZUL)
    f = fonte(80, True); n = f"{i:02d}"; dr.text((x + 75 - dr.textlength(n, font=f) / 2, M + 18), n, font=f, fill="white")
    f = fonte(20); s = f"de {len(FOL)}"; dr.text((x + 75 - dr.textlength(s, font=f) / 2, M + 112), s, font=f, fill="white")
    dr.text((x + 180, M + 22), "FICHA TÉCNICA", font=fonte(24, True), fill=AZUL); dr.text((x + 180, M + 58), tit, font=fonte(46, True), fill="black")
    y = M + 190; f = fonte(28)
    for l in quebra(dr, txt, f, CW): dr.text((x, y), l, font=f, fill=CINZA); y += 39
    y += 26; dr.text((x, y), "LEGENDA", font=fonte(20, True), fill=AZUL); y += 34
    for cor, t, tra in (("black", "medida externa da máquina", 0), (VOL, "volume / área de impressão", 1)) + ((((90, 95, 102), "vidro da mesa", 1),) if v == "topo" else ()):
        if tra: tracejado(dr, [(x, y + 15), (x + 60, y + 15)], cor, 4, 14, 8)
        else: dr.line((x, y + 15, x + 60, y + 15), fill=cor, width=3)
        dr.text((x + 80, y), t, font=fonte(25), fill="black"); y += 40
    y += 22; dr.text((x, y), "ESPECIFICAÇÕES", font=fonte(20, True), fill=AZUL); y += 34
    for n, (a, b) in enumerate(ESP):
        if n % 2 == 0: dr.rectangle((x, y - 5, xr, y + 40), fill=(238, 242, 246))
        dr.text((x + 10, y), a, font=fonte(25, True), fill="black"); dr.text((x + 345, y), b, font=fonte(25), fill="black"); y += 45
    yc = SH - M - 200; dr.rectangle((x, yc, xr, SH - M), outline="black", width=2)       # carimbo
    for yy in (yc + 66, yc + 116, yc + 160): dr.line((x, yy, xr, yy), fill="black", width=1)
    dr.line((x + 410, yc + 116, x + 410, SH - M), fill="black", width=1)
    dr.text((x + 18, yc + 12), f"MULBOT COREXY {MAQ}³", font=fonte(36, True), fill="black")
    dr.text((x + 18, yc + 78), "Ficha técnica com vistas cotadas", font=fonte(22), fill="black")
    dr.text((x + 18, yc + 126), "Unidade: mm", font=fonte(20), fill=CINZA); dr.text((x + 428, yc + 126), "Vista ortográfica, sem escala", font=fonte(20), fill=CINZA)
    dr.text((x + 18, yc + 168), f"Folha {i:02d}/{len(FOL)}", font=fonte(22, True), fill="black")
    dr.text((x + 428, yc + 168), f"{datetime.date.today():%d/%m/%Y}", font=fonte(22, True), fill="black")
    sh.save(f"{DST}/{i:02d} - {tit.replace('³', '')}.png"); pags.append(sh)
pags[0].save(f"{DST}/Mulbot CoreXY {MAQ} - ficha tecnica.pdf", save_all=True, append_images=pags[1:], resolution=150)
print("folhas", len(pags))
