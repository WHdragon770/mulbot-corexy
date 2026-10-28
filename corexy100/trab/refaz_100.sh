#!/bin/bash
# Depois das pranchas da 200: refaz as 12 folhas da 100 (texto 100³) e remonta o MP4 da 100 com a legenda 1044 mm (sem renderizar de novo)
CX=/home/lucas/corexy100; P=$CX/trab/prog_desenhos.txt; L=$CX/trab/desenhos.log
WIN="/mnt/c/Users/lucas/Documents/Projetos 3D/CoreXY/CoreXY 100"
export LD_LIBRARY_PATH=~/.local/opt/blibs/root/usr/lib/x86_64-linux-gnu
cd $CX; until grep -q "^FIM\|^ERRO" ~/corexy/out/anim/prog_pranchas.txt && ! pgrep -x blender >/dev/null; do echo "0 3 Correcao 100: espera as pranchas da 200" > $P; sleep 20; done
echo "1 3 Correcao 100: 12 folhas" > $P; : > $L
rm -rf final/desenhos; python3 scripts/desenhos/folhas.py final/desenhos >> $L 2>&1 || { echo "ERRO Correcao 100: folhas.py (trab/desenhos.log)" > $P; exit 1; }
D="$WIN/03 Desenhos de montagem"; rm -rf "$D"; mkdir -p "$D"; cp final/desenhos/*.png final/desenhos/*.pdf "$D"/
echo "2 3 Correcao 100: remontando o MP4 (legenda 1044 mm)" > $P
sed -i 's/correias de 1418 mm/correias de 1044 mm/' out/anim/linha.json
python3 scripts/video/monta.py out/anim/quadros_cycles final/video/corexy_video_cycles.mp4 >> $L 2>&1 || { echo "ERRO Correcao 100: monta.py" > $P; exit 1; }
cp final/video/corexy_video_cycles.mp4 "$WIN/04 Video/Mulbot CoreXY 100 - video de montagem.mp4"
echo "FIM Correcao 100 pronta: desenhos (100³) e video (correias 1044 mm)" > $P
