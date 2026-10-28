#!/bin/bash
# Fila da tarde (28/10): placas da 100 -> manual completo da 100 -> as 18:00 volta o render Cycles da 200
T=/home/lucas/corexy100/trab; PM=$T/prog_manual.txt; R="/mnt/c/Users/lucas/Documents/Projetos 3D/CoreXY/CoreXY 100"
echo 1000 > /proc/self/oom_score_adj
$T/placas100.sh
echo "0 1 gerando o PDF (capa, guias, lista, folhas, detalhes)" > $PM
( cd /home/lucas/corexy100/scripts/desenhos && python3 completo.py "$R" $T/manual_completo.pdf ) > $T/manual.log 2>&1 \
  && cp $T/manual_completo.pdf "$R/03 Desenhos de montagem/manual completo.pdf" \
  && echo "FIM Manual completo da CoreXY 100: $(grep -o 'PDF [0-9]* páginas' $T/manual.log) em 03 Desenhos de montagem" >> $PM \
  || echo "ERRO manual completo (ver corexy100/trab/manual.log)" >> $PM
while [ $(date +%H%M) -lt 1800 ]; do sleep 60; done
cd /home/lucas/corexy && exec bash scripts/video/render_noite.sh "" cycles
