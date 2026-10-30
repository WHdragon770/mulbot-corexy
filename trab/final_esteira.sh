#!/bin/bash
S=/tmp/claude-1000/-home-lucas/a7d1791e-1798-4349-a13b-8bb88e69054d/scratchpad; P=$S/prog_esteira.txt; T=/home/lucas/corexy/trab; L=$T/final.log
cd /home/lucas/corexy/scripts; echo 1000 > /proc/self/oom_score_adj; : > $L
echo "0 8 montagem + STL por conjunto" >> $P
( cd /home/lucas/corexy; ESFERAS=0 python3 scripts/cxy.py ) >> $L 2>&1 || { echo "ERRO cxy" >> $P; exit 1; }
rm -rf $T/stl_v4; python3 stl_impressao.py $T/stl_v4 >> $L 2>&1 || { echo "ERRO stl_impressao" >> $P; exit 1; }
echo "1 8 orientando as pecas novas" >> $P
[ -d $T/orient4 ] || cp -r $T/orient3 $T/orient4
SO=$(python3 -c "import json; print(','.join(k for k in json.load(open('placas/impressao_rot.json')) if not k.startswith(('DL1-','fusoZ','porcaZ','presilha'))))")
( cd placas; SO=$SO python3 orienta.py $T/stl_v4 $T/orient4 2>&1 | grep -v Warn ) >> $L 2>&1 || { echo "ERRO orienta" >> $P; exit 1; }
echo "2 8 verificando todas as pecas (ponte 10)" >> $P
find $T/orient4 -name "*.stl" | grep -v -E "Resina|07 Rold" | sort | tr '\n' '\0' | (cd placas; PONTE=10 JSON=$T/semsup_final.json xargs -0 python3 semsup_check.py) 2>&1 | grep -v Warn | grep ilha > $T/semsup_final.txt
echo "3 8 placas 3MF + resina" >> $P
rm -rf $T/placas4; ( cd placas; python3 placas.py $T/orient4 $T/placas4 && python3 resina.py $T/orient4 "$T/placas4/Resina (Photon)" ) >> $L 2>&1 || { echo "ERRO placas" >> $P; exit 1; }
mkdir -p "$T/placas4/Previa das placas"; for f in "$T/placas4/Kobra X (3MF)"/*.3mf; do b=$(basename "$f" .3mf); ( cd placas; python3 ver_placas.py "$f" "$T/placas4/Previa das placas/$b.png" ) >> $L 2>&1; done
echo "4 8 fatiando no Slicer Next" >> $P
: > $S/prog_fatia.txt; ( cd placas; ./fatia_teste.sh "$T/placas4/Kobra X (3MF)" $S/prog_fatia.txt ) >> $L 2>&1
cp /mnt/c/Users/lucas/AppData/Local/Temp/cxy_fatia/resultado.txt $T/fatia_resultado.txt
echo "5 8 colisao 22 poses" >> $P
( cd /home/lucas/corexy; python3 scripts/colisao.py 2>&1 | grep -v Warn | tail -5 ) > $T/colisao_final.txt
echo "6 8 correias" >> $P
( cd /home/lucas/corexy; python3 scripts/colisao_correia.py 2>&1 | grep -v Warn | tail -6 ) > $T/correia_final.txt
echo "7 8 cabos" >> $P
( cd /home/lucas/corexy; python3 scripts/cabos_check.py 4.5 1 2>&1 | grep -v Warn ) > $T/cabos_final.txt
( cd /home/lucas/corexy; CABOS=0 python3 scripts/colisao_esteira.py 2>&1 | grep -v Warn | grep -A20 "^esteira:" ) > $T/colisao_esteira_final.txt; ( cd /home/lucas/corexy; ESFERAS=0 python3 scripts/cxy.py ) >> $L 2>&1
echo "FIM Regeracao final pronta: $(grep -vc ' 0 ilha' $T/semsup_final.txt) arquivo(s) com ilha" >> $P
