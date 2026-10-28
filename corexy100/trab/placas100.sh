#!/bin/bash
# Placas de impressao da CoreXY 100: copia o 02 STL, orienta, monta 3MF Kobra X + placa de resina + previas, fatia e entrega em 06
T=/home/lucas/corexy100/trab; P=$T/prog_placas.txt; L=$T/placas.log; S=/home/lucas/corexy100/scripts/placas
W="/mnt/c/Users/lucas/Documents/Projetos 3D/CoreXY/CoreXY 100"; echo 1000 > /proc/self/oom_score_adj; : > $L; : > $P
echo "0 6 copiando os STL" >> $P
rm -rf $T/stl $T/orient $T/placas; cp -r "$W/02 STL para imprimir" $T/stl; rm -f $T/stl/*.csv
echo "1 6 orientando as pecas" >> $P
mkdir -p $T/orient; echo '{}' > $T/orient/orienta.json        # em lotes de 10 pecas, 1 processo por lote (tudo junto passa de 2 GB)
ls $T/stl/*/*.stl $T/stl/*/*/*.stl | sed 's#.*/##; s# \[[0-9]*x\]\.stl##' | sort -u | xargs -d '\n' -n 10 | tr ' ' ',' | while read -r SO; do
  ( cd $S; SO="$SO" python3 orienta.py $T/stl $T/orient 2>&1 | grep -v Warn; exit ${PIPESTATUS[0]} ) >> $L 2>&1 || { echo "ERRO orienta (lote $SO)" >> $P; exit 1; }
done || exit 1
echo "2 6 verificando sem suporte (ponte 10)" >> $P
find $T/orient -name "*.stl" | grep -v -E "Resina|07 Rold" | sort | tr '\n' '\0' | (cd $S; PONTE=10 JSON=$T/semsup.json xargs -0 python3 semsup_check.py) 2>&1 | grep -v Warn | grep ilha > $T/semsup.txt
echo "3 6 placas 3MF + resina" >> $P
( cd $S; python3 placas.py $T/orient $T/placas && python3 resina.py $T/orient "$T/placas/Resina (Photon)" ) >> $L 2>&1 || { echo "ERRO placas" >> $P; exit 1; }
echo "4 6 previas das placas" >> $P
mkdir -p "$T/placas/Previa das placas"; for f in "$T/placas/Kobra X (3MF)"/*.3mf; do b=$(basename "$f" .3mf); ( cd $S; python3 ver_placas.py "$f" "$T/placas/Previa das placas/$b.png" ) >> $L 2>&1; done
echo "5 6 fatiando no Slicer Next" >> $P
( cd $S; ./fatia_teste.sh "$T/placas/Kobra X (3MF)" $T/prog_fatia.txt ) >> $L 2>&1
cp /mnt/c/Users/lucas/AppData/Local/Temp/cxy_fatia/resultado.txt $T/fatia_resultado.txt 2>/dev/null
D="$W/06 Placas de impressao"; rm -rf "$D"; mkdir -p "$D"; cp -r "$T/placas/Kobra X (3MF)" "$T/placas/Resina (Photon)" "$T/placas/Previa das placas" "$D/"; cp $T/placas/*.json "$D/" 2>/dev/null
echo "FIM Placas da CoreXY 100 em 06 Placas de impressao: $(ls "$D/Kobra X (3MF)" | wc -l) 3MF, $(grep -vc ' 0 ilha' $T/semsup.txt) com ilha" >> $P
