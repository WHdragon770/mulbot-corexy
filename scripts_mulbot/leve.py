# blender -b montagem.blend -P leve.py -- saida.glb
import bpy, sys
out = sys.argv[sys.argv.index("--")+1:][0]
for o in list(bpy.data.objects):
    if o.type == 'MESH': o.modifiers.clear()
done = {}
for m in list(bpy.data.meshes):
    n = len(m.polygons)
    if n <= 15000 or m.users == 0: continue
    users = [o for o in bpy.data.objects if o.type == 'MESH' and o.data == m]
    nm = m.copy(); tmp = bpy.data.objects.new("tmp", nm); bpy.context.scene.collection.objects.link(tmp)
    md = tmp.modifiers.new("d", 'DECIMATE'); md.ratio = max(0.06, 15000/n)
    bpy.context.view_layer.objects.active = tmp
    for o in bpy.context.view_layer.objects: o.select_set(False)
    tmp.select_set(True)
    bpy.ops.object.modifier_apply(modifier="d")
    for o in users: o.data = nm
    bpy.data.objects.remove(tmp)
bpy.ops.export_scene.gltf(filepath=out, export_format='GLB', export_apply=False, export_yup=True)
print("OK leve")
