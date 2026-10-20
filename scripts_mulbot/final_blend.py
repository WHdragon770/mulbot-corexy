# blender -b -P final_blend.py -- montagem.json outdir
import bpy, sys, json, os, math
from mathutils import Matrix, Vector
a = sys.argv[sys.argv.index("--")+1:]
J = json.load(open(a[0])); out = a[1]; os.makedirs(out, exist_ok=True)
bpy.ops.wm.read_factory_settings(use_empty=True)
sc = bpy.context.scene; sc.unit_settings.system = 'METRIC'; sc.unit_settings.scale_length = 0.001; sc.unit_settings.length_unit = 'MILLIMETERS'
CORES = {"cinza": ((0.40,0.41,0.43), 0.45, 0), "verm": ((0.42,0.012,0.01), 0.4, 0), "azul": ((0.004,0.085,0.17), 0.4, 0),
         "preto": ((0.03,0.03,0.035), 0.5, 0), "aco": ((0.62,0.63,0.66), 0.3, 1), "vidro": ((0.85,0.95,0.95), 0.05, 0),
         "alu": ((0.80,0.81,0.83), 0.35, 1), "pcb": ((0.03,0.25,0.10), 0.5, 0), "lcd": ((0.45,0.52,0.9), 0.2, 0),
         "latao": ((0.8,0.6,0.2), 0.3, 1), "branco": ((0.92,0.92,0.92), 0.4, 0)}
mats = {}
for k, (c, r, met) in CORES.items():
    m = bpy.data.materials.new(k); m.use_nodes = True; b = m.node_tree.nodes["Principled BSDF"]
    b.inputs["Base Color"].default_value = (*c, 1); b.inputs["Roughness"].default_value = r; b.inputs["Metallic"].default_value = met
    if k == "vidro":
        b.inputs["Transmission Weight"].default_value = 0.95; b.inputs["IOR"].default_value = 1.5
        m.diffuse_color = (*c, 0.3)
    else: m.diffuse_color = (*c, 1)
    mats[k] = m
cols = {}
cache = {}
for it in J:
    g = it["grupo"]
    if g not in cols:
        cols[g] = bpy.data.collections.new(g); sc.collection.children.link(cols[g])
    f = it["stl"]
    if f not in cache:
        bpy.ops.wm.stl_import(filepath=f); o = bpy.context.selected_objects[0]
        me = o.data; me.name = it["peca"]; cache[f] = me
        for c_ in o.users_collection: c_.objects.unlink(o)
        bpy.data.objects.remove(o)
        for p in me.polygons: p.use_smooth = False
    nm = f'{it["peca"]} | {it["nome"]}' if it["peca"].startswith(("DL1", "TRANSFER")) else it["nome"]
    o = bpy.data.objects.new(nm, cache[f]); cols[g].objects.link(o)
    o.matrix_world = Matrix(it["T"])
    o.data.materials.clear() if False else None
    if not o.material_slots: o.data.materials.append(None)
    o.material_slots[0].link = 'OBJECT'; o.material_slots[0].material = mats[it["cor"]]
# auto smooth leve para pecas impressas
bpy.ops.wm.save_as_mainfile(filepath=f"{out}/mulbot_DL1_montagem.blend")
# GLB
bpy.ops.export_scene.gltf(filepath=f"{out}/mulbot_DL1_montagem.glb", export_format='GLB', export_apply=True, export_yup=True)
# versao leve (decimada) para visualizadores
for me in bpy.data.meshes:
    pass
for o in list(bpy.data.objects):
    if o.type == 'MESH' and len(o.data.polygons) > 20000 and not o.modifiers:
        md = o.modifiers.new("dec", 'DECIMATE'); md.ratio = max(0.08, 20000/len(o.data.polygons))
bpy.ops.export_scene.gltf(filepath=f"{out}/mulbot_DL1_montagem_leve.glb", export_format='GLB', export_apply=True, export_yup=True)
print("OK blend+glb")
