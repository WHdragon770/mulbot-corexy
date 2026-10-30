#!/bin/bash
# espera o Cycles da 200 terminar e sobe o MP4 no repo (limite do GitHub: 100 MB)
P=/home/lucas/corexy/out/anim/progresso_cycles.txt; V=/home/lucas/corexy/final/video/corexy_video_cycles.mp4; G=/home/lucas/repos/mulbot-corexy
until grep -q "^FIM\|^ERRO" $P; do sleep 60; done
grep -q "^FIM" $P || exit 1
T=$(stat -c %s $V); if [ $T -gt 95000000 ]; then echo "video $((T/1000000)) MB: grande demais pro GitHub, nao subiu" > /home/lucas/corexy/out/anim/video_git.txt; exit 1; fi
mkdir -p $G/entrega/video; cp $V "$G/entrega/video/Mulbot CoreXY 200 - video de montagem.mp4"; cd $G
git add entrega/video && git commit -qm "CoreXY 200: video de montagem renderizado no Cycles

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>" && git push -q && echo "video no git: $(git log --oneline -1)" > /home/lucas/corexy/out/anim/video_git.txt
