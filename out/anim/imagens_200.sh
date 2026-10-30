#!/bin/bash
# Imagens de conferencia da 200 depois que o render da 100 acabar (poses/cabos ja feitos 27/10 20h)
CX=$HOME/corexy; PR=$CX/out/anim/progresso_cycles.txt; P100=$HOME/corexy100/out/anim/progresso_cycles.txt; LOG=$CX/out/anim/imagens_200.log
BL=$HOME/.local/opt/blender-4.2.3-linux-x64/blender; export LD_LIBRARY_PATH=$HOME/.local/opt/blibs/root/usr/lib/x86_64-linux-gnu CXY_DIR=$CX
WIN="/mnt/c/Users/lucas/Documents/Projetos 3D/CoreXY/CoreXY 200/04 Video"
cd $CX; sleep 120
until grep -q "^FIM\|^ERRO" $P100; do echo "0 1 Imagens 200: espera a 100 terminar ($(cut -d' ' -f1 $P100)/2562)" > $PR; sleep 60; done
echo "0 16 Imagens 200: custo dos quadros" > $PR
"$BL" -b final/corexy_montagem_leve.blend -P scripts/video/anima2.py -P scripts/video/custo.py -- info /tmp/cxy_info > $LOG 2>&1
grep -q Traceback $LOG && { echo "ERRO Imagens 200: anima2 info falhou (ver out/anim/imagens_200.log)" > $PR; exit 1; }
rm -rf out/anim/folha_200; mkdir -p out/anim/folha_200
( while sleep 20; do echo "$(ls out/anim/folha_200 | wc -l) 16 Imagens 200: renderizando quadros de conferencia" > $PR; done ) & W=$!
QUADROS="150,450,700,900,1030,1170,1290,1400,1520,1640,1800,2000,2100,2190,2300,2500" \
  "$BL" -b final/corexy_montagem_leve.blend -P scripts/video/anima2.py -- folha out/anim/folha_200 >> $LOG 2>&1
kill $W
python3 - >> $LOG 2>&1 <<'PY'
import glob; from PIL import Image, ImageDraw
fs = sorted(glob.glob("out/anim/folha_200/b*.png")); W, H = 640, 360
F = Image.new("RGB", (4 * W, ((len(fs) + 3) // 4) * H), "white")
for i, f in enumerate(fs):
    im = Image.open(f).convert("RGB").resize((W, H)); ImageDraw.Draw(im).text((8, 8), f[-8:-4], fill="red"); F.paste(im, ((i % 4) * W, (i // 4) * H))
F.save("out/anim/folha_200/folha.jpg", quality=85)
PY
n=$(ls out/anim/folha_200/b*.png 2>/dev/null | wc -l)
[ $n -gt 0 ] && mkdir -p "$WIN" && cp out/anim/folha_200/folha.jpg "$WIN/PREVIA - imagens de conferencia.jpg"
[ $n -eq 16 ] && echo "FIM Imagens 200 prontas: CoreXY 200\\04 Video\\PREVIA - imagens de conferencia.jpg" > $PR || echo "ERRO Imagens 200: so $n de 16 (ver out/anim/imagens_200.log)" > $PR
