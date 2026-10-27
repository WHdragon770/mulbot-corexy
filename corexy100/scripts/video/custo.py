# Roda depois do anima2.py (mesmo Blender, modo info): triangulos visiveis em cada quadro -> out/anim/custo.json
# (base da estimativa de tempo: quadro com a maquina cheia custa mais que quadro com 3 pecas)
import bpy, json, os
CX = os.environ.get("CXY_DIR") or os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))   # raiz do projeto
sc = bpy.context.scene
tri = {}
for o in bpy.data.objects:
    if o.type == 'MESH':
        me = o.data; me.calc_loop_triangles(); tri[o.name] = len(me.loop_triangles)
curvas = {}
for o in bpy.data.objects:
    if o.type == 'MESH' and o.animation_data and o.animation_data.action:
        for fc in o.animation_data.action.fcurves:
            if fc.data_path == "hide_render": curvas[o.name] = fc
out = []
for f in range(1, sc.frame_end + 1):
    s = 0
    for n, t in tri.items():
        fc = curvas.get(n)
        oculto = fc.evaluate(f) > 0.5 if fc else bpy.data.objects[n].hide_render
        if not oculto: s += t
    out.append(s)
json.dump(out, open(f"{CX}/out/anim/custo.json", "w"))
print("CUSTO", len(out), min(out), max(out))
