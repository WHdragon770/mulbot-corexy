#!/bin/bash
# conferencia rapida sem suporte das pecas novas: derived/<peca>.stl -> rotacao fixa (impressao_rot.json) -> semsup_check
# rapido.sh <pasta_saida> [peca ...]
OUT=$1; shift; mkdir -p $OUT
python3 - "$OUT" "$@" <<'PY'
import sys, json, numpy as np, trimesh
out, so = sys.argv[1], sys.argv[2:]
R = json.load(open("/home/lucas/corexy100/scripts/placas/impressao_rot.json"))
for k, v in R.items():
    if k.startswith(("DL1-", "fusoZ", "porcaZ", "presilha")) or (so and k not in so): continue
    m = trimesh.load(f"/home/lucas/corexy100/derived/{k}.stl", process=False)
    T = np.eye(4); T[:3, :3] = v; m.apply_transform(T); m.apply_translation(-m.bounds[0]); m.export(f"{out}/{k}.stl")
PY
cd /home/lucas/corexy100/scripts/placas; JSON=$OUT/check.json python3 semsup_check.py $OUT/*.stl 2>&1 | grep -v Warn | grep ilha
