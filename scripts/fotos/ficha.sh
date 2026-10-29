#!/bin/bash
# Ficha tecnica das 2 maquinas: 4 vistas Cycles cada (1 Blender por vista) + pranchas cotadas + PDF, copia pro Windows
CX=$HOME/corexy; O=$CX/trab/ficha; PR=$O/progresso.txt; LOG=$O/render.log
BL=$HOME/.local/opt/blender-4.2.3-linux-x64/blender; export LD_LIBRARY_PATH=$HOME/.local/opt/blibs/root/usr/lib/x86_64-linux-gnu
DOC="/mnt/c/Users/lucas/Documents/Projetos 3D/CoreXY"; n=0; : > $LOG
for m in 200 100; do
  B=$CX/final/corexy_montagem_leve.blend; [ $m = 100 ] && B=$HOME/corexy100/final/corexy_montagem_leve.blend; mkdir -p $O/r$m
  for v in frente lado topo iso; do
    echo "$n 8 Ficha tecnica: render $m - $v" > $PR
    "$BL" -b $B -P $CX/scripts/fotos/ficha_render.py -- $v $O/r$m/$v.png $m >> $LOG 2>&1
    [ -s $O/r$m/$v.png ] || { echo "ERRO Ficha tecnica: render $m $v falhou (trab/ficha/render.log)" > $PR; exit 1; }
    n=$((n+1))
  done
done
echo "8 8 Ficha tecnica: montando as folhas" > $PR
for m in 200 100; do
  o=100; [ $m = 100 ] && o=200
  rm -rf $O/f$m; python3 $CX/scripts/fotos/ficha_monta.py $m $O/r$m $O/f$m $O/r$o >> $LOG 2>&1 || { echo "ERRO Ficha tecnica: montagem $m" > $PR; exit 1; }
  D="$DOC/CoreXY $m/08 Ficha tecnica"; rm -rf "$D"; mkdir -p "$D"; cp $O/f$m/* "$D/"
done
echo "FIM Ficha tecnica pronta: CoreXY 100 e 200\\08 Ficha tecnica" > $PR
