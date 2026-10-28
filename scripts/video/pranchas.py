# Pranchas de conferencia da 200: cada quadro (anima2.py folha, CXY_RES=1920x1080) vira uma prancha com numero,
# titulo, texto descritivo e carimbo. Uso: python3 pranchas.py <pasta dos b####.png> <saida>  -> NN - titulo.png + PDF
import sys, os, datetime
from PIL import Image, ImageDraw, ImageFont
SRC, DST = sys.argv[1], sys.argv[2]
F = "/usr/share/fonts/truetype/dejavu/DejaVuSans"
def fonte(t, b=False): return ImageFont.truetype(F + ("-Bold" if b else "") + ".ttf", t)
AZUL, CINZA = "#1a5f8a", "#5a5f66"
P = [  # quadro, etapa, titulo, descricao
 (192, "Montagem 1/9", "Quadro", "Quadro em perfis impressos ocos, unidos por cantoneiras e parafusos também impressos. Os canais internos dos perfis levam os cabos dos motores e sensores até a caixa da eletrônica, sem fio aparente por fora."),
 (288, "Montagem 2/9", "Eixo Z e mesa", "Mesa sustentada por 2 fusos verticais, cada um com seu motor de passo. Os dois motores Z trabalham juntos e levantam a mesa por igual dos dois lados."),
 (384, "Montagem 3/9", "Torres e motores A/B", "Torres traseiras com os motores A e B do CoreXY. Os motores ficam parados no quadro: o pórtico e o carro andam leves, sem carregar o peso deles."),
 (480, "Montagem 4/9", "Vigas Y com guia em V", "Vigas laterais com trilho em V impresso. O pórtico corre sobre roldanas V de resina, sem trilho linear de aço nem rolamento comprado."),
 (576, "Montagem 5/9", "Pórtico", "Pórtico do eixo X apoiado nas duas vigas Y. É nele que corre o carro do hotend, guiado pelas mesmas roldanas em V."),
 (672, "Montagem 6/9", "Carro X e hotend", "Carro X com hotend, torre das correias e fim de curso reunidos numa peça só, o que reduz o número de peças e as folgas entre elas."),
 (768, "Montagem 7/9", "Polias e correias CoreXY", "2 correias de 1418 mm em circuito CoreXY. Quando os motores A e B giram juntos o carro anda em um eixo; quando giram em sentidos opostos, anda no outro."),
 (864, "Montagem 8/9", "Extrusora direta", "Extrusora montada direto sobre o carro. O caminho do filamento até o bico fica curto, o que melhora a retração e o controle do fluxo."),
 (960, "Montagem 9/9", "Eletrônica, esteira e display", "Caixa traseira com RAMPS, Arduino Mega e fonte 12 V 150 W. Os cabos do carro descem pela esteira porta-cabos; o display de controle fica na frente."),
 (1030, "Visão geral", "Impressora montada", "Mulbot CoreXY 200³ completa. Área útil de impressão de 200 x 200 x 200 mm, com quadro, guias, fusos e parafusos impressos."),
 (1170, "Detalhe", "Guia em V impressa", "Roldana de resina com 10 roletes impressos junto, numa peça só. Ela corre no trilho em V da viga e dispensa rolamento comprado."),
 (1290, "Detalhe", "Carro X", "Hotend, extrusora direta, torre das correias e fim de curso no mesmo carro. As pontas das 2 correias prendem na torre do carro."),
 (1400, "Detalhe", "Presilha do vidro", "Presilha giratória que prende o vidro na mesa: meia volta solta, meia volta trava. A troca do vidro é feita sem ferramenta."),
 (1520, "Detalhe", "Sistema CoreXY", "2 correias de 1418 mm e os motores A e B parados no quadro. X e Y saem da soma e da diferença do giro dos dois motores."),
 (1640, "Detalhe", "Eletrônica", "RAMPS 1.4, Arduino Mega e fonte na caixa de trás, com tomada IEC com chave. Os cabos chegam por dentro do quadro."),
 (1800, "Cabeamento", "Passagem de cabos", "Quadro mostrado translúcido: 9 cabos passam por dentro dos perfis ocos, de cada motor e sensor até a caixa da RAMPS."),
 (2000, "Funcionamento", "Impressora funcionando", "Movimento real da máquina: X e Y pela soma das 2 correias, Z pelos 2 fusos subindo a mesa por igual."),
 (2190, "Vista explodida", "Vista explodida", "Todas as peças afastadas na direção de montagem, pra conferir o que vai em cada conjunto e a ordem de encaixe."),
 (2300, "Detalhe explodido", "Pórtico explodido", "Close da vista explodida no pórtico: roldanas V, polias loucas com gaiola de esferas e fixadores impressos afastados do lugar."),
 (2500, "Visão geral", "Mulbot CoreXY 200³", "Versão final: quadro, guias, fusos e parafusos impressos. Projeto derivado da Mulbot DL1, convertida pra cinemática CoreXY."),
]
W, H, M, BAND = 1920, 1080, 40, 250
SW, SH = W + 2 * M, H + 2 * M + BAND
def quebra(dr, t, f, w):
    ls, l = [], ""
    for p in t.split():
        if dr.textlength((l + " " + p).strip(), font=f) > w: ls.append(l); l = p
        else: l = (l + " " + p).strip()
    return ls + [l]
