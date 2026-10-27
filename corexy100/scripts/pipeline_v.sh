#!/bin/bash
# regera tudo apos a troca X/Y para guia em V: montagem, STL de impressao, blend/glb/leve/3mf e renders (1 vista por processo)
PR=/home/lucas/corexy100/out/progresso_v.txt; CX=/home/lucas/corexy100; N=15; i=0
BL=~/.local/opt/blender-4.2.3-linux-x64/blender; export LD_LIBRARY_PATH=~/.local/opt/blibs/root/usr/lib/x86_64-linux-gnu
passo() { i=$((i+1)); echo "$i $N $1" > $PR; }
falha() { echo "ERRO $1" > $PR; exit 1; }
cd $CX
passo "Montagem (cxy.py)"; ESFERAS=0 python3 scripts/cxy.py > out/pipe.log 2>&1 || falha "cxy.py"
passo "Conferindo passagem dos cabos (sonda 4.5 mm)"; (echo 1000 > /proc/self/oom_score_adj; python3 scripts/cabos_check.py 4.5 1) >> out/pipe.log 2>&1 || falha "cabos_check"
passo "STL para imprimir"; rm -rf out/stl_v; python3 scripts/stl_impressao.py out/stl_v >> out/pipe.log 2>&1 || falha "stl_impressao"
for e in blend glb leve 3mf; do passo "Exportando $e"; python3 scripts/exporta.py $e >> out/pipe.log 2>&1 || falha "exporta $e"; done
for v in heroi heroi2 tras lado topo carro_hotend carro_rodas mesa; do
  passo "Render $v"
  $BL -b final/corexy_montagem_leve.blend -P scripts/render_final.py -- final/render CYCLES 64 1200 final/limites.json $v >> out/pipe.log 2>&1 || falha "render $v"
done
echo "FIM CoreXY: quadro oco com passagem de cabos - exportacao e renders prontos" > $PR
