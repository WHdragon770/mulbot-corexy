# Fotos da CoreXY 100 ao lado da 200 (mesma escala): abre o _leve.blend da 100, anexa todos os objetos do _leve.blend da 200
# deslocados em +X e renderiza 3 vistas (heroi em perspectiva, frente e topo ortogonais).
# blender_gpu -b corexy100/final/corexy_montagem_leve.blend -P lado_a_lado.py -- <blend_200> <saida> [EEVEE|CYCLES] [res]
import bpy, sys, math, os
from mathutils import Vector
a = sys.argv[sys.argv.index("--") + 1:]
B200, OUT = a[0], a[1]; ENG = a[2] if len(a) > 2 else "EEVEE"; RES = int(a[3]) if len(a) > 3 else 2000
os.makedirs(OUT, exist_ok=True)
sc = bpy.context.scene
LO1, HI1 = Vector((-169.5, -256.0, -24.9)), Vector((198.0, 273.7, 483.4))     # final/limites.json da 100
LO2, HI2 = Vector((-219.5, -293.0, -24.9)), Vector((248.0, 323.7, 583.4))     # e da 200
VAO = 160                                                                    # vao entre as duas (mm)
DX = HI1.x - LO2.x + VAO
DY = (LO1.y - LO2.y)                                                         # frentes alinhadas

antes = set(bpy.data.objects)
with bpy.data.libraries.load(B200, link=False) as (src, dst):
    dst.objects = list(src.objects)
col = bpy.data.collections.new("CoreXY200"); sc.collection.children.link(col)
for o in dst.objects:
    if o is None or o.type in ('CAMERA', 'LIGHT'): continue
    col.objects.link(o)
    if o.parent is None: o.location += Vector((DX, DY, 0))
for o in list(sc.objects):
    if o.type in ('CAMERA', 'LIGHT'): bpy.data.objects.remove(o)

sc.render.resolution_x = RES; sc.render.resolution_y = int(RES * 0.56)
if ENG == "CYCLES":
    sc.render.engine = 'CYCLES'; sc.cycles.samples = 64; sc.cycles.use_denoising = True
else:
    sc.render.engine = 'BLENDER_EEVEE' if bpy.app.version >= (5, 0) else 'BLENDER_EEVEE_NEXT'
    sc.eevee.taa_render_samples = 64
    try: sc.eevee.use_raytracing = True
    except Exception: pass
sc.view_settings.view_transform = 'AgX' if 'AgX' in [i.identifier for i in sc.view_settings.bl_rna.properties['view_transform'].enum_items] else 'Standard'
w = bpy.data.worlds.new("w"); sc.world = w; w.use_nodes = True
bg = w.node_tree.nodes["Background"]; bg.inputs[0].default_value = (0.78, 0.82, 0.86, 1); bg.inputs[1].default_value = 0.8
def sun(rot, e):
    l = bpy.data.lights.new("s", 'SUN'); l.energy = e; l.angle = 0.2
    o = bpy.data.objects.new("s", l); sc.collection.objects.link(o); o.rotation_euler = [math.radians(x) for x in rot]
sun((50, 10, -35), 3.0); sun((60, -10, 140), 1.2)
bpy.ops.mesh.primitive_plane_add(size=30000, location=(0, 0, LO1.z))
m = bpy.data.materials.new("chao"); m.use_nodes = True
p = m.node_tree.nodes["Principled BSDF"]; p.inputs["Base Color"].default_value = (0.55, 0.57, 0.6, 1); p.inputs["Roughness"].default_value = 0.6
bpy.context.active_object.data.materials.append(m)

lo = Vector((LO1.x, min(LO1.y, LO2.y + DY), LO1.z)); hi = Vector((HI2.x + DX, max(HI1.y, HI2.y + DY), HI2.z))
c = (lo + hi) / 2; L = hi.x - lo.x
cam = bpy.data.objects.new("cam", bpy.data.cameras.new("cam")); sc.collection.objects.link(cam); sc.camera = cam
cam.data.clip_end = 30000
V = {"heroi": ('PERSP', Vector((c.x - 700, lo.y - 1700, hi.z + 650)), Vector((c.x, c.y, lo.z + 300)), 38),
     "frente": ('ORTHO', Vector((c.x, lo.y - 3000, lo.z + (hi.z - lo.z) * 0.62)), Vector((c.x, c.y, lo.z + (hi.z - lo.z) * 0.62)), L * 1.4),
     "topo": ('ORTHO', Vector((c.x, c.y + 60, hi.z + 3000)), Vector((c.x, c.y + 60.01, lo.z)), L * 1.4)}
for k, (tp, loc, tgt, v) in V.items():
    cam.data.type = tp
    if tp == 'ORTHO': cam.data.ortho_scale = v
    else: cam.data.lens = v
    cam.location = loc; cam.rotation_euler = (tgt - loc).to_track_quat('-Z', 'Y').to_euler()
    sc.render.filepath = f"{OUT}/{k}.png"; bpy.ops.render.render(write_still=True)
    print("FOTO", k, flush=True)
