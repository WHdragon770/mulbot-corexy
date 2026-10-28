#!/bin/bash
# Corrige as 5 pecas com parte no ar: regera, confere sem suporte nas pecas mexidas e colisao (22 poses), atualiza o 02
CX=/home/lucas/corexy100; T=$CX/trab; P=$T/prog_fix5.txt; L=$T/fix5.log; S=$CX/scripts/placas
W="/mnt/c/Users/lucas/Documents/Projetos 3D/CoreXY/CoreXY 100"; echo 1000 > /proc/self/oom_score_adj; : > $L
cd $CX
echo "0 5 montagem (cxy.py)" > $P; ESFERAS=0 python3 scripts/cxy.py >> $L 2>&1 || { echo "ERRO fix5: cxy.py" > $P; exit 1; }
echo "1 5 STL para imprimir" > $P; rm -rf $T/stl_novo; python3 scripts/stl_impressao.py $T/stl_novo >> $L 2>&1 || { echo "ERRO fix5: stl_impressao" > $P; exit 1; }
echo "2 5 orientando as pecas mexidas" > $P
SO=posteTrasInf_D,posteTrasInf_E,baseZInf_D,baseZInf_E,baseZSup_D,posteFrenteInf_D,posteFrenteInf_E,bracoMesa_D,bracoMesa_E
rm -rf $T/fix_or; mkdir -p $T/fix_or; echo '{}' > $T/fix_or/orienta.json
(cd $S; SO=$SO python3 orienta.py $T/stl_novo $T/fix_or) >> $L 2>&1 || { echo "ERRO fix5: orienta" > $P; exit 1; }
echo "3 5 sem suporte (ponte 10)" > $P
find $T/fix_or -name "*.stl" | sort | tr '\n' '\0' | (cd $S; PONTE=10 xargs -0 python3 semsup_check.py) 2>&1 | grep -v Warn | tee -a $L > $T/fix5_semsup.txt
echo "4 5 colisao (22 poses)" > $P
python3 scripts/colisao.py > $T/fix5_colisao.txt 2>&1
echo "FIM fix5: $(grep -c ' 0 ilha' $T/fix5_semsup.txt)/9 sem ilha, $(tail -1 $T/fix5_colisao.txt)" > $P
