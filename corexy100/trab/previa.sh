#!/bin/bash
# reexporta blend/leve (grupos novos) e roda so a previa Workbench (poses e cabos ja prontos)
P=/home/lucas/corexy100/out/anim/progresso_previa.txt; CX=/home/lucas/corexy100; L=$CX/trab/video_prep.log
cd $CX; echo 1000 > /proc/self/oom_score_adj
echo "0 2 poses de novo (com cabos da esteira)" > $P; python3 scripts/video/poses.py 60 >> $L 2>&1 || { echo "ERRO poses.py" > $P; exit 1; }
CXY_DIR=$CX bash scripts/video/render_noite.sh "" previa
