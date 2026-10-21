# blender -b -P render_caixa.py -- cxy.json outdir lo hi "nome:cx/cy/cz:ax/ay/az:lente;..." : close das pecas dentro de uma caixa
import bpy, sys, json, numpy as np
from mathutils import Vector, Matrix
a = sys.argv[sys.argv.index("--") + 1:]; J = json.load(open(a[0])); out = a[1]
CORES = {"cinza": (0.78, 0.79, 0.8, 1), "verm": (0.72, 0.08, 0.07, 1), "azul": (0.05, 0.35, 0.48, 1), "preto": (0.06, 0.06, 0.07, 1),
         "aco": (0.6, 0.62, 0.65, 1), "vidro": (0.7, 0.85, 0.85, 0.25), "alu": (0.82, 0.83, 0.85, 1), "pcb": (0.05, 0.3, 0.12, 1),
         "lcd": (0.55, 0.6, 0.85, 1), "latao": (0.95, 0.72, 0.1, 1)}
bpy.ops.wm.read_factory_settings(use_empty=True)
sc = bpy.context.scene; sc.render.engine = 'BLENDER_WORKBENCH'; sh = sc.display.shading
sh.light = 'STUDIO'; sh.color_type = 'OBJECT'; sh.show_cavity = True; sh.cavity_type = 'BOTH'; sh.show_object_outline = True
sc.world = bpy.data.worlds.new("w"); sc.world.color = (0.05, 0.065, 0.085); sc.display.render_aa = '8'
sc.render.resolution_x, sc.render.resolution_y = 1400, 1100; sc.view_settings.view_transform = 'Standard'
LO, HI = np.array([float(v) for v in a[2].split(",")]), np.array([float(v) for v in a[3].split(",")])
cache = {}
for e in J:
    if e["nome"].startswith("esfera"): continue
    if e["stl"] not in cache:
        bpy.ops.wm.stl_import(filepath=e["stl"]); o = bpy.context.selected_objects[0]; cache[e["stl"]] = o.data
        bpy.data.objects.remove(o)
    me = cache[e["stl"]]; T = Matrix(e["T"])
    n_ = len(me.vertices); bb = [T @ Vector(me.vertices[i].co) for i in range(0, n_, max(1, n_ // 200))]
    if not bb: continue
    c = np.array([[p.x, p.y, p.z] for p in bb]); lo, hi = c.min(0), c.max(0)
    if np.any(hi < LO) or np.any(lo > HI): continue
    o = bpy.data.objects.new(e["nome"], me); o.matrix_world = T; o.color = CORES.get(e["cor"], (0.5, 0.5, 0.5, 1)); sc.collection.objects.link(o)
cam = bpy.data.objects.new("cam", bpy.data.cameras.new("cam")); sc.collection.objects.link(cam); sc.camera = cam
cam.data.clip_start = 1; cam.data.clip_end = 10000
def shot(nome, loc, alvo, lens=50):
    cam.location = Vector(loc); cam.rotation_euler = (Vector(alvo) - cam.location).to_track_quat('-Z', 'Y').to_euler(); cam.data.lens = lens
    sc.render.filepath = f"{out}/{nome}.png"; bpy.ops.render.render(write_still=True)
for s in a[4].split(";"):
    n, loc, alvo, lens = s.split(":")
    shot(n, [float(v) for v in loc.split("/")], [float(v) for v in alvo.split("/")], float(lens))
