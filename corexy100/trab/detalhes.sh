#!/bin/bash
# Fotos de detalhe da CoreXY 100 (mesmas da 200, enquadramentos com x +-50, y -50 atras, z -100) -> trab/detalhes, copia pra 04 Detalhes
CX=/home/lucas/corexy100; P=$CX/trab/prog_detalhes.txt; L=$CX/trab/detalhes.log; O=$CX/trab/detalhes
BL=~/.local/opt/blender-4.2.3-linux-x64/blender; export LD_LIBRARY_PATH=~/.local/opt/blibs/root/usr/lib/x86_64-linux-gnu
BW="$BL -b --factory-startup -P"; RC="$BW scripts/render_caixa.py -- out/cxy.json"
WIN="/mnt/c/Users/lucas/Documents/Projetos 3D/CoreXY/CoreXY 100/04 Detalhes (imagens)"
cd $CX; echo 1000 > /proc/self/oom_score_adj; : > $L; rm -rf $O; mkdir -p $O
N=8; i=0; passo() { echo "$i $N Detalhes 100: $1" > $P; echo "== $1" >> $L; i=$((i+1)); }
falha() { echo "ERRO Detalhes 100: $1 (ver trab/detalhes.log)" > $P; exit 1; }
passo "extrusora direta"
$RC $O/extrusora -90,-90,330 90,130,520 \
 "extrusora_direta_frente:260/-330/620:0/10/400:45;extrusora_direta_lado:420/40/460:0/15/400:50;extrusora_direta_tras:-230/330/600:0/10/410:45" >> $L 2>&1 || falha "extrusora"
passo "presilha do vidro"; bash scripts/foco_canto.sh $O/presilha >> $L 2>&1 || falha "presilha"
passo "passagem de cabos"
python3 - >> $L 2>&1 <<PY || falha "cabos json"
import json,sys,numpy as np,trimesh
sys.path.insert(0,'scripts'); from base import M,Tm,caixa
J=json.load(open('out/cxy.json')); D={j['nome']:j for j in J}
V=[j for j in J if j['nome'].startswith(('caixaRAMPS','portaRAMPS','fonte','protecaoFonte','display','motor','fimCurso','lcd'))]
V.append(dict(nome='ar',stl='$CX/derived/cabos_ar.stl',T=np.eye(4).tolist(),cor='azul'))
json.dump(V,open('$O/cabos_rede.json','w'))
out=[]
for n,cut in (('posteTrasInf_E',caixa((-126,100,-1),(-50,210,300))),('baseLatT_E',caixa((-126,-50,-1),(-50,210,300))),('baseTras_E',caixa((-150,157,-1),(50,210,300))),
              ('posteTrasSup_E',caixa((-126,100,90),(-50,210,300)))):
    m=trimesh.load(D[n]['stl']); m.apply_transform(np.array(D[n]['T'])); c=M(m)-cut
    fn='$O/corte_'+n+'.stl'; Tm(c).export(fn); out.append(dict(nome=n,stl=fn,T=np.eye(4).tolist(),cor='cinza'))
out.append(D['caixaRAMPS']); json.dump(out,open('$O/cabos_corte.json','w'))
PY
$BW ~/mulbot/scripts/render_asm.py -- $O/cabos_rede.json $O/cabos iso,isoE 1100 >> $L 2>&1 || falha "cabos rede"
$BW ~/mulbot/scripts/render_asm.py -- $O/cabos_corte.json $O/cabos "canto:1/-0.6/0.5:-100/130/110:240" 1100 >> $L 2>&1 || falha "cabos corte"
passo "guias em V (X, Y e Z)"
$RC $O/guia_v -70,-30,320 70,110,460 "carroX_frente:180/-260/500:0/35/385:50;carroX_tras:-170/320/520:0/35/385:50" >> $L 2>&1 || falha "guia X"
$RC $O/guia_v -190,-20,300 -60,120,470 "carroY_fora:-430/-150/460:-125/45/350:50;carroY_dentro:20/-120/280:-125/45/350:45" >> $L 2>&1 || falha "guia Y"
$RC $O/guia_v -190,-110,137 -50,60,277 "eixoZ_frente:-270/-330/317:-115/-25/212:50;eixoZ_dentro:30/-260/257:-115/-25/212:45" >> $L 2>&1 || falha "guia Z"
passo "esteira porta-cabos"
$RC $O/esteira -1000,-1000,-1000 1000,1000,1000 "visao_geral:560/-400/760:20/20/330:35;visao_de_tras:280/520/680:40/30/360:40" >> $L 2>&1 || falha "esteira geral"
$RC $O/esteira -105,-20,370 105,140,500 "esteira_X_por_tras:-120/330/600:-20/80/415:40;esteira_X_de_cima:60/-150/660:-20/70/420:40" >> $L 2>&1 || falha "esteira X"
$RC $O/esteira 90,-120,240 210,190,460 "esteira_Y_por_fora:470/-160/500:180/60/350:45;esteira_Y_entrada_torre:370/370/460:170/120/360:45" >> $L 2>&1 || falha "esteira Y"
python3 - >> $L 2>&1 <<PY2 || falha "elo json"
import json, numpy as np
json.dump([dict(nome="elo%d" % k, stl="$CX/derived/elo_esteira.stl", T=(np.eye(4) + np.array([[0,0,0,k*16.0],[0,0,0,0],[0,0,0,0],[0,0,0,0]])).tolist(), cor="preto") for k in range(3)], open("$O/elo.json", "w"))
PY2
$BW scripts/render_caixa.py -- $O/elo.json $O/esteira -100,-100,-100 200,100,100 "elo_3_juntos:20/-70/45:24/0/0:50;elo_por_cima:24/-1/90:24/0/0:50" >> $L 2>&1 || falha "elo"
rm -f $O/*.json $O/*.stl
echo "$N $N Detalhes 100: prontos ($(find $O -name '*.png' | wc -l) PNG), aguardando conferencia" > $P
