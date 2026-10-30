#!/bin/bash
# Entrega da mesa aquecida (MESA=220 e 235): montagem, STL das pecas que mudam (ja deitadas p/ imprimir), imagens e .glb
S=/tmp/claude-1000/-home-lucas/8e120b17-d074-43e4-a34d-99bb784f54bb/scratchpad; P=$S/prog_aq.txt
C=/home/lucas/corexy; T=$C/trab; O=$T/aq_entrega; L=$T/aq_entrega.log
BL="env LD_LIBRARY_PATH=$HOME/.local/opt/blibs/root/usr/lib/x86_64-linux-gnu $HOME/.local/opt/blender-4.2.3-linux-x64/blender -b --factory-startup"
cd $C; echo 1000 > /proc/self/oom_score_adj; rm -rf $O; : > $L
i=0
for v in 220 235; do
  D="$O/$v"; mkdir -p "$D/STL para imprimir" "$D/Imagens"
  echo "$i 8 mesa $v: montagem" >> $P; i=$((i+1))
  MESA=$v ESFERAS=0 python3 scripts/cxy.py >> $L 2>&1 || { echo "ERRO cxy $v" >> $P; exit 1; }
  cp out/cxy.json $T/cxy_$v.json
  python3 - "$v" "$D/STL para imprimir" >> $L 2>&1 <<'PY' || { echo "ERRO stl $v" >> $P; exit 1; }
import sys, json, numpy as np, trimesh
v, out = sys.argv[1], sys.argv[2]
R = json.load(open("/home/lucas/corexy/scripts/placas/impressao_rot.json"))
for n, q in ((f"localizador_aq{v}", 4), ("presilha_disco_aq", 4), ("calcoFimCursoZ", 1), ("protecaoFonte360", 1)):
    m = trimesh.load(f"/home/lucas/corexy/derived/{n}.stl"); T = np.eye(4); T[:3, :3] = R[n]; m.apply_transform(T)
    b = m.bounds; m.apply_translation([-(b[0][0] + b[1][0]) / 2, -(b[0][1] + b[1][1]) / 2, -b[0][2]])
    m.export(f"{out}/{n} [{q}x].stl")
PY
  echo "$i 8 mesa $v: imagens" >> $P; i=$((i+1))
  ./scripts/foco_canto.sh $T/canto_$v >> $L 2>&1
  for f in iso tras topo; do cp $T/canto_$v/$f.png "$D/Imagens/canto_mesa_$f.png"; done
  $BL -P scripts/render_caixa.py -- out/cxy.json "$D/Imagens" 60,180,0 260,400,320 \
    "fonte_tras:420/620/300:145/280/150:35;fonte_lado_mosfet:-150/560/220:120/280/100:35" >> $L 2>&1
  $BL -P scripts/render_caixa.py -- out/cxy.json "$D/Imagens" -260,-200,330 260,200,420 \
    "mesa_geral:420/-520/620:0/0/380:40" >> $L 2>&1
  $BL -P scripts/render_caixa.py -- out/cxy.json "$D/Imagens" -400,-400,-50 400,400,700 \
    "maquina_iso:1100/-1300/1000:0/40/250:40" >> $L 2>&1
  $BL -P scripts/render_caixa.py -- out/cxy.json "$D/Imagens" -230,-80,320 -130,0,370 \
    "fim_curso_Z_calco:-60/-260/300:-176/-50/350:60" >> $L 2>&1
  echo "$i 8 mesa $v: montagem 3D (.glb)" >> $P; i=$((i+1))
  python3 - "$D/corexy_mesa_aquecida_$v.glb" >> $L 2>&1 <<'PY' || echo "AVISO glb $v" >> $P
import sys, json, numpy as np, trimesh
CORES = {"cinza": (200, 202, 204), "verm": (184, 20, 18), "azul": (13, 89, 122), "preto": (15, 15, 18), "aco": (153, 158, 166),
         "vidro": (178, 217, 217), "alu": (209, 212, 217), "pcb": (13, 77, 31), "lcd": (140, 153, 217), "latao": (242, 184, 26)}
sc = trimesh.Scene(); cache = {}
for e in json.load(open("/home/lucas/corexy/out/cxy.json")):
    if e["stl"] not in cache: cache[e["stl"]] = trimesh.load(e["stl"])
    m = cache[e["stl"]].copy(); m.visual.face_colors = (*CORES.get(e["cor"], (128, 128, 128)), 90 if e["cor"] == "vidro" else 255)
    sc.add_geometry(m, node_name=e["nome"], transform=np.array(e["T"]))
sc.export(sys.argv[1]); print("glb", sys.argv[1])
PY
  i=$((i+1))
done
echo "7 8 voltando a montagem padrao (mesa fria)" >> $P
ESFERAS=0 python3 scripts/cxy.py >> $L 2>&1
echo "FIM Mesa aquecida 220 e 235 prontas em trab/aq_entrega" >> $P
