#!/bin/bash
P=/tmp/claude-1000/-home-lucas/e557defd-4194-41b3-9f1b-ccad173c7b9a/scratchpad/prog_chk.txt; L=/home/lucas/corexy/trab/checagens.log; cd /home/lucas/corexy
echo 1000 > /proc/self/oom_score_adj; : > $L
echo "0 4 cabos (sonda 4.5 mm)" >> $P; echo "== cabos" >> $L; python3 scripts/cabos_check.py 4.5 1 2>&1 | grep -v Warn >> $L
echo "1 4 correias" >> $P; echo "== correias" >> $L; python3 scripts/colisao_correia.py 2>&1 | grep -v Warn | tail -15 >> $L
echo "2 4 colisao 22 poses" >> $P; echo "== colisao" >> $L; python3 scripts/colisao.py 2>&1 | grep -v Warn | tail -8 >> $L
echo "3 4 colisao parada" >> $P; echo "== parada" >> $L; python3 scripts/estatica.py dutoCoreXY carroX bracoFimCursoX suportePortico bracoMesa baseZInf baseZSup torreTras trilhoY base poste trav 2>&1 | grep -v Warn | tail -40 >> $L
echo "FIM checagens prontas" >> $P
