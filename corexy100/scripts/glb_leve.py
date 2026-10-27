# blender -b corexy_montagem.blend -P glb_leve.py -- saida.glb|saida.blend : decima malha por malha (sem modifiers acumulados) e exporta
import bpy, sys
out = sys.argv[sys.argv.index("--")+1]
tmp = bpy.data.objects.new("tmp", None)
for me in list(bpy.data.meshes):
    n = len(me.polygons)
    if n <= 20000: continue
    o = bpy.data.objects.new("tmp_dec", me); bpy.context.scene.collection.objects.link(o)
    md = o.modifiers.new("dec", 'DECIMATE'); md.ratio = max(0.08, 20000 / n)
    dg = bpy.context.evaluated_depsgraph_get()
    novo = bpy.data.meshes.new_from_object(o.evaluated_get(dg)); novo.name = me.name
    bpy.data.objects.remove(o); me.user_remap(novo); bpy.data.meshes.remove(me)
    print("dec", novo.name, n, "->", len(novo.polygons), flush=True)
if out.endswith(".blend"): bpy.ops.wm.save_as_mainfile(filepath=out, compress=True)
else: bpy.ops.export_scene.gltf(filepath=out, export_format='GLB', export_apply=False, export_yup=True)
print("OK leve", out)
