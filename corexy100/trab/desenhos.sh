#!/bin/bash
# Desenhos de montagem da CoreXY 100 (12 folhas CXY-00..11) -> final/desenhos + PDF, copia pra 03 Desenhos de montagem
CX=/home/lucas/corexy100; P=$CX/trab/prog_desenhos.txt; L=$CX/trab/desenhos.log; O=$CX/out/cabos/corte
BL=~/.local/opt/blender-4.2.3-linux-x64/blender; export LD_LIBRARY_PATH=~/.local/opt/blibs/root/usr/lib/x86_64-linux-gnu
WIN="/mnt/c/Users/lucas/Documents/Projetos 3D/CoreXY/CoreXY 100/03 Desenhos de montagem"
cd $CX; : > $L; mkdir -p $O; echo "0 3 Desenhos 100: corte do canto (cabos)" > $P
python3 - >> $L 2>&1 <<PY || { echo "ERRO Desenhos 100: corte json" > $P; exit 1; }
import json,sys,numpy as np,trimesh
sys.path.insert(0,'scripts'); from base import M,Tm,caixa
D={j['nome']:j for j in json.load(open('out/cxy.json'))}
out=[]
for n,cut in (('posteTrasInf_E',caixa((-126,100,-1),(-50,210,300))),('baseLatT_E',caixa((-126,-50,-1),(-50,210,300))),('baseTras_E',caixa((-150,157,-1),(50,210,300))),
              ('posteTrasSup_E',caixa((-126,100,90),(-50,210,300)))):   # caixas da 200 com x +50, y -50 (z do poste de cima -100)
    m=trimesh.load(D[n]['stl']); m.apply_transform(np.array(D[n]['T'])); c=M(m)-cut
    fn='$O/corte_'+n+'.stl'; Tm(c).export(fn); out.append(dict(nome=n,stl=fn,T=np.eye(4).tolist(),cor='cinza'))
out.append(D['caixaRAMPS']); json.dump(out,open('$O/cabos_corte.json','w'))
PY
$BL -b --factory-startup -P ~/mulbot/scripts/render_asm.py -- $O/cabos_corte.json $O "canto:1/-0.6/0.5:-100/130/110:240" 1100 >> $L 2>&1 || { echo "ERRO Desenhos 100: render corte" > $P; exit 1; }
echo "1 3 Desenhos 100: 12 folhas" > $P
rm -rf final/desenhos; python3 scripts/desenhos/folhas.py final/desenhos >> $L 2>&1 || { echo "ERRO Desenhos 100: folhas.py (ver trab/desenhos.log)" > $P; exit 1; }
echo "2 3 Desenhos 100: copiando" > $P
rm -rf "$WIN"; mkdir -p "$WIN"; cp final/desenhos/*.png final/desenhos/*.pdf "$WIN"/ 2>/dev/null
echo "FIM Desenhos da 100 prontos: CoreXY 100\\03 Desenhos de montagem ($(ls "$WIN" | wc -l) arquivos)" > $P
