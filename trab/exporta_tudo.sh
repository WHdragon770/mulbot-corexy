#!/bin/bash
S=/tmp/claude-1000/-home-lucas/e557defd-4194-41b3-9f1b-ccad173c7b9a/scratchpad; P=$S/prog_exp.txt; L=/home/lucas/corexy/trab/exporta.log; CX=/home/lucas/corexy
BL=~/.local/opt/blender-4.2.3-linux-x64/blender; export LD_LIBRARY_PATH=~/.local/opt/blibs/root/usr/lib/x86_64-linux-gnu
cd $CX; echo 1000 > /proc/self/oom_score_adj; : > $L; N=14; i=0
passo() { echo "$i $N $1" >> $P; i=$((i+1)); }
passo "montagem na pose padrao"; ESFERAS=0 python3 scripts/cxy.py >> $L 2>&1 || { echo "ERRO cxy" >> $P; exit 1; }
for e in blend glb leve 3mf; do passo "exportando $e"; python3 scripts/exporta.py $e >> $L 2>&1 || { echo "ERRO exporta $e" >> $P; exit 1; }; done
for v in heroi heroi2 tras lado topo carro_hotend carro_rodas mesa; do
  passo "render $v"; $BL -b final/corexy_montagem_leve.blend -P scripts/render_final.py -- final/render CYCLES 64 1200 final/limites.json $v >> $L 2>&1 || { echo "ERRO render $v" >> $P; exit 1; }
done
passo "desenhos de montagem"; rm -rf final/desenhos; python3 scripts/desenhos/folhas.py final/desenhos >> $L 2>&1 || { echo "ERRO desenhos" >> $P; exit 1; }
echo "FIM Montagem 3D, renders e desenhos atualizados" >> $P
