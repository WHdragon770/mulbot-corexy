#!/bin/bash
cd ~/corexy100; PR=out/checa_prog.txt; echo 1000 > /proc/self/oom_score_adj
echo "1 3 colisao" > $PR; python3 scripts/colisao.py > out/colisao.log 2>&1 || { echo "ERRO colisao" > $PR; exit 1; }
echo "2 3 esteira" > $PR; python3 scripts/colisao_esteira.py > out/col_esteira.log 2>&1 || { echo "ERRO esteira" > $PR; exit 1; }
echo "3 3 cabos" > $PR; python3 scripts/cabos_check.py 4.5 1 > out/cabos_check.log 2>&1 || { echo "ERRO cabos_check" > $PR; exit 1; }
echo "FIM CoreXY 100: checagens prontas" > $PR
