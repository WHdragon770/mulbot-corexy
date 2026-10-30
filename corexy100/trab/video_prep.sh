#!/bin/bash
# CoreXY 100: poses + cabos do video e previa Workbench (pra conferir camera antes das ~12 h de Cycles)
P=/home/lucas/corexy100/out/anim/progresso_previa.txt; CX=/home/lucas/corexy100; L=$CX/trab/video_prep.log
cd $CX; echo 1000 > /proc/self/oom_score_adj; mkdir -p out/anim/poses out/anim/cabos; : > $L
echo "0 3 poses da maquina funcionando (60)" > $P
python3 scripts/video/poses.py 60 >> $L 2>&1 || { echo "ERRO poses.py" > $P; exit 1; }
echo "1 3 caminho dos cabos" > $P
python3 scripts/video/cabos_caminhos.py >> $L 2>&1 || { echo "ERRO cabos_caminhos.py" > $P; exit 1; }
echo "2 3 previa Workbench" > $P
CXY_DIR=$CX bash scripts/video/render_noite.sh "" previa
