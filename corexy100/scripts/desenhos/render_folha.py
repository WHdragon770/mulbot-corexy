# blender -b --factory-startup -P render_folha.py -- itens.json vista.json saida.png
# Render tecnico (workbench, contorno, cavidade, fundo transparente) de um conjunto + ponto visivel de cada objeto
# (onde a seta do balao encosta). Grava saida.png e saida.json {objeto: [px, py, n_visiveis]}.
import bpy, sys, json, os
from mathutils import Matrix, Vector
from bpy_extras.object_utils import world_to_camera_view
a = sys.argv[sys.argv.index("--") + 1:]
ITENS = json.load(open(a[0])); V = json.load(open(a[1])); OUT = a[2]
bpy.ops.wm.read_factory_settings(use_empty=True)
sc = bpy.context.scene
sc.render.engine = 'BLENDER_WORKBENCH'
sh = sc.display.shading
sh.light = 'STUDIO'; sh.color_type = 'OBJECT'; sh.show_cavity = True; sh.cavity_type = 'BOTH'
sh.show_object_outline = True; sh.object_outline_color = (0, 0, 0); sh.show_shadows = False; sh.show_specular_highlight = True
sc.render.film_transparent = True
sc.view_settings.view_transform = 'Standard'
W, H = V.get("res", [2200, 1900]); sc.render.resolution_x = W; sc.render.resolution_y = H
CORES = {"cinza": (0.80, 0.81, 0.82, 1), "verm": (0.78, 0.10, 0.08, 1), "azul": (0.10, 0.45, 0.66, 1),
         "preto": (0.12, 0.12, 0.13, 1), "aco": (0.62, 0.64, 0.67, 1), "vidro": (0.80, 0.88, 0.86, 0.35),
         "alu": (0.84, 0.85, 0.87, 1), "pcb": (0.08, 0.40, 0.18, 1), "lcd": (0.45, 0.55, 0.85, 1),
         "latao": (0.85, 0.68, 0.22, 1), "tpu": (0.78, 0.10, 0.08, 1), "branco": (0.95, 0.95, 0.95, 1)}
cache, objs = {}, []
for it in ITENS:
    f = it["stl"]
    if f not in cache:
        bpy.ops.wm.stl_import(filepath=f); o = bpy.context.selected_objects[0]
        cache[f] = o.data; bpy.data.objects.remove(o)
    o = bpy.data.objects.new(it["nome"], cache[f]); sc.collection.objects.link(o)
    o.matrix_world = Matrix(it["T"]); o.color = CORES[it["cor"]]; objs.append(o)
dg = bpy.context.evaluated_depsgraph_get()
pts = [o.matrix_world @ Vector(c) for o in objs for c in o.bound_box]
mn = Vector([min(p[i] for p in pts) for i in range(3)]); mx = Vector([max(p[i] for p in pts) for i in range(3)])
d = Vector(V["dir"]).normalized()
cc = Vector(V["centro"]) if "centro" in V else (mn + mx) / 2
R = (mx - mn).length
cam = bpy.data.objects.new("cam", bpy.data.cameras.new("cam")); sc.collection.objects.link(cam); sc.camera = cam
cam.data.type = 'ORTHO'; cam.data.clip_end = R * 20; cam.data.sensor_fit = 'HORIZONTAL'   # ortho_scale = largura sempre
cam.location = cc + d * R * 3
cam.rotation_euler = (-d).to_track_quat('-Z', 'Y').to_euler()
# enquadra: escala ortografica pelo maior lado projetado (+ margem)
bpy.context.view_layer.update()
cam.data.ortho_scale = 1.0
bpy.context.view_layer.update()
inv = cam.matrix_world.inverted()
loc = [inv @ p for p in pts]
lx = max(p.x for p in loc) - min(p.x for p in loc); ly = max(p.y for p in loc) - min(p.y for p in loc)
cx = (max(p.x for p in loc) + min(p.x for p in loc)) / 2; cy = (max(p.y for p in loc) + min(p.y for p in loc)) / 2
asp = W / H
if "escala" in V:                     # detalhe: centro e escala dados (mm na largura)
    cam.data.ortho_scale = V["escala"]
else:
    cam.location = cam.matrix_world @ Vector((cx, cy, 0))
    cam.data.ortho_scale = max(lx, ly * asp) * V.get("margem", 1.08)
bpy.context.view_layer.update()
sc.render.filepath = OUT; bpy.ops.render.render(write_still=True)
# ponto visivel de cada objeto: vertices amostrados, raio ate a camera (ortho: direcao d) sem bater em nada
anc = {}
for o in objs:
    me = o.data; nv = len(me.vertices); passo = max(1, nv // 600)
    vis = []
    for i in range(0, nv, passo):
        p = o.matrix_world @ me.vertices[i].co
        hit, *_ = sc.ray_cast(dg, p + d * 0.05, d)
        if not hit:
            c = world_to_camera_view(sc, cam, p)
            if 0.01 < c.x < 0.99 and 0.01 < c.y < 0.99: vis.append((c.x * W, (1 - c.y) * H))
    if vis:   # todos os pontos visiveis (ate 60): a folha escolhe o mais perto da borda da silhueta
        anc[o.name] = [len(vis), [list(v) for v in vis[::max(1, len(vis) // 60)]]]
json.dump(anc, open(os.path.splitext(OUT)[0] + ".json", "w"))