os.makedirs(DST, exist_ok=True); pags = []
for i, (q, et, tit, txt) in enumerate(P, 1):
    im = Image.new("RGB", (SW, SH), "white"); dr = ImageDraw.Draw(im)
    r = Image.open(f"{SRC}/b{q:04d}.png").convert("RGBA")                 # recorta em 16:9 em volta da maquina (alfa)
    x0, y0_, x1, y1 = r.getchannel("A").point(lambda v: 255 if v > 8 else 0).getbbox(); cx, cy = (x0 + x1) / 2, (y0_ + y1) / 2
    w = max((x1 - x0) * 1.12, (y1 - y0_) * 1.12 * 16 / 9, r.width * 0.5); w = min(w, r.width); h = w * 9 / 16
    cx = min(max(cx, w / 2), r.width - w / 2); cy = min(max(cy, h / 2), r.height - h / 2)
    r = r.crop((int(cx - w / 2), int(cy - h / 2), int(cx + w / 2), int(cy + h / 2))).resize((W, H), Image.LANCZOS)
    fu = Image.new("RGB", (W, H)); fd = ImageDraw.Draw(fu)                # fundo degrade claro de estudio
    for yy in range(H): t = yy / H; fd.line((0, yy, W, yy), fill=tuple(int(a + (b - a) * t) for a, b in zip((246, 247, 249), (214, 219, 225))))
    fu.paste(r, (0, 0), r); im.paste(fu, (M, M))
    dr.rectangle((M, M, M + W, M + H), outline="black", width=2)
    y0 = M + H + 30; yb = SH - M
    dr.rectangle((M, y0, M + 190, yb), fill=AZUL)                       # numero da prancha
    f = fonte(96, True); n = f"{i:02d}"; dr.text((M + 95 - dr.textlength(n, font=f) / 2, y0 + 30), n, font=f, fill="white")
    f = fonte(22); s = f"de {len(P)}"; dr.text((M + 95 - dr.textlength(s, font=f) / 2, y0 + 150), s, font=f, fill="white")
    x = M + 230; CAR = 470; wt = M + W - CAR - 40 - x
    dr.text((x, y0 + 4), et.upper(), font=fonte(24, True), fill=AZUL)
    dr.text((x, y0 + 36), tit, font=fonte(50, True), fill="black")
    f = fonte(27)
    for k, l in enumerate(quebra(dr, txt, f, wt)): dr.text((x, y0 + 106 + k * 36), l, font=f, fill=CINZA)
    xc = M + W - CAR; dr.rectangle((xc, y0, M + W, yb), outline="black", width=2)  # carimbo
    for yy in (y0 + 70, y0 + 125, y0 + 170): dr.line((xc, yy, M + W, yy), fill="black", width=1)
    dr.text((xc + 18, y0 + 14), "MULBOT COREXY 200³", font=fonte(36, True), fill="black")
    dr.text((xc + 18, y0 + 82), "Imagens de conferência da montagem", font=fonte(22), fill="black")
    dr.text((xc + 18, y0 + 135), f"Quadro {q} do vídeo de montagem", font=fonte(20), fill=CINZA)
    dr.text((xc + 18, y0 + 182), f"Prancha {i:02d}/{len(P)}     {datetime.date.today():%d/%m/%Y}", font=fonte(22, True), fill="black")
    nome = f"{i:02d} - {tit.replace('/', '-').replace('³', '')}.png"; im.save(f"{DST}/{nome}"); pags.append(im)
pags[0].save(f"{DST}/Mulbot CoreXY 200 - imagens de conferencia.pdf", save_all=True, append_images=pags[1:], resolution=150)
print("pranchas", len(pags))
