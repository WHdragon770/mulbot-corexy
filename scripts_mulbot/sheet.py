import sys, glob, os
from PIL import Image, ImageDraw, ImageFont
import trimesh
src, out = sys.argv[1], sys.argv[2]
os.makedirs(out, exist_ok=True)
names = sorted({os.path.basename(f).split("__")[0] for f in glob.glob(src+"/*.png")})
V = ["iso","top","front","right","bot","back"]
try: font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 22)
except: font = ImageFont.load_default()
for n in names:
    W = 420
    im = Image.new("RGB", (W*3, W*2+40), "white")
    for i, v in enumerate(V):
        t = Image.open(f"{src}/{n}__{v}.png").convert("RGB")
        im.paste(t, ((i%3)*W, 40+(i//3)*W))
        ImageDraw.Draw(im).text(((i%3)*W+5, 45+(i//3)*W), v, fill="black", font=font)
    m = trimesh.load(f"/home/lucas/mulbot/repo/MODELS/{n}.stl"); e = m.extents
    ImageDraw.Draw(im).text((5,5), f"{n}   X{e[0]:.1f} Y{e[1]:.1f} Z{e[2]:.1f}", fill="black", font=font)
    im.save(f"{out}/{n}.png")
