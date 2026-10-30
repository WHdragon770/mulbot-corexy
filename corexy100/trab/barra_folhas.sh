#!/bin/bash
# barra das folhas CXY: conta os PNG novos ate o gerador (PID $1) terminar
cd ~/corexy100; P=trab/prog_folhas.txt
while kill -0 "$1" 2>/dev/null; do
  n=$(find final/desenhos -name 'CXY-*.png' -newer trab/.marca_folhas | wc -l)
  u=$(ls -t final/desenhos/CXY-*.png | head -1 | xargs -d '\n' basename | cut -c1-6)
  echo "$n 12 Folhas de montagem CoreXY 100: $u" > $P; sleep 15
done
if [ "$(find final/desenhos -name '*.pdf' -newer trab/.marca_folhas | wc -l)" -gt 0 ]; then echo "FIM Folhas CXY da 100 prontas" > $P; else echo "ERRO Folhas CXY da 100: gerador parou sem PDF" > $P; fi
