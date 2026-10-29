# Vista tecnica ortografica + pontos medidos projetados (pra ficha_monta.py desenhar cotas).
# blender -b <leve.blend> -P ficha_render.py -- <frente|lado|topo|iso> <saida.png> <area mm>
import bpy, sys, math, json
from mathutils import Vector
from bpy_extras.object_utils import world_to_camera_view
vista, out, area = sys.argv[sys.argv.index("--") + 1:][:3]; area = float(area)
sc = bpy.context.scene; RX, RY = 1700, 1500
sc.render.resolution_x, sc.render.resolution_y, sc.render.resolution_percentage = RX, RY, 100
sc.render.engine = 'CYCLES'; sc.cycles.device = 'CPU'; sc.cycles.samples = 48; sc.cycles.use_denoising = True
sc.cycles.max_bounces = 4; sc.render.film_transparent = True
sc.view_settings.view_transform = 'Standard'; sc.view_settings.look = 'None'
w = bpy.data.worlds.new("w"); sc.world = w; w.use_nodes = True
bg = w.node_tree.nodes["Background"]; bg.inputs[0].default_value = (0.85, 0.88, 0.92, 1); bg.inputs[1].default_value = 0.9
for rot, e in (((50, 10, -35), 3.0), ((60, -10, 140), 1.2)):
    l = bpy.data.lights.new("s", 'SUN'); l.energy = e; l.angle = 0.2
    o = bpy.data.objects.new("s", l); sc.collection.objects.link(o); o.rotation_euler = [math.radians(x) for x in rot]
lo = Vector((1e9,) * 3); hi = -lo
for o in bpy.data.objects:
    if o.type != 'MESH' or o.hide_render: continue
    for c in o.bound_box:
        p = o.matrix_world @ Vector(c); lo = Vector(map(min, lo, p)); hi = Vector(map(max, hi, p))
vb = [bpy.data.objects["mesa_vidro"].matrix_world @ Vector(c) for c in bpy.data.objects["mesa_vidro"].bound_box]
vlo = Vector([min(p[i] for p in vb) for i in range(3)]); vhi = Vector([max(p[i] for p in vb) for i in range(3)])
gc = (vlo + vhi) / 2; zt = vhi.z                   # centro e topo do vidro (mesa no alto = inicio da impressao)
plo = Vector((gc.x - area / 2, gc.y - area / 2, zt - area)); phi = Vector((gc.x + area / 2, gc.y + area / 2, zt))  # volume varrido pela peca
c = (lo + hi) / 2; d = hi - lo
D = {"frente": Vector((0, -1, 0)), "lado": Vector((1, 0, 0)), "topo": Vector((0, 0, 1)), "iso": Vector((1, -1.15, 0.85)).normalized()}[vista]
cam = bpy.data.objects.new("cam", bpy.data.cameras.new("cam")); sc.collection.objects.link(cam); sc.camera = cam
cam.data.type = 'ORTHO'; cam.data.clip_end = 20000
cam.location = c + D * 3000
cam.rotation_euler = (0, 0, 0) if vista == "topo" else (-D).to_track_quat('-Z', 'Y').to_euler()
bpy.context.view_layer.update()
def px(p):
    v = world_to_camera_view(sc, cam, Vector(p)); return [v.x * RX, (1 - v.y) * RY]
cs = [Vector((x, y, z)) for x in (lo.x, hi.x) for y in (lo.y, hi.y) for z in (lo.z, hi.z)]
cam.data.ortho_scale = 1.0
pts = [px(p) for p in cs]; wx = max(p[0] for p in pts) - min(p[0] for p in pts); wy = max(p[1] for p in pts) - min(p[1] for p in pts)
cam.data.ortho_scale = max(wx / RX, wy / RY) * (1.42 if vista != "iso" else 1.18)   # folga pras cotas
bpy.context.view_layer.update()
J = {"vista": vista, "area": area, "lo": list(lo), "hi": list(hi), "plo": list(plo), "phi": list(phi), "vlo": list(vlo), "vhi": list(vhi),
     "caixa": [px(p) for p in cs], "volume": [px(Vector((x, y, z))) for x in (plo.x, phi.x) for y in (plo.y, phi.y) for z in (plo.z, phi.z)],
     "vidro": [px(Vector((x, y, vhi.z))) for x, y in ((vlo.x, vlo.y), (vhi.x, vlo.y), (vhi.x, vhi.y), (vlo.x, vhi.y))],
     "mm_px": RX / (cam.data.ortho_scale * 1)}
json.dump(J, open(out.replace(".png", ".json"), "w"))
sc.render.filepath = out; bpy.ops.render.render(write_still=True)
