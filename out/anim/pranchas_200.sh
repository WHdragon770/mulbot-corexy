#!/bin/bash
# Pranchas de conferencia da 200 (1920x1080 + texto), espera o Blender dos desenhos da 100 acabar
CX=$HOME/corexy; PR=$CX/out/anim/prog_pranchas.txt; LOG=$CX/out/anim/pranchas_200.log; O=$CX/out/anim/pranchas_200
BL=$HOME/.local/opt/blender-4.2.3-linux-x64/blender; export LD_LIBRARY_PATH=$HOME/.local/opt/blibs/root/usr/lib/x86_64-linux-gnu CXY_DIR=$CX
WIN="/mnt/c/Users/lucas/Documents/Projetos 3D/CoreXY/CoreXY 200/04 Video"
cd $CX
until ! pgrep -x blender >/dev/null; do echo "0 20 Pranchas 200: espera o Blender livre" > $PR; sleep 30; done
Q=$(python3 -c "import re;print(','.join(re.findall(r'^ \((\d+),',open('scripts/video/pranchas.py').read(),re.M)))")
( while sleep 10; do echo "$(ls $O/b*.png 2>/dev/null | wc -l) 20 Pranchas 200: renderizando" > $PR; done ) & W=$!
CXY_RES=2880x1620 QUADROS=$Q "$BL" -b final/corexy_montagem_leve.blend -P scripts/video/anima2.py -- folha $O > $LOG 2>&1
kill $W
grep -q Traceback $LOG && { echo "ERRO Pranchas 200: render falhou (out/anim/pranchas_200.log)" > $PR; exit 1; }
python3 scripts/video/pranchas.py $O $O/pranchas >> $LOG 2>&1 || { echo "ERRO Pranchas 200: montagem falhou" > $PR; exit 1; }
D="$WIN/Imagens de conferencia"; rm -rf "$D"; mkdir -p "$D"; cp $O/pranchas/* "$D/"; rm -f "$WIN/PREVIA - imagens de conferencia.jpg"
echo "FIM Pranchas 200 prontas: CoreXY 200\\04 Video\\Imagens de conferencia" > $PR
