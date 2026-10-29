#!/bin/bash
# Render do video da CoreXY em blocos de 120 quadros (1 Blender por bloco; resumivel: quadro pronto e pulado),
# depois som + legendas + MP4. Uso: render_noite.sh [HH:MM de inicio] [cycles|previa]
#   variaveis: CXY_DIR (raiz do projeto, padrao = 2 pastas acima deste script), BLENDER (executavel, padrao blender 4.2.3),
#              CYCLES_DEVICE=OPTIX|CUDA|HIP|ONEAPI|METAL (usa GPU; padrao CPU)
CX=${CXY_DIR:-$(cd "$(dirname "$0")/../.." && pwd)}; export CXY_DIR=$CX; MODO=${2:-cycles}
Q=$CX/out/anim/quadros_$MODO; PR=$CX/out/anim/progresso_$MODO.txt; LOG=$CX/out/anim/render_$MODO.log
BL=${BLENDER:-$HOME/.local/opt/blender-4.2.3-linux-x64/blender}; [ -x "$BL" ] || BL=blender
[ -d "$HOME/.local/opt/blibs/root/usr/lib/x86_64-linux-gnu" ] && export LD_LIBRARY_PATH=$HOME/.local/opt/blibs/root/usr/lib/x86_64-linux-gnu
WIN="/mnt/c/Users/lucas/Documents/Projetos 3D/CoreXY/CoreXY 100"          # copia pro Windows do Aleixo, so se existir
BLEND=$CX/final/corexy_montagem_leve.blend
mkdir -p $Q
if [ -n "$1" ]; then                                   # espera ate a hora marcada
  alvo=$(date -d "$1" +%s); [ $alvo -lt $(date +%s) ] && alvo=$(date -d "tomorrow $1" +%s)
  while [ $(date +%s) -lt $alvo ]; do echo "0 1 Aguardando o horario: comeca as $1" > $PR; sleep 60; done
fi
cd $CX
"$BL" -b $BLEND -P scripts/video/anima2.py -- info $Q > $LOG 2>&1 || { echo "ERRO linha do tempo (anima2 info)" > $PR; exit 1; }
TOT=$(python3 -c "import json;print(json.load(open('$CX/out/anim/linha.json'))['fim'])")
rm -f $PR.eta; python3 scripts/video/estimativa.py $Q --vigiar $PR >> $LOG 2>&1 &     # termino pelo peso de cada quadro
for ((a=1; a<=TOT; a+=120)); do
  b=$((a+119)); [ $b -gt $TOT ] && b=$TOT
  falta=0; for ((i=a; i<=b; i++)); do [ -s $Q/f$(printf %04d $i).png ] || { falta=1; break; }; done
  [ $falta = 0 ] && continue                          # bloco completo (confere quadro a quadro, nao so a contagem)
  ( while true; do                                    # progresso enquanto o bloco roda
      n=$(find $Q/ -name 'f*.png' -size +0 | wc -l)
      eta=""; [ -s $PR.eta ] && eta=" - termina ~$(cat $PR.eta)"
      echo "$n $TOT Video CoreXY: quadro $n de $TOT$eta" > $PR; sleep 20; done ) & W=$!
  "$BL" -b $BLEND -P scripts/video/anima2.py -- $MODO $Q $a $b >> $LOG 2>&1
  kill $W 2>/dev/null
  find $Q/ -name 'f*.png' -size 0 -delete               # placeholder de bloco interrompido
done
n=$(find $Q/ -name 'f*.png' -size +0 | wc -l)
[ $n -lt $TOT ] && { echo "ERRO render parou em $n de $TOT quadros (ver $LOG)" > $PR; exit 1; }
echo "$TOT $TOT Gerando som e montando o MP4" > $PR
python3 scripts/video/som.py >> $LOG 2>&1 || { echo "ERRO som.py" > $PR; exit 1; }
mkdir -p $CX/final/video; SAI=$CX/final/video/corexy_video_$MODO.mp4
python3 scripts/video/monta.py $Q $SAI >> $LOG 2>&1 || { echo "ERRO monta.py" > $PR; exit 1; }
if [ -d "$WIN" ]; then
  mkdir -p "$WIN/04 Video"
  if [ $MODO = cycles ]; then cp $SAI "$WIN/04 Video/Mulbot CoreXY 100 - video de montagem.mp4"
  else cp $SAI "$WIN/04 Video/PREVIA - video de montagem (rascunho rapido).mp4"; fi
fi
echo "FIM Video pronto: $SAI" > $PR
