#!/bin/bash
# Fila do video da 200: espera o render da 100 acabar (PC nao aguenta 2), refaz poses (esteira) + cabos + custo
# e gera as IMAGENS de conferencia (1 quadro por cena, workbench) + folha unica. Para ai: Cycles so depois do OK.
CX=$HOME/corexy; PR=$CX/out/anim/progresso_cycles.txt; P100=$HOME/corexy100/out/anim/progresso_cycles.txt; LOG=$CX/out/anim/fila_200.log
BL=$HOME/.local/opt/blender-4.2.3-linux-x64/blender; export LD_LIBRARY_PATH=$HOME/.local/opt/blibs/root/usr/lib/x86_64-linux-gnu CXY_DIR=$CX
WIN="/mnt/c/Users/lucas/Documents/Projetos 3D/CoreXY/CoreXY 200/04 Video"
cd $CX
: # sem espera (27/10: ele fechou tudo, roda junto com a 100 em nice)
if [ ! -s out/anim/poses/poses.json ] || [ out/anim/poses/poses.json -ot out/cxy.json ]; then
  ( while sleep 30; do n=$(grep -o "^[0-9]*" out/anim/progresso_poses.txt 2>/dev/null); echo "${n:-0} 60 Imagens 200: poses da esteira ${n:-0}/60" > $PR; done ) & W=$!
  python3 scripts/video/poses.py 60 >> $LOG 2>&1; r=$?; kill $W
  [ $r = 0 ] || { echo "ERRO Imagens 200: poses.py falhou (ver out/anim/fila_200.log)" > $PR; exit 1; }
fi
echo "0 1 Imagens 200: cabos da esteira" > $PR
python3 scripts/video/cabos_caminhos.py >> $LOG 2>&1 || { echo "ERRO Imagens 200: cabos_caminhos.py falhou" > $PR; exit 1; }
echo "0 1 Imagens 200: custo dos quadros" > $PR
"$BL" -b final/corexy_montagem_leve.blend -P scripts/video/anima2.py -P scripts/video/custo.py -- info /tmp/cxy_info >> $LOG 2>&1 || { echo "ERRO Imagens 200: custo.py falhou" > $PR; exit 1; }
echo "0 16 Imagens 200: renderizando 16 quadros de conferencia" > $PR
rm -rf out/anim/folha_200; mkdir -p out/anim/folha_200
QUADROS="150,450,700,900,1030,1170,1290,1400,1520,1640,1800,2000,2100,2190,2300,2500" \
  "$BL" -b final/corexy_montagem_leve.blend -P scripts/video/anima2.py -- folha out/anim/folha_200 >> $LOG 2>&1
python3 - <<'PY' >> $LOG 2>&1
import glob; from PIL import Image, ImageDraw
fs = sorted(glob.glob("out/anim/folha_200/b*.png")); W, H = 640, 360
F = Image.new("RGB", (4 * W, ((len(fs) + 3) // 4) * H), "white")
for i, f in enumerate(fs):
    im = Image.open(f).convert("RGB").resize((W, H)); ImageDraw.Draw(im).text((8, 8), f[-8:-4], fill="red"); F.paste(im, ((i % 4) * W, (i // 4) * H))
F.save("out/anim/folha_200/folha.jpg", quality=85)
PY
n=$(ls out/anim/folha_200/b*.png 2>/dev/null | wc -l)
[ -d "$(dirname "$WIN")" ] && mkdir -p "$WIN" && cp out/anim/folha_200/folha.jpg "$WIN/PREVIA - imagens de conferencia.jpg"
echo "FIM Imagens 200 prontas ($n de 16): 04 Video\\PREVIA - imagens de conferencia.jpg. Render Cycles aguarda o OK" > $PR
