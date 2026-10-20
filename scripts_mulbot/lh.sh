#!/bin/bash
# lista furos pequenos de pecas
for p in "$@"; do echo "== $p"; head -1 ~/mulbot/feat/"$p".txt | cut -c1-200; grep hole ~/mulbot/feat/"$p".txt | python3 -c "
import sys,ast
L=[]
for l in sys.stdin:
  h=ast.literal_eval(l.split('hole ',1)[1])
  if h['d']<${DMAX:-9}: L.append(h)
L.sort(key=lambda h:(h['ax'],[x if x is not None else 0 for x in h['c']],h['lo']))
for h in L: print('  ',h['ax'],h['c'],h['d'],h['lo'],h['hi'])
"; done
