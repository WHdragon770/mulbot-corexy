# blender -b final/corexy_montagem_leve.blend -P scripts/glb_celular.py -- saida.glb [tris_alvo]
# versão pra celular: decima cada malha até o total da cena (contando instâncias) ficar perto do alvo
import bpy, sys
a = sys.argv[sys.argv.index("--")+1:]
out = a[0]; alvo = int(a[1]) if len(a) > 1 else 900000
def tris(me): return sum(len(p.vertices) - 2 for p in me.polygons)
usos = {}
for o in bpy.data.objects:
    if o.type == 'MESH': usos[o.data] = usos.get(o.data, 0) + 1
total = sum(tris(m) * u for m, u in usos.items())
r = min(1.0, alvo / total)
print("total", total, "ratio", round(r, 4), flush=True)
for me, u in list(usos.items()):
    n = tris(me)
    if n <= 300 or r >= 1: continue
    o = bpy.data.objects.new("tmp_dec", me); bpy.context.scene.collection.objects.link(o)
    md = o.modifiers.new("dec", 'DECIMATE'); md.ratio = max(r, 300 / n)
    dg = bpy.context.evaluated_depsgraph_get()
    novo = bpy.data.meshes.new_from_object(o.evaluated_get(dg)); novo.name = me.name
    bpy.data.objects.remove(o); me.user_remap(novo); bpy.data.meshes.remove(me)
final = sum(tris(o.data) for o in bpy.data.objects if o.type == 'MESH')
print("final", final, flush=True)
# modelo está em mm (1 unidade = 1 mm): escala 0,001 pra abrir no tamanho real (metros) no AR do celular
raiz = bpy.data.objects.new("CoreXY", None); bpy.context.scene.collection.objects.link(raiz)
for o in list(bpy.context.scene.objects):
    if o.parent is None and o is not raiz: o.parent = raiz
raiz.scale = (0.001,) * 3
bpy.ops.export_scene.gltf(filepath=out, export_format='GLB', export_apply=False, export_yup=True,
                          export_normals=True, export_texcoords=False, export_cameras=False, export_lights=False)
print("OK celular", out)
