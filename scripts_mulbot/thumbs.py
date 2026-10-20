# blender -b -P thumbs.py -- <stl_dir> <out_dir>
import bpy, sys, os, glob, math
from mathutils import Vector
a = sys.argv[sys.argv.index("--")+1:]
src, out = a[0], a[1]
os.makedirs(out, exist_ok=True)
bpy.ops.wm.read_factory_settings(use_empty=True)
sc = bpy.context.scene
sc.render.engine = 'BLENDER_WORKBENCH'
sh = sc.display.shading
sh.light = 'STUDIO'; sh.color_type = 'SINGLE'; sh.single_color = (0.8, 0.45, 0.35)
sh.show_cavity = True; sh.show_object_outline = True
sc.render.resolution_x = sc.render.resolution_y = 420
cam = bpy.data.objects.new("cam", bpy.data.cameras.new("cam")); sc.collection.objects.link(cam); sc.camera = cam
cam.data.type = 'ORTHO'
files = sorted(glob.glob(src + "/*.stl"))
if len(a) > 2: files = [f for f in files if any(k in os.path.basename(f) for k in a[2].split(","))]
for f in files:
    name = os.path.splitext(os.path.basename(f))[0]
    bpy.ops.wm.stl_import(filepath=f)
    o = bpy.context.selected_objects[0]
    bb = [o.matrix_world @ Vector(c) for c in o.bound_box]
    mn = Vector([min(v[i] for v in bb) for i in range(3)]); mx = Vector([max(v[i] for v in bb) for i in range(3)])
    c = (mn+mx)/2; r = (mx-mn).length
    cam.data.ortho_scale = r*1.05
    views = {"iso": Vector((1,-1.2,0.9)), "top": Vector((0,0,1)), "front": Vector((0,-1,0)), "right": Vector((1,0,0)), "bot": Vector((0,0,-1)), "back": Vector((0,1,0))}
    for vn, d in views.items():
        cam.location = c + d.normalized()*r*3
        up = 'Y'
        q = (c - cam.location).to_track_quat('-Z', 'Y' if vn not in ("top","bot") else 'Y')
        if vn in ("top", "bot"):
            from mathutils import Euler
            cam.rotation_euler = Euler((0 if vn=="top" else math.pi, 0, 0))
        else:
            cam.rotation_euler = (c - cam.location).to_track_quat('-Z', 'Z').to_euler()
        cam.data.clip_end = r*10
        sc.render.filepath = f"{out}/{name}__{vn}.png"
        bpy.ops.render.render(write_still=True)
    bpy.data.objects.remove(o)
