# blender -b arquivo.blend -P render_final.py -- outdir engine samples res
import bpy, sys, math, os
from mathutils import Vector
a = sys.argv[sys.argv.index("--")+1:]
out, eng, spp, res = a[0], a[1], int(a[2]), int(a[3])
sc = bpy.context.scene
sc.render.resolution_x = res; sc.render.resolution_y = int(res*0.8)
if eng == "CYCLES":
    sc.render.engine = 'CYCLES'; sc.cycles.device = 'CPU'; sc.cycles.samples = spp; sc.cycles.use_denoising = True
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
bpy.ops.mesh.primitive_plane_add(size=3000, location=(0, 0, -10.0))
chao = bpy.context.active_object; m = bpy.data.materials.new("chao"); m.use_nodes = True
m.node_tree.nodes["Principled BSDF"].inputs["Base Color"].default_value = (0.55, 0.57, 0.6, 1); m.node_tree.nodes["Principled BSDF"].inputs["Roughness"].default_value = 0.6
chao.data.materials.append(m)
cam = bpy.data.objects.new("cam", bpy.data.cameras.new("cam")); sc.collection.objects.link(cam); sc.camera = cam
cam.data.lens = 50; cam.data.clip_end = 20000
V = {"heroi": ((-640, -840, 500), (0, 0, 185)), "heroi2": ((720, -800, 450), (0, 0, 185)),
     "tras": ((560, 840, 520), (0, 40, 200)), "lado": ((-1050, -100, 240), (0, 20, 200)),
     "carro_hotend": ((-160, -330, 330), (0, 15, 175)), "mesa": ((-420, -520, 420), (0, -10, 110))}
sel = a[4].split(",") if len(a) > 4 else list(V)
for k in sel:
    loc, tgt = V[k]
    cam.location = Vector(loc); cam.rotation_euler = (Vector(tgt) - cam.location).to_track_quat('-Z', 'Y').to_euler()
    cam.data.lens = 50 if k not in ("carro_hotend",) else 60
    sc.render.filepath = f"{out}/{k}.png"; bpy.ops.render.render(write_still=True)
