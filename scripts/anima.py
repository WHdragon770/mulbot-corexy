# blender -b corexy_montagem_leve.blend -P anima.py -- saida.mp4 [res_x] [frame_ini frame_fim] [png_dir]
# Animacao: montagem por etapas (pecas voam ate o lugar) + vista explodida, camera orbitando. Workbench (rapido, sem GPU).
import bpy, sys, math, os
from mathutils import Vector

a = sys.argv[sys.argv.index("--") + 1:]
OUT = a[0]; RX = int(a[1]) if len(a) > 1 else 1280
sc = bpy.context.scene
FPS = 30

ETAPAS = [("Quadro", "Quadro"), ("Eixo Z e mesa", "Eixo Z e mesa"), ("Torres e motores CoreXY", "Torres e motores CoreXY"),
          ("Trilhos Y", "Trilhos Y"), ("Portico", "Pórtico"), ("Carro do hotend", "Carro do hotend"),
          ("Polias e correias", "Polias e correias"), ("Extrusora", "Extrusora"), ("Eletronica e display", "Eletrônica e display")]
FIX = "Fixadores impressos"

def centro(o):
    bb = [o.matrix_world @ Vector(v) for v in o.bound_box]
    return sum(bb, Vector()) / 8

objs = [o for o in bpy.data.objects if o.type == 'MESH']
lo = Vector((min(centro(o).x for o in objs), min(centro(o).y for o in objs), min(centro(o).z for o in objs)))
C = Vector((0, 15, 300))                                  # centro aprox. da maquina (limites.json)
cent = {o.name: centro(o) for o in objs}
grupo = {o.name: o.users_collection[0].name for o in objs}

# fixadores vao na etapa da peca nao-fixador mais proxima
base = [o for o in objs if grupo[o.name] != FIX]
etapa_de = {}
for o in objs:
    g = grupo[o.name]
    if g == FIX:
        p = min(base, key=lambda b: (cent[b.name] - cent[o.name]).length)
        g = grupo[p.name]; etapa_de[o.name] = ([e[0] for e in ETAPAS].index(g), True)
    else:
        etapa_de[o.name] = ([e[0] for e in ETAPAS].index(g), False)

# ---------- linha do tempo ----------
T0 = 20                       # respiro inicial
DUR_ET = 46                   # quadros por etapa
VOO = 22                      # duracao do voo de cada peca
F_MONT = T0 + DUR_ET * len(ETAPAS)
F_HOLD = F_MONT + 45          # montada, girando
F_EXP = F_HOLD + 60           # explode
F_EXP_HOLD = F_EXP + 120      # explodida girando
F_VOLTA = F_EXP_HOLD + 50     # junta de novo
F_FIM = F_VOLTA + 40
sc.frame_start, sc.frame_end = 1, F_FIM
sc.render.fps = FPS

def ease(fc):
    for f in fc:
        for k in f.keyframe_points: k.interpolation = 'BEZIER'; k.easing = 'AUTO'

for o in objs:
    ei, fix = etapa_de[o.name]
    ini = T0 + ei * DUR_ET
    pecas = sorted([n for n in etapa_de if etapa_de[n] == (ei, fix)], key=lambda n: (cent[n].z, cent[n].x))
    k = pecas.index(o.name) / max(1, len(pecas))
    # pecas da etapa chegam nos primeiros ~55%, fixadores no fim
    f0 = int(ini + (k * 14 if not fix else 18 + k * 8))
    f1 = f0 + (VOO if not fix else 14)
    d = cent[o.name] - C; d.z = 0
    d = d.normalized() if d.length > 1 else Vector((0, -1, 0))
    voo = d * (220 if not fix else 90) + Vector((0, 0, 380 if not fix else 120))
    L = o.location.copy()
    # explodida: espalha radial a partir do centro + separa por grupo na vertical
    r = cent[o.name] - C
    ex = Vector((r.x * 0.75, r.y * 0.75, r.z * 0.6))
    if fix: ex *= 1.35
    sep_z = {"Eixo Z e mesa": -60, "Portico": 140, "Carro do hotend": 230, "Polias e correias": 170,
             "Torres e motores CoreXY": 110, "Trilhos Y": 70, "Extrusora": 200, "Eletronica e display": -40}
    ex.z += sep_z.get(grupo[o.name] if not fix else ETAPAS[ei][0], 0)

    o.hide_render = True; o.keyframe_insert("hide_render", frame=1)
    o.hide_render = False; o.keyframe_insert("hide_render", frame=f0)
    o.location = L + voo; o.keyframe_insert("location", frame=f0)
    o.location = L; o.keyframe_insert("location", frame=f1)
    o.keyframe_insert("location", frame=F_HOLD + int(k * 10))
    o.location = L + ex; o.keyframe_insert("location", frame=F_EXP)
    o.keyframe_insert("location", frame=F_EXP_HOLD)
    o.location = L; o.keyframe_insert("location", frame=F_VOLTA)
    for f in o.animation_data.action.fcurves:
        if f.data_path == "hide_render":
            for kp in f.keyframe_points: kp.interpolation = 'CONSTANT'
        else:
            for kp in f.keyframe_points: kp.interpolation = 'BEZIER'; kp.easing = 'AUTO'; kp.handle_left_type = kp.handle_right_type = 'AUTO_CLAMPED'

