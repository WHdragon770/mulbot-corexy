# junta os renders num painel com titulos e notas
from PIL import Image, ImageDraw, ImageFont
F = "/usr/share/fonts/truetype/dejavu/DejaVuSans"
ft, fn, fh = ImageFont.truetype(F + "-Bold.ttf", 30), ImageFont.truetype(F + ".ttf", 20), ImageFont.truetype(F + "-Bold.ttf", 40)
P = [("1_montado", "1. Montado (frente)", ["Trilho em V faz parte do poste: 1 peça só", "Parafusos M5 = roldanas fixas", "Sextavado amarelo = bucha excêntrica (aperto)"]),
     ("3_explodido", "2. Como monta", ["Roldana impressa + rolamento 625 (5x16x5)", "Espaçador, placa, bucha e 3 parafusos M5", "Porca nylon atrás de cada roldana"]),
     ("4_corte_topo", "3. Corte visto de cima", ["V do trilho encaixa no canal da roldana", "Contato só nos flancos a 45°, folga na ponta", "Girar a bucha empurra a roldana direita (±0,75 mm)"]),
     ("5_sem_placa", "4. Sem a placa: 3 roldanas abraçando o V", ["Sem esferas, sem tampas, sem pré-carga chata", "Ajuste: solta o M5, gira o sextavado, aperta", "Orelha da placa recebe o braço da mesa"])]
W, H, TOP = 1100, 1000, 70
img = Image.new("RGB", (2 * W, 2 * (H + 150) + TOP), (13, 17, 22)); d = ImageDraw.Draw(img)
d.text((30, 14), "Guia em V impressa com 3 roldanas: exemplo pro eixo Z da CoreXY", font=fh, fill=(240, 240, 240))
for i, (f, tit, notas) in enumerate(P):
    x, y = (i % 2) * W, TOP + (i // 2) * (H + 150)
    img.paste(Image.open(f"render/{f}.png"), (x, y))
    d.text((x + 24, y + 18), tit, font=ft, fill=(255, 255, 255))
    for k, n in enumerate(notas): d.text((x + 30, y + H + 14 + k * 32), "• " + n, font=fn, fill=(210, 215, 222))
img.save("render/guia_v_painel.png"); img.resize((img.width // 2, img.height // 2)).save("render/guia_v_painel_pequeno.png")
