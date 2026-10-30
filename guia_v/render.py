# blender -b -P render.py -- stl_dir out_dir
import bpy, sys, os
from mathutils import Vector
a = sys.argv[sys.argv.index("--") + 1:]; src, out = a
bpy.ops.wm.read_factory_settings(use_empty=True)
sc = bpy.context.scene; sc.render.engine = 'BLENDER_WORKBENCH'; sh = sc.display.shading
sh.light = 'STUDIO'; sh.color_type = 'OBJECT'; sh.show_cavity = True; sh.cavity_type = 'BOTH'; sh.show_object_outline = True
sc.world = bpy.data.worlds.new("w"); sc.world.color = (0.05, 0.065, 0.085)
sc.render.resolution_x, sc.render.resolution_y = 1100, 1000; sc.display.render_aa = '8'
sc.view_settings.view_transform = 'Standard'
COR = {"poste": (0.62, 0.64, 0.67, 1), "placa": (0.07, 0.27, 0.42, 1), "roldana": (0.75, 0.1, 0.1, 1), "rolamento": (0.85, 0.86, 0.88, 1),
       "bucha": (0.95, 0.72, 0.1, 1), "parafuso": (0.15, 0.15, 0.17, 1), "porca": (0.3, 0.3, 0.32, 1), "espacador": (0.07, 0.27, 0.42, 1)}
cam = bpy.data.objects.new("cam", bpy.data.cameras.new("cam")); sc.collection.objects.link(cam); sc.camera = cam
cam.data.clip_start = 1; cam.data.clip_end = 10000
def carrega(pref, fora=()):
    for o in list(bpy.data.objects):
        if o.type == 'MESH': bpy.data.objects.remove(o)
    for g, c in COR.items():
        p = f"{src}/{pref}_{g}.stl"
        if g in fora or not os.path.exists(p): continue
        bpy.ops.wm.stl_import(filepath=p); o = bpy.context.selected_objects[0]; o.color = c
def shot(nome, loc, alvo, lens=50, orto=None):
    cam.location = Vector(loc); cam.rotation_euler = (Vector(alvo) - cam.location).to_track_quat('-Z', 'Y').to_euler()
    cam.data.type = 'ORTHO' if orto else 'PERSP'; cam.data.lens = lens
    if orto: cam.data.ortho_scale = orto
    sc.render.filepath = f"{out}/{nome}.png"; bpy.ops.render.render(write_still=True)
carrega("mont"); shot("1_montado", (-260, -330, 230), (0, 10, 110), 50)
shot("2_atras", (300, 260, 170), (0, 10, 110), 50)
carrega("exp"); shot("3_explodido", (-400, -330, 240), (0, -95, 108), 62)
carrega("corte"); shot("4_corte_topo", (0, -15, 600), (0, -15, 110), orto=110)
carrega("mont", ("placa", "bucha", "parafuso", "espacador")); shot("5_sem_placa", (-230, -170, 250), (0, 0, 115), 55)
