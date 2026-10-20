# blender -b arquivo.blend -P render_final.py -- outdir engine samples res
import bpy, sys, math, os
from mathutils import Vector
a = sys.argv[sys.argv.index("--")+1:]
out, eng, spp, res = a[0], a[1], int(a[2]), int(a[3])
sc = bpy.context.scene
sc.render.resolution_x = res; sc.render.resolution_y = int(res*0.8)
if eng == "CYCLES":
    sc.render.engine = 'CYCLES'; sc.cycles.device = 'CPU'; sc.cycles.samples = spp; sc.cycles.use_denoising = os.environ.get("DENOISE", "0") == "1"
    sc.cycles.use_auto_tile = True; sc.cycles.tile_size = 256
    sc.cycles.max_bounces = 4; sc.cycles.transmission_bounces = 4; sc.render.film_transparent = False
else:
    sc.render.engine = 'BLENDER_WORKBENCH'; sh = sc.display.shading
    sh.light = 'STUDIO'; sh.color_type = 'MATERIAL'; sh.show_cavity = True; sh.show_object_outline = True; sh.show_shadows = True
sc.view_settings.view_transform = 'Standard'; sc.view_settings.look = 'None'
# mundo
w = bpy.data.worlds.new("w"); sc.world = w; w.use_nodes = True
bg = w.node_tree.nodes["Background"]; bg.inputs[0].default_value = (0.78, 0.82, 0.86, 1); bg.inputs[1].default_value = 0.8
# luzes
def sun(rot, e):
    l = bpy.data.lights.new("s", 'SUN'); l.energy = e; l.angle = 0.2
    o = bpy.data.objects.new("s", l); sc.collection.objects.link(o); o.rotation_euler = [math.radians(x) for x in rot]
sun((50, 10, -35), 3.0); sun((60, -10, 140), 1.2)
# chao
import json
LIM = json.load(open(a[4])); lo, hi = Vector(LIM["lo"]), Vector(LIM["hi"]); c = (lo + hi) / 2; H = hi.z - lo.z
bpy.ops.mesh.primitive_plane_add(size=4000, location=(c.x, c.y, lo.z))
chao = bpy.context.active_object; m = bpy.data.materials.new("chao"); m.use_nodes = True
m.node_tree.nodes["Principled BSDF"].inputs["Base Color"].default_value = (0.55, 0.57, 0.6, 1); m.node_tree.nodes["Principled BSDF"].inputs["Roughness"].default_value = 0.6
chao.data.materials.append(m)
cam = bpy.data.objects.new("cam", bpy.data.cameras.new("cam")); sc.collection.objects.link(cam); sc.camera = cam
cam.data.lens = 50; cam.data.clip_end = 20000
k_ = H / 400.0                                       # escala em relacao a Mulbot (~400 mm de altura)
def P(x, y, z): return (c.x + x * k_, c.y + y * k_, lo.z + z * k_)
ZB_ = lo.z + 0.47 * H
V = {"heroi": (P(-640, -840, 700), (c.x, c.y, ZB_)), "heroi2": (P(720, -800, 650), (c.x, c.y, ZB_)),
     "tras": (P(560, 840, 720), (c.x, c.y + 20, ZB_)), "lado": (P(-1050, -100, 420), (c.x, c.y, ZB_)),
     "topo": (P(0, -150, 1250), (c.x, c.y, lo.z + 0.8 * H)),
     "carro_hotend": ((240, -350, 690), (0, 0, 475)), "carro_rodas": ((-230, 340, 640), (0, 40, 470)), "mesa": (P(-420, -560, 520), (c.x, c.y - 10, lo.z + 0.62 * H))}
sel = a[5].split(",") if len(a) > 5 else list(V)
for k in sel:
    loc, tgt = V[k]
    cam.location = Vector(loc); cam.rotation_euler = (Vector(tgt) - cam.location).to_track_quat('-Z', 'Y').to_euler()
    cam.data.lens = 50 if k not in ("carro_hotend", "carro_rodas") else 42
    sc.render.filepath = f"{out}/{k}.png"; bpy.ops.render.render(write_still=True)
