# Exporta a CoreXY: regrupa o cxy.json, gera .blend/.glb/.glb leve (Blender), .3mf e renders Cycles em ~/corexy/final
import json, os, sys, subprocess, numpy as np
CX = "/home/lucas/corexy"; FIN = f"{CX}/final"; os.makedirs(f"{FIN}/render", exist_ok=True)
BL = os.path.expanduser("~/.local/opt/blender-4.2.3-linux-x64/blender")
ENV = dict(os.environ, LD_LIBRARY_PATH=os.path.expanduser("~/.local/opt/blibs/root/usr/lib/x86_64-linux-gnu"))
GR = [("Quadro", ("base", "poste", "trav", "chapaZY", "pe")),
      ("Torres e motores CoreXY", ("torre", "motorA", "motorB")),
      ("Portico", ("suportePortico", "rodaY", "buchaY", "trilhoX", "loucaPortico", "fimCursoX")),
      ("Carro do hotend", ("carroX", "bracoFimCursoX", "rodaX", "buchaX", "hotend", "presilhaHotend", "duto", "ventoinha")),
      ("Polias e correias", ("louca", "correia")),
      ("Eixo Z e mesa", ("trilhoZ", "carroZ", "rodaZ", "buchaZ", "motorZ", "fusoZ", "porcaZ", "bracoMesa", "mesa", "fimCursoZ")),
      ("Trilhos Y", ("trilhoY", "fimCursoY")),
      ("Extrusora", ("ezr", "motorE", "suporteExtrusora", "bowden", "roboExtrusora")),
      ("Eletronica e display", ("caixaRAMPS", "portaRAMPS", "ramps", "mega", "fonte", "protecaoFonte", "tomadaIEC",
                                "display", "lcd", "botaoReset", "knobDisplay", "roboDisplay", "roboGrande"))]
def grupo(n):
    if n.startswith("fix_"): return "Fixadores impressos"
    for g, pre in GR:
        if n.startswith(pre): return g
    return "Outros"
J = json.load(open(f"{CX}/out/cxy.json"))
for it in J: it["grupo"] = grupo(it["nome"])
outros = sorted({it["nome"] for it in J if it["grupo"] == "Outros"})
if outros: print("sem grupo:", outros)
FJ = f"{FIN}/corexy_montagem.json"; json.dump(J, open(FJ, "w"))
# limites da maquina (cantos das caixas) p/ as cameras
import trimesh
lo = np.full(3, 1e9); hi = -lo
BB = {}
for it in J:
    if it["stl"] not in BB: BB[it["stl"]] = trimesh.load(it["stl"], process=False).bounds
    b = BB[it["stl"]]; T = np.array(it["T"])
    k = np.array([[x, y, z, 1] for x in b[:, 0] for y in b[:, 1] for z in b[:, 2]]) @ T.T
    lo = np.minimum(lo, k[:, :3].min(0)); hi = np.maximum(hi, k[:, :3].max(0))
print("limites", lo.round(1), hi.round(1), "tamanho", (hi - lo).round(1))
json.dump({"lo": lo.tolist(), "hi": hi.tolist()}, open(f"{FIN}/limites.json", "w"))
del BB; import gc; gc.collect()
# cada etapa num processo separado (RAM do WSL e curta): blend -> glb -> leve -> 3mf
etapas = sys.argv[1:] or ["blend", "glb", "leve", "3mf", "render"]
if "blend" in etapas:
    subprocess.run([BL, "-b", "--factory-startup", "-P", f"{CX}/scripts/final_blend.py", "--", FJ, FIN], env=ENV, check=True)
if "glb" in etapas:
    subprocess.run([BL, "-b", f"{FIN}/corexy_montagem.blend", "--python-expr",
                    f"import bpy; bpy.ops.export_scene.gltf(filepath='{FIN}/corexy_montagem.glb', export_format='GLB', export_apply=True, export_yup=True)"], env=ENV, check=True)
if "leve" in etapas:
    for saida in ("corexy_montagem_leve.glb", "corexy_montagem_leve.blend"):
        subprocess.run([BL, "-b", f"{FIN}/corexy_montagem.blend", "-P", f"{CX}/scripts/glb_leve.py", "--", f"{FIN}/{saida}"], env=ENV, check=True)
if "3mf" in etapas:
    subprocess.run([sys.executable, f"{CX}/scripts/exporta_3mf_stream.py", FJ, f"{FIN}/corexy_montagem.3mf"], check=True)
if "render" in etapas:
    subprocess.run([BL, "-b", f"{FIN}/corexy_montagem.blend", "-P", f"{CX}/scripts/render_final.py", "--",
                    f"{FIN}/render", "CYCLES", "64", "1600", f"{FIN}/limites.json"], env=ENV, check=True)
