#!/bin/bash
# Espera ate as 19:00 e entao roda o render final do video (abre a barra no Windows na hora).
CX=/home/lucas/corexy; PR=$CX/out/anim/progresso_cycles.txt
alvo=$(date -d "19:00" +%s); [ $alvo -lt $(date +%s) ] && alvo=$(date -d "tomorrow 19:00" +%s)
echo "0 1 Render do video agendado: comeca as 19:00" > $PR
while [ $(date +%s) -lt $alvo ]; do sleep 30; done
/home/lucas/bin/barra "CoreXY - video final (Cycles)" $PR
exec $CX/scripts/video/render_noite.sh "" cycles
