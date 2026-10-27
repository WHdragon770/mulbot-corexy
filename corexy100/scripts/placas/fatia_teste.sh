#!/bin/bash
# Fatia todas as placas de cada 3MF no Anycubic Slicer Next (CLI) p/ conferir; o CLI trava com nome de placa -> fatia uma copia sem nome
# fatia_teste.sh <pasta_3mf> <arquivo_progresso>   -> resultado em <pasta_3mf>/../fatiamento/<arquivo>/plate_N.gcode
D="$1"; PRG="$2"; T=/mnt/c/Users/lucas/AppData/Local/Temp/cxy_fatia; WT='C:\Users\lucas\AppData\Local\Temp\cxy_fatia'
EXE="/mnt/c/Program Files/AnycubicSlicerNext/AnycubicSlicerNext.exe"
rm -rf $T; mkdir -p $T; N=$(ls "$D"/*.3mf | wc -l); i=0
for f in "$D"/*.3mf; do
  b=$(basename "$f" .3mf); i=$((i+1)); echo "$i $((N+1)) fatiando $b" >> "$PRG"
  python3 -c "
import zipfile,re,sys
a=zipfile.ZipFile(sys.argv[1])
with zipfile.ZipFile(sys.argv[2],'w',zipfile.ZIP_DEFLATED) as z:
    for n in a.namelist():
        d=a.read(n)
        if n=='Metadata/model_settings.config': d=re.sub(r'plater_name\" value=\"[^\"]*\"','plater_name\" value=\"\"',d.decode())
        z.writestr(n,d)" "$f" "$T/$i.3mf"
  mkdir -p "$T/out$i"
  timeout 3000 "$EXE" --slice 0 --outputdir "$WT\\out$i" "$WT\\$i.3mf" > "$T/log$i.txt" 2>&1; rc=$?
  echo "$b|$rc|$(ls $T/out$i | grep -c 'gcode$')" >> $T/resultado.txt
done
echo "FIM Placas da CoreXY fatiadas: $(cat $T/resultado.txt | tr '\n' ' ')" >> "$PRG"
