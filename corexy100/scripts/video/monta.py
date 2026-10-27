# Junta os quadros renderizados + legendas (desenhadas aqui, com fade) + som.wav num MP4 (H.264 + AAC).
# python3 monta.py quadros_dir saida.mp4 [som.wav]
import sys, os, json, subprocess, numpy as np, imageio_ffmpeg
CX = os.environ.get("CXY_DIR") or os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))   # raiz do projeto
from PIL import Image, ImageDraw, ImageFont
Q, OUT = sys.argv[1], sys.argv[2]
SOM = sys.argv[3] if len(sys.argv) > 3 else f"{CX}/out/anim/som.wav"
L = json.load(open(f"{CX}/out/anim/linha.json")); FPS = L["fps"]
F = "/usr/share/fonts/truetype/dejavu/DejaVuSans"
fs = sorted(int(n[1:5]) for n in os.listdir(Q) if n.startswith("f") and n.endswith(".png") and os.path.getsize(f"{Q}/{n}") > 0)
ult = 0
while ult + 1 in fs: ult += 1                     # so a parte continua ja renderizada
if not ult: sys.exit("sem quadros")
W, H = Image.open(f"{Q}/f0001.png").size; k = H / 720
fT, fS, fG, fG2 = (ImageFont.truetype(F + "-Bold.ttf", int(42 * k)), ImageFont.truetype(F + ".ttf", int(26 * k)),
                   ImageFont.truetype(F + "-Bold.ttf", int(86 * k)), ImageFont.truetype(F + ".ttf", int(34 * k)))
def legenda(im, f):
    for i, (a, b, t, s) in enumerate(L["legendas"]):
        if not a <= f <= b: continue
        al = min(1, (f - a) / 8, (b - f) / 8)
        cam = Image.new("RGBA", im.size, (0, 0, 0, 0)); d = ImageDraw.Draw(cam)
        if i in (0, len(L["legendas"]) - 1):         # abertura / final: titulo grande no centro
            tw = d.textlength(t, font=fG); sw = d.textlength(s, font=fG2)
            d.rectangle((0, H * 0.36, W, H * 0.64), fill=(15, 20, 28, int(150 * al)))
            d.text(((W - tw) / 2, H * 0.39), t, font=fG, fill=(255, 255, 255, int(255 * al)))
            d.text(((W - sw) / 2, H * 0.53), s, font=fG2, fill=(230, 235, 240, int(255 * al)))
        else:                                       # faixa embaixo a esquerda
            tw = max(d.textlength(t, font=fT), d.textlength(s, font=fS) if s else 0)
            x0, y0 = 40 * k, H - (150 if s else 110) * k
            d.rectangle((0, y0, x0 + tw + 40 * k, y0 + (118 if s else 78) * k), fill=(15, 20, 28, int(170 * al)))
            d.rectangle((0, y0, 10 * k, y0 + (118 if s else 78) * k), fill=(200, 40, 30, int(255 * al)))
            d.text((x0, y0 + 14 * k), t, font=fT, fill=(255, 255, 255, int(255 * al)))
            if s: d.text((x0, y0 + 68 * k), s, font=fS, fill=(220, 225, 232, int(255 * al)))
        im = Image.alpha_composite(im, cam)
    return im
ff = imageio_ffmpeg.get_ffmpeg_exe()
cmd = [ff, "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
       "-i", SOM, "-c:v", "libx264", "-preset", "slow", "-crf", "18", "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "192k",
       "-shortest", "-movflags", "+faststart", OUT]
p = subprocess.Popen(cmd, stdin=subprocess.PIPE)
for f in range(1, ult + 1):
    im = legenda(Image.open(f"{Q}/f{f:04d}.png").convert("RGBA"), f)
    p.stdin.write(np.asarray(im.convert("RGB")).tobytes())
p.stdin.close(); p.wait()
print("video", OUT, ult, "quadros", f"{ult / FPS:.1f} s", "de", L["fim"])
