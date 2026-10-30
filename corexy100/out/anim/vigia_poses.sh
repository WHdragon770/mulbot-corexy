#!/bin/bash
P=~/corexy100/out/anim/poses.prog; J=~/corexy100/out/anim/poses/poses_parcial.json
while pgrep -f "poses.py 60" >/dev/null; do
  n=$(python3 -c "import json;print(len(json.load(open('$J'))))" 2>/dev/null || echo 0)
  echo "$n 60 Poses CoreXY 100: $n de 60" >> $P; sleep 20
done
n=$(python3 -c "import json;print(len(json.load(open('$J'))))" 2>/dev/null)
n=$(python3 -c "import json;print(len(json.load(open('$HOME/corexy100/out/anim/poses/poses.json'))['poses']))" 2>/dev/null); if [ "$n" = 60 ]; then echo "FIM Poses CoreXY 100 prontas (60/60)" >> $P; else echo "ERRO Poses pararam em $n de 60" >> $P; fi
