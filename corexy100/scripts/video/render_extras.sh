#!/bin/bash
# Render das cenas extras (Benchy 8x, peca da 200 impressa na 100, 100 x 200 lado a lado) em blocos de 120 quadros
# (resumivel: quadro pronto e pulado), depois som + legendas + MP4. Uso: render_extras.sh [cycles|previa]
#   variaveis: CXY_DIR (raiz da 100), CXY_200 (_leve.blend da 200, padrao $CXY_DIR/../final/corexy_montagem_leve.blend),
#              BLENDER (executavel), CYCLES_DEVICE=OPTIX|CUDA|HIP|ONEAPI|METAL (GPU; padrao CPU)
CX=${CXY_DIR:-$(cd "$(dirname "$0")/../.." && pwd)}; export CXY_DIR=$CX; MODO=${1:-cycles}
export CXY_200=${CXY_200:-$CX/../final/corexy_montagem_leve.blend} CXY_LINHA=$CX/out/anim/linha_extras.json
Q=$CX/out/anim/quadros_extras_$MODO; PR=$CX/out/anim/progresso_extras.txt; LOG=$CX/out/anim/render_extras_$MODO.log
BL=${BLENDER:-$HOME/.local/opt/blender-4.2.3-linux-x64/blender}; [ -x "$BL" ] || BL=blender
[ -d "$HOME/.local/opt/blibs/root/usr/lib/x86_64-linux-gnu" ] && export LD_LIBRARY_PATH=$HOME/.local/opt/blibs/root/usr/lib/x86_64-linux-gnu
BLEND=$CX/final/corexy_montagem_leve.blend
mkdir -p $Q; cd $CX
for p in benchy:3DBenchy peca200:peca200_baseFrente_D_parte1; do        # caminho do bico (fatiador do video)
  [ -s benchy/${p%%:*}_caminho.npz ] || python3 scripts/video/fatia.py benchy/${p#*:}.stl benchy/${p%%:*}_caminho.npz >> $LOG 2>&1 \
    || { echo "ERRO fatia.py ${p%%:*}" > $PR; exit 1; }
done
"$BL" -b $BLEND -P scripts/video/extras.py -- info $Q >> $LOG 2>&1 || { echo "ERRO linha do tempo (extras info)" > $PR; exit 1; }
TOT=$(python3 -c "import json;print(json.load(open('$CXY_LINHA'))['fim'])")
for ((a=1; a<=TOT; a+=120)); do
  b=$((a+119)); [ $b -gt $TOT ] && b=$TOT
  [ -s $Q/f$(printf %04d $b).png ] && [ $(find $Q -name 'f*.png' -size +0 | wc -l) -ge $b ] && continue
  ( while true; do n=$(find $Q -name 'f*.png' -size +0 | wc -l); echo "$n $TOT Extras CoreXY: quadro $n de $TOT" > $PR; sleep 20; done ) & W=$!
  "$BL" -b $BLEND -P scripts/video/extras.py -- $MODO $Q $a $b >> $LOG 2>&1
  kill $W 2>/dev/null
  find $Q -name 'f*.png' -size 0 -delete
done
n=$(find $Q -name 'f*.png' -size +0 | wc -l)
[ $n -lt $TOT ] && { echo "ERRO render parou em $n de $TOT quadros (ver $LOG)" > $PR; exit 1; }
echo "$TOT $TOT Gerando som e montando o MP4" > $PR
python3 scripts/video/som.py $CX/out/anim/som_extras.wav >> $LOG 2>&1 || { echo "ERRO som.py" > $PR; exit 1; }
mkdir -p $CX/final/video; SAI=$CX/final/video/corexy_extras_$MODO.mp4
python3 scripts/video/monta.py $Q $SAI $CX/out/anim/som_extras.wav >> $LOG 2>&1 || { echo "ERRO monta.py" > $PR; exit 1; }
echo "FIM Extras prontos: $SAI" > $PR
