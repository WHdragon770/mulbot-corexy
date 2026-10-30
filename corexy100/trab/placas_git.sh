#!/bin/bash
# Refaz as placas da 100 e sobe no git se der FIM
T=/home/lucas/corexy100/trab; G=/home/lucas/repos/mulbot-corexy; W="/mnt/c/Users/lucas/Documents/Projetos 3D/CoreXY/CoreXY 100"
$T/placas100.sh
grep -q "^FIM" $T/prog_placas.txt || { echo "placas deram ERRO, nada subiu"; exit 1; }
cp $T/placas100.sh $G/corexy100/trab/; cd $G; rm -rf "corexy100/entrega/06 Placas de impressao"; cp -r "$W/06 Placas de impressao" corexy100/entrega/
git add -A corexy100 && git commit -qm "CoreXY 100: 5 pecas sem parte no ar (janela da fonte em 5, junta da base Z +15, apoio do braco da mesa) + 02 STL e placas refeitos

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>" && git push -q && echo "placas no git: $(git log --oneline -1)"
