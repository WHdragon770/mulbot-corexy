# blender -b -P render_asm.py -- montagem.json outdir [vistas] [res]
import bpy, sys, json, math, os
from mathutils import Matrix, Vector
a = sys.argv[sys.argv.index("--")+1:]
J = json.load(open(a[0])); out = a[1]; os.makedirs(out, exist_ok=True)
vistas = a[2].split(",") if len(a) > 2 else ["iso"]
res = int(a[3]) if len(a) > 3 else 1400
bpy.ops.wm.read_factory_settings(use_empty=True)
sc = bpy.context.scene
sc.render.engine = 'BLENDER_WORKBENCH'
sh = sc.display.shading
sh.light = 'STUDIO'; sh.color_type = 'MATERIAL'; sh.show_cavity = True; sh.show_object_outline = True
sh.show_shadows = False
sc.render.resolution_x = res; sc.render.resolution_y = int(res*0.8)
CORES = {"cinza": (0.78,0.79,0.8,1), "verm": (0.72,0.08,0.07,1), "azul": (0.05,0.35,0.48,1),
         "preto": (0.06,0.06,0.07,1), "aco": (0.6,0.62,0.65,1), "vidro": (0.7,0.85,0.85,0.25),
         "alu": (0.82,0.83,0.85,1), "pcb": (0.05,0.3,0.12,1), "lcd": (0.55,0.6,0.85,1), "latao": (0.8,0.65,0.2,1),
         "tpu": (0.72,0.08,0.07,1), "branco": (0.93,0.93,0.93,1)}
mats = {}
for k, c in CORES.items():
    m = bpy.data.materials.new(k); m.diffuse_color = c; mats[k] = m
cache = {}
objs = []
for it in J:
    f = it["stl"]
    if f not in cache:
        bpy.ops.wm.stl_import(filepath=f); o = bpy.context.selected_objects[0]
        cache[f] = o.data; bpy.data.objects.remove(o)
    o = bpy.data.objects.new(it["nome"], cache[f]); sc.collection.objects.link(o)
    o.matrix_world = Matrix(it["T"]); o.data.materials.clear() if False else None
    o.active_material = None
    o.material_slots and None
    # material por objeto
    if not o.material_slots:
        o.data.materials.append(None)
    o.material_slots[0].link = 'OBJECT'; o.material_slots[0].material = mats[it["cor"]]
    o.color = CORES[it["cor"]]
    objs.append(o)
if "vidro" in [it["cor"] for it in J]:
    sh.show_xray = False
mn = Vector((min(min((o.matrix_world @ Vector(c))[i] for c in o.bound_box) for o in objs) for i in range(3)))
mx = Vector((max(max((o.matrix_world @ Vector(c))[i] for c in o.bound_box) for o in objs) for i in range(3)))
ctr = (mn+mx)/2; R = (mx-mn).length
cam = bpy.data.objects.new("cam", bpy.data.cameras.new("cam")); sc.collection.objects.link(cam); sc.camera = cam
cam.data.clip_end = R*20
V = {"iso": (1.0,-1.25,0.85), "iso2": (-1.1,-1.2,0.8), "isot": (0.9,1.1,0.8), "frente": (0,-1,0.0001), "lado": (1,0,0.0001),
     "topo": (0.0,-0.02,1), "tras": (0,1,0.0001), "baixo": (0.3,-0.4,-1), "isoE": (-1.2,-0.9,0.6)}
for v in vistas:
    nome = v
    if ":" in v:  # nome:dx,dy,dz:cx,cy,cz:escala
        nome, d, c, s = v.split(":"); d = Vector([float(x) for x in d.split("/")]); cc = Vector([float(x) for x in c.split("/")]); esc = float(s)
    else:
        d = Vector(V[v]); cc = ctr; esc = R*1.0
    cam.data.type = 'ORTHO'; cam.data.ortho_scale = esc
    cam.location = cc + d.normalized()*R*3
    cam.rotation_euler = (cc - cam.location).to_track_quat('-Z', 'Y').to_euler()
    sc.render.filepath = f"{out}/{nome}.png"; bpy.ops.render.render(write_still=True)
