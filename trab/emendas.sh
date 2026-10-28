#!/bin/bash
# Desenhos de emenda da 200 impressa na 100: recorta de novo (so pra ter o cortes.json com as posicoes) e gera as folhas EM-00..
CX=/home/lucas/corexy; P=$CX/trab/prog_emendas.txt; L=$CX/trab/emendas.log; N=$CX/trab/na100
W="/mnt/c/Users/lucas/Documents/Projetos 3D/CoreXY/CoreXY 200"
cd $CX; : > $L; rm -rf $N
( while sleep 15; do echo "$(grep -c partes $L) 46 Emendas 200: recortando as pecas" > $P; done ) & B=$!
python3 scripts/cortar_na_100.py "$W/02 STL para imprimir" $N >> $L 2>&1; r=$?; kill $B
[ $r -ne 0 ] && { echo "ERRO Emendas 200: recorte falhou (trab/emendas.log)" > $P; exit 1; }
( while sleep 15; do echo "$(grep -c '^EM-' $L) 46 Emendas 200: desenhando as folhas" > $P; done ) & B=$!
python3 scripts/desenhos/emendas.py $N $CX/final/desenhos_na100 >> $L 2>&1; r=$?; kill $B
[ $r -ne 0 ] && { echo "ERRO Emendas 200: folhas falharam (trab/emendas.log)" > $P; exit 1; }
D="$W/03b Desenhos de emenda (impressa na 100)"; rm -rf "$D"; mkdir -p "$D"; cp $CX/final/desenhos_na100/*.png $CX/final/desenhos_na100/*.pdf "$D/"
echo "FIM Emendas 200 prontas: CoreXY 200\\03b Desenhos de emenda ($(ls "$D" | wc -l) arquivos)" > $P
