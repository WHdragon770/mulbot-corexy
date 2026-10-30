#!/bin/bash
# Regera todas as imagens da CoreXY (renders 01, desenhos 03, detalhes 04) em trab/imagens
S=/tmp/claude-1000/-home-lucas/a7d1791e-1798-4349-a13b-8bb88e69054d/scratchpad; P=$S/prog_img.txt; CX=/home/lucas/corexy; L=$CX/trab/imagens.log
BL=~/.local/opt/blender-4.2.3-linux-x64/blender; export LD_LIBRARY_PATH=~/.local/opt/blibs/root/usr/lib/x86_64-linux-gnu
BW="$BL -b --factory-startup -P"; O=$CX/trab/imagens; cd $CX; echo 1000 > /proc/self/oom_score_adj; : > $L; rm -rf $O; mkdir -p $O
N=16; i=0; passo() { echo "$i $N $1" >> $P; echo "== $1" >> $L; i=$((i+1)); }
falha() { echo "ERRO $1" >> $P; exit 1; }
passo "montagem na pose padrao"; ESFERAS=0 python3 scripts/cxy.py >> $L 2>&1 || falha "cxy"
for v in heroi heroi2 tras lado topo carro_hotend carro_rodas mesa; do
  passo "render $v"; $BL -b final/corexy_montagem_leve.blend -P scripts/render_final.py -- $O/render CYCLES 64 1200 final/limites.json $v >> $L 2>&1 || falha "render $v"
done
passo "desenhos de montagem"; python3 scripts/desenhos/folhas.py $O/desenhos >> $L 2>&1 || falha "desenhos"
passo "detalhe: extrusora direta"
$BW scripts/render_caixa.py -- out/cxy.json $O/extrusora -200,-120,380 200,140,600 \
 "extrusora_direta_frente:260/-330/720:0/10/500:45;extrusora_direta_lado:420/40/560:0/15/500:50;extrusora_direta_tras:-230/330/700:0/10/510:45" >> $L 2>&1 || falha "extrusora"
passo "detalhe: presilha do vidro"; bash scripts/foco_canto.sh $O/presilha >> $L 2>&1 || falha "presilha"
passo "detalhe: passagem de cabos"
python3 - >> $L 2>&1 <<PY || falha "cabos json"
import json,sys,numpy as np,trimesh
sys.path.insert(0,'scripts'); from base import M,Tm,caixa
J=json.load(open('out/cxy.json')); D={j['nome']:j for j in J}
V=[j for j in J if j['nome'].startswith(('base','poste','trav','torre','trilhoY','caixaRAMPS','portaRAMPS','fonte','protecaoFonte','display','motor','fimCurso','lcd'))]
V.append(dict(nome='ar',stl='$CX/derived/cabos_ar.stl',T=np.eye(4).tolist(),cor='azul'))
R=[j for j in V if not j['nome'].startswith(('base','poste','trav','torre','trilhoY'))]
json.dump(R,open('$O/cabos_rede.json','w'))
out=[]
for n,cut in (('posteTrasInf_E',caixa((-176,150,-1),(-100,260,300))),('baseLatT_E',caixa((-176,0,-1),(-100,260,300))),('baseTras_E',caixa((-200,207,-1),(0,260,300))),
              ('posteTrasSup_E',caixa((-176,150,190),(-100,260,300)))):
    m=trimesh.load(D[n]['stl']); m.apply_transform(np.array(D[n]['T'])); c=M(m)-cut
    fn='$O/corte_'+n+'.stl'; Tm(c).export(fn); out.append(dict(nome=n,stl=fn,T=np.eye(4).tolist(),cor='cinza'))
out.append(D['caixaRAMPS']); json.dump(out,open('$O/cabos_corte.json','w'))
PY
$BW ~/mulbot/scripts/render_asm.py -- $O/cabos_rede.json $O/cabos iso,isoE 1100 >> $L 2>&1 || falha "cabos rede"
$BW ~/mulbot/scripts/render_asm.py -- $O/cabos_corte.json $O/cabos "canto:1/-0.6/0.5:-150/180/110:240" 1100 >> $L 2>&1 || falha "cabos corte"
passo "detalhe: guias em V (X, Y e Z)"
$BW scripts/render_caixa.py -- out/cxy.json $O/guia_v -70,-30,420 70,110,560 \
 "carroX_frente:180/-260/600:0/35/485:50;carroX_tras:-170/320/620:0/35/485:50" >> $L 2>&1 || falha "guia X"
$BW scripts/render_caixa.py -- out/cxy.json $O/guia_v -240,-20,400 -110,120,570 \
 "carroY_fora:-480/-150/560:-175/45/450:50;carroY_dentro:-30/-120/380:-175/45/450:45" >> $L 2>&1 || falha "guia Y"
$BW scripts/render_caixa.py -- out/cxy.json $O/guia_v -240,-110,240 -100,60,380 \
 "eixoZ_frente:-320/-330/420:-165/-25/315:50;eixoZ_dentro:-20/-260/360:-165/-25/315:45" >> $L 2>&1 || falha "guia Z"
rm -f $O/*.json $O/*.stl
echo "FIM Imagens da CoreXY regeradas ($(find $O -name '*.png' | wc -l) PNG + PDF)" >> $P
