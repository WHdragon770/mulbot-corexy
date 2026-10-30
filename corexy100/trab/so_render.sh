#!/bin/bash
P=/home/lucas/corexy100/trab/prog_img.txt; L=/home/lucas/corexy100/trab/imagens.log; CX=/home/lucas/corexy100
BL=~/.local/opt/blender-4.2.3-linux-x64/blender; export LD_LIBRARY_PATH=~/.local/opt/blibs/root/usr/lib/x86_64-linux-gnu
cd $CX; echo 1000 > /proc/self/oom_score_adj; : > $L; : > $P; N=8; i=0
for v in heroi heroi2 tras lado topo carro_hotend carro_rodas mesa; do
  echo "$i $N render $v" >> $P; i=$((i+1))
  $BL -b final/corexy_montagem_leve.blend -P scripts/render_final.py -- final/render CYCLES 64 1200 final/limites.json $v >> $L 2>&1
  [ -s final/render/$v.png ] || { echo "ERRO render $v (ver trab/imagens.log)" >> $P; exit 1; }
done
D="/mnt/c/Users/lucas/Documents/Projetos 3D/CoreXY/CoreXY 100/01 Montagem 3D"
cp final/render/*.png "$D"/ && rm -f "$D/CoreXY100_iso.png" && echo "FIM CoreXY 100: 8 imagens finais em Documentos" >> $P
