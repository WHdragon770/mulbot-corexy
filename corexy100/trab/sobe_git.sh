#!/bin/bash
# Sobe no git cada etapa da fila_tarde quando termina: placas -> manual completo
T=/home/lucas/corexy100/trab; G=/home/lucas/repos/mulbot-corexy; W="/mnt/c/Users/lucas/Documents/Projetos 3D/CoreXY/CoreXY 100"
CO="

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"
until grep -qE "^(FIM|ERRO)" $T/prog_placas.txt; do sleep 30; done
if grep -q "^FIM" $T/prog_placas.txt; then
  cd $G; rm -rf "corexy100/entrega/06 Placas de impressao"; cp -r "$W/06 Placas de impressao" corexy100/entrega/
  git add -A corexy100/entrega && git commit -qm "CoreXY 100: placas de impressao (3MF Kobra X, resina, previas)$CO" && git push -q && echo "placas no git: $(git log --oneline -1)"
else echo "placas deram ERRO, nada subiu"; fi
until grep -qE "^(FIM|ERRO)" $T/prog_manual.txt 2>/dev/null; do sleep 30; done
if grep -q "^FIM" $T/prog_manual.txt; then
  cd $G; cp "$W/03 Desenhos de montagem/manual completo.pdf" "corexy100/entrega/03 Desenhos de montagem/"
  git add -A corexy100/entrega && git commit -qm "CoreXY 100: manual completo em PDF$CO" && git push -q && echo "manual no git: $(git log --oneline -1)"
else echo "manual deu ERRO, nada subiu"; fi
tail -n 1 $T/prog_placas.txt $T/prog_manual.txt
