#!/bin/bash
# ./scripts/foco_canto.sh outdir  -> renders de perto do canto +X+Y da mesa (presilha_1)
OUT=${1:-out/presilha2}; mkdir -p $OUT
python3 - <<'PY' > /dev/null
import json, numpy as np
J = json.load(open("/home/lucas/corexy100/out/cxy.json"))
k = [j for j in J if j["nome"] in ("mesa_vidro", "mesa_suporteMesa") or (j["nome"].startswith("mesa_") and j["nome"].endswith("_1"))]
json.dump(k, open("/home/lucas/corexy100/out/canto.json", "w"))
T = np.array([j for j in k if j["nome"] == "mesa_presilha_1"][0]["T"])
open("/home/lucas/corexy100/out/canto.txt", "w").write("%.2f/%.2f/%.2f" % (121.0, 121.0, 0))
PY
C=$(python3 -c "
import json;J={j['nome']:j for j in json.load(open('/home/lucas/corexy100/out/canto.json'))}
import numpy as np;from trimesh import load
m=load(J['mesa_presilha_1']['stl']);m.apply_transform(np.array(J['mesa_presilha_1']['T']));b=m.bounds;c=(b[0]+b[1])/2
print('%.2f/%.2f/%.2f'%(c[0]-3,c[1]-3,b[1][2]-4))")
LD_LIBRARY_PATH=~/.local/opt/blibs/root/usr/lib/x86_64-linux-gnu ~/.local/opt/blender-4.2.3-linux-x64/blender -b --factory-startup -P ~/mulbot/scripts/render_asm.py -- out/canto.json $OUT \
 "iso:1/-1.25/0.85:$C:42,lado:1/-1/0.0001:$C:42,topo:0.01/-0.02/1:$C:40,tras:-1/1.2/0.7:$C:42" 800 2>&1 | grep -iE "error|Traceback" | head
