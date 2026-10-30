#!/bin/bash
# Prepara o video pra versao atual: poses, cabos da cena, linha do tempo/custo e previa workbench
S=/tmp/claude-1000/-home-lucas/a7d1791e-1798-4349-a13b-8bb88e69054d/scratchpad; P=$S/prog_video.txt; CX=/home/lucas/corexy; L=$CX/trab/video_prep.log
cd $CX; echo 1000 > /proc/self/oom_score_adj; : > $L
falha() { echo "ERRO $1 (ver trab/video_prep.log)" >> $P; exit 1; }
echo "0 100 poses da maquina funcionando (60)" >> $P
mkdir -p out/anim/poses; rm -f out/anim/poses/*
( while sleep 15; do [ -s out/anim/progresso_poses.txt ] && read a b r < out/anim/progresso_poses.txt && [ "$a" -eq "$a" ] 2>/dev/null && echo "$((a*30/b)) 100 $r" >> $P; done ) & W=$!
CABOS=0 python3 scripts/video/poses.py 60 >> $L 2>&1; ok=$?; kill $W; [ $ok = 0 ] || falha "poses"
echo "31 100 montagem na pose padrao (com cabos)" >> $P; ESFERAS=0 python3 scripts/cxy.py >> $L 2>&1 || falha "cxy"
echo "33 100 cabos da cena de passagem" >> $P; python3 scripts/video/cabos_caminhos.py >> $L 2>&1 || falha "cabos_caminhos"
echo "36 100 linha do tempo e custo por quadro" >> $P
LD_LIBRARY_PATH=~/.local/opt/blibs/root/usr/lib/x86_64-linux-gnu ~/.local/opt/blender-4.2.3-linux-x64/blender -b final/corexy_montagem_leve.blend \
  -P scripts/video/anima2.py -P scripts/video/custo.py -- info $S/info >> $L 2>&1 || falha "anima2 info/custo"
rm -rf out/anim/quadros_previa out/anim/progresso_previa.txt
( while sleep 20; do [ -s out/anim/progresso_previa.txt ] && read a b r < out/anim/progresso_previa.txt && [ "$a" -eq "$a" ] 2>/dev/null && echo "$((38+a*62/b)) 100 previa: $r" >> $P; done ) & W=$!
bash scripts/video/render_noite.sh "" previa >> $L 2>&1; kill $W
grep -q '^FIM' out/anim/progresso_previa.txt || falha "previa: $(cat out/anim/progresso_previa.txt)"
echo "FIM Video pronto pra renderizar; previa nova em 01 Montagem 3D\\Video" >> $P
