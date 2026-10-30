#!/bin/bash
# CoreXY 100: exporta blend/glb/3mf e renderiza as 8 imagens finais (Cycles 64 amostras, 1200 px) igual a 200
P=/home/lucas/corexy100/trab/prog_img.txt; L=/home/lucas/corexy100/trab/imagens.log; CX=/home/lucas/corexy100
BL=~/.local/opt/blender-4.2.3-linux-x64/blender; export LD_LIBRARY_PATH=~/.local/opt/blibs/root/usr/lib/x86_64-linux-gnu
cd $CX; echo 1000 > /proc/self/oom_score_adj; : > $L; : > $P; N=13; i=0
passo() { echo "$i $N $1" >> $P; i=$((i+1)); }
passo "montagem na pose padrao"; ESFERAS=0 python3 scripts/cxy.py >> $L 2>&1 || { echo "ERRO cxy" >> $P; exit 1; }
for e in blend glb leve 3mf; do passo "exportando $e"; python3 scripts/exporta.py $e >> $L 2>&1 || { echo "ERRO exporta $e" >> $P; exit 1; }; done
for v in heroi heroi2 tras lado topo carro_hotend carro_rodas mesa; do
  passo "render $v"; $BL -b final/corexy_montagem_leve.blend -P scripts/render_final.py -- final/render CYCLES 64 1200 final/limites.json $v >> $L 2>&1 || { echo "ERRO render $v" >> $P; exit 1; }
done
D="/mnt/c/Users/lucas/Documents/Projetos 3D/CoreXY/CoreXY 100/01 Montagem 3D"; mkdir -p "$D"
cp final/corexy_montagem*.blend final/corexy_montagem*.glb final/corexy_montagem.3mf "$D"/; ls final/render/*.png >/dev/null 2>&1 || { echo "ERRO renders nao sairam" >> $P; exit 1; }; cp final/render/*.png "$D"/ && rm -f "$D/CoreXY100_iso.png"
echo "FIM CoreXY 100: 8 imagens finais e montagem 3D em Documentos" >> $P