# ---------- camera: orbita em volta do centro ----------
cam = bpy.data.objects.new("cam", bpy.data.cameras.new("cam")); sc.collection.objects.link(cam); sc.camera = cam
cam.data.lens = 40; cam.data.clip_start = 2; cam.data.clip_end = 300000
alvo = bpy.data.objects.new("alvo", None); sc.collection.objects.link(alvo); alvo.location = C
piv = bpy.data.objects.new("piv", None); sc.collection.objects.link(piv); piv.location = C
cam.parent = piv
tr = cam.constraints.new('TRACK_TO'); tr.target = alvo; tr.track_axis = 'TRACK_NEGATIVE_Z'; tr.up_axis = 'UP_Y'
def cam_k(f, ang, dist, alt, az=None):
    a_ = math.radians(ang)
    cam.location = (math.sin(a_) * dist * -1, -math.cos(a_) * dist, alt); cam.keyframe_insert("location", frame=f)
    if az is not None: alvo.location = (C.x, C.y, az); alvo.keyframe_insert("location", frame=f)
# orbita continua; afasta na explodida
passos = [(1, -35, 1650, 750, 300), (F_MONT, 75, 1650, 800, 290), (F_HOLD, 110, 1700, 800, 290),
          (F_EXP, 160, 2900, 1000, 340), (F_EXP_HOLD, 300, 2900, 1000, 340), (F_VOLTA, 345, 1700, 800, 290), (F_FIM, 380, 1650, 750, 290)]
# keyframes intermediarios a cada 10 quadros (orbita em arco, nao em linha reta)
import bisect
fs = [p[0] for p in passos]
for f in range(1, F_FIM + 1, 5):
    i = max(0, bisect.bisect_right(fs, f) - 1); j = min(i + 1, len(passos) - 1)
    p, q = passos[i], passos[j]
    t = 0 if j == i else (f - p[0]) / (q[0] - p[0])
    s = t * t * (3 - 2 * t)
    ang = p[1] + (q[1] - p[1]) * t                     # angulo linear (orbita sem parar)
    cam_k(f, ang, *[p[n] + (q[n] - p[n]) * s for n in (2, 3, 4)])

# ---------- legenda ----------
txt = bpy.data.curves.new("leg", 'FONT'); txt.size = 0.38; txt.align_x = 'LEFT'
leg = bpy.data.objects.new("leg", txt); sc.collection.objects.link(leg); leg.parent = cam
leg.location = (-4.3, -2.35, -10)  # canto inferior esquerdo, 10 mm a frente da camera
mt = bpy.data.materials.new("txt"); mt.diffuse_color = (1, 1, 1, 1); txt.materials.append(mt)
tit = bpy.data.curves.new("tit", 'FONT'); tit.size = 0.24; tit.body = "CoreXY estilo Mulbot  ·  200 x 200 x 200 mm"
to = bpy.data.objects.new("tit", tit); sc.collection.objects.link(to); to.parent = cam; to.location = (-4.3, 2.25, -10)
to.data.materials.append(mt)
rotulos = [(T0 + i * DUR_ET, f"{i + 1}/{len(ETAPAS)}  {e[1]}") for i, e in enumerate(ETAPAS)]
rotulos += [(F_MONT, "Montada"), (F_HOLD, "Vista explodida"), (F_VOLTA - 30, "Montada")]
def muda_leg(scene, *_):
    f = scene.frame_current; b = ""
    for f0, s in rotulos:
        if f >= f0: b = s
    txt.body = b
bpy.app.handlers.frame_change_pre.append(muda_leg)

# ---------- cena / render ----------
sc.render.engine = 'BLENDER_WORKBENCH'; sh = sc.display.shading
sh.light = 'STUDIO'; sh.color_type = 'MATERIAL'; sh.show_cavity = True; sh.cavity_type = 'BOTH'
sh.show_object_outline = True; sh.show_shadows = False
w = bpy.data.worlds.new("w"); sc.world = w; w.color = (0.05, 0.065, 0.085)
sc.display.render_aa = '8'
sc.view_settings.view_transform = 'Standard'
sc.render.resolution_x = RX; sc.render.resolution_y = RX * 9 // 16; sc.render.resolution_percentage = 100
# (sem chao: plano gigante deixava um veu cinza no workbench)

if len(a) > 3:
    sc.frame_start, sc.frame_end = int(a[2]), int(a[3])
if len(a) > 4:   # quadros soltos em png (teste)
    for f in range(sc.frame_start, sc.frame_end + 1, max(1, (sc.frame_end - sc.frame_start) // 8 or 1)):
        sc.frame_set(f); sc.render.filepath = f"{a[4]}/f{f:04d}.png"; bpy.ops.render.render(write_still=True)
else:
    sc.render.image_settings.file_format = 'FFMPEG'
    sc.render.ffmpeg.format = 'MPEG4'; sc.render.ffmpeg.codec = 'H264'
    sc.render.ffmpeg.constant_rate_factor = 'HIGH'; sc.render.ffmpeg.ffmpeg_preset = 'GOOD'
    sc.render.filepath = OUT
    bpy.ops.render.render(animation=True)
print("FRAMES", F_FIM, "OK", OUT)
