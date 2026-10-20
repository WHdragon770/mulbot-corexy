# Video da CoreXY (v2): montagem por etapas com a camera indo em cada conjunto, closes de detalhe, presilha do vidro
# girando, maquina funcionando (poses reais do cxy.py, correias trocadas a cada pose), vista explodida e final.
# blender -b final/corexy_montagem_leve.blend -P anima2.py -- MODO saida_dir [f_ini f_fim]
#   MODO = cycles (720p, render final, PNG resumivel) | previa (workbench 640x360 rapido) | info (so grava a linha do tempo)
# Grava tambem out/anim/linha.json (legendas e eventos de som) pro som.py e o monta.py.
import bpy, sys, math, json, os, random
from mathutils import Vector, Matrix
a = sys.argv[sys.argv.index("--") + 1:]
MODO, OUTD = a[0], a[1]
FPS = 24
CX = os.environ.get("CXY_DIR") or os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))   # raiz do projeto
sc = bpy.context.scene
random.seed(7)

# ---------------- linha do tempo (quadros) ----------------
ETAPAS = [("Quadro", "Quadro (oco, com passagem de cabos)"), ("Eixo Z e mesa", "Eixo Z e mesa"),
          ("Torres e motores CoreXY", "Torres e motores A/B"), ("Trilhos Y", "Vigas Y com guia em V"),
          ("Portico", "Pórtico"), ("Carro do hotend", "Carro X e hotend"), ("Polias e correias", "Polias e correias CoreXY"),
          ("Extrusora", "Extrusora direta"), ("Eletronica e display", "Eletrônica e display")]
FIX = "Fixadores impressos"
F_A0, DUR_ET = 97, 96
F_A1 = F_A0 + DUR_ET * len(ETAPAS)            # 961  montada
F_D0 = F_A1 + 144                             # 1105 closes
DET = 120
F_W0 = F_D0 + 5 * DET                         # 1705 funcionando
F_W1 = F_W0 + 240                             # 1945
F_E0, F_E1, F_E2, F_E3 = F_W1 + 10, F_W1 + 60, F_W1 + 150, F_W1 + 192   # explode / abre / segura / fecha
F_FIM = F_E3 + 143                            # 2280
sc.frame_start, sc.frame_end = 1, F_FIM
sc.render.fps = FPS

# pecas da Mulbot vem do .glb como "DL1-03-04_110 | mesa_suporteMesa": volta pro nome da montagem (cxy.json),
# senao mesa/knobs/polias nao acham as poses e ficam parados enquanto o vidro anda
for o in list(bpy.data.objects):
    if " | " in o.name: o.name = o.name.split(" | ")[-1]
objs = [o for o in bpy.data.objects if o.type == 'MESH']
def centro(o):
    bb = [o.matrix_world @ Vector(v) for v in o.bound_box]; return sum(bb, Vector()) / 8
cent = {o.name: centro(o) for o in objs}
grupo = {o.name: o.users_collection[0].name for o in objs}
C = Vector((0, 15, 280))
base = [o for o in objs if grupo[o.name] != FIX]
etapa = {}
for o in objs:
    g = grupo[o.name]
    if g == FIX: g = grupo[min(base, key=lambda b: (cent[b.name] - cent[o.name]).length).name]
    etapa[o.name] = ([e[0] for e in ETAPAS].index(g), grupo[o.name] == FIX)
L0 = {o.name: o.location.copy() for o in objs}

# ---------------- poses da maquina funcionando ----------------
PZ = json.load(open(f"{CX}/out/anim/poses/poses.json"))["poses"]
PASSO = (F_W1 - F_W0 - 30) // (len(PZ) - 1)    # 15 quadros pra sair/voltar da pose padrao
def f_pose(k): return F_W0 + 15 + k * PASSO
mov = set(PZ[0]["T"])
TB = {j["nome"]: j["T"] for j in json.load(open(f"{CX}/out/cxy.json"))}   # pose padrao (o .blend foi exportado nela)
def desloc(n, T): return Vector(tuple(T[i][3] - TB[n][i][3] for i in range(3)))

# ---------------- presilhas: giram meia volta no close (3o detalhe) ----------------
pres = {o.name: o for o in objs if o.name.startswith("mesa_presilha_")}
pino = {}
for n in pres:
    nut = bpy.data.objects.get(n.replace("presilha_", "porcaPresilha_"))
    pino[n] = cent[nut.name] if nut else cent[n]
F_P = F_D0 + 2 * DET
DESCE = 150.0                                # mesa desce no close da presilha (no alto ela fica colada no portico)
mesa_z = {n for n in mov if all(abs(PZ[-1]["T"][n][i][3] - TB[n][i][3]) < 1e-3 for i in (0, 1)) and abs(PZ[-1]["T"][n][2][3] - TB[n][2][3]) > 1}
def zoff(f):                                  # mesma curva das chaves da mesa (Bezier com pontas planas = smoothstep)
    ss = lambda u: u * u * (3 - 2 * u)
    if F_P - 24 <= f < F_P: k = ss((f - (F_P - 24)) / 24)
    elif F_P <= f <= F_P + DET - 12: k = 1.0
    elif F_P + DET - 12 < f <= F_P + DET + 16: k = 1 - ss((f - (F_P + DET - 12)) / 28)
    else: k = 0.0
    return Vector((0, 0, -DESCE * k))
GIRO = [(F_P + 30, 0.0), (F_P + 58, 180.0), (F_P + 78, 180.0), (F_P + 104, 0.0)]

# ---------------- keyframes das pecas ----------------
eventos = []                                     # (quadro, tipo, intensidade) p/ o som
def k_loc(o, f, v): o.location = v; o.keyframe_insert("location", frame=f)
for o in objs:
    ei, fix = etapa[o.name]
    ini = F_A0 + ei * DUR_ET
    irmaos = sorted([n for n in etapa if etapa[n] == (ei, fix)], key=lambda n: (cent[n].z, cent[n].x))
    kq = irmaos.index(o.name) / max(1, len(irmaos))
    f0 = int(ini + (6 + kq * 50 if not fix else 62 + kq * 16)); f1 = f0 + (20 if not fix else 9)
    d = cent[o.name] - C; d.z = 0; d = d.normalized() if d.length > 1 else Vector((0, -1, 0))
    voo = d * (260 if not fix else 70) + Vector((0, 0, 420 if not fix else 90))
    L = L0[o.name]
    r = cent[o.name] - C; ex = Vector((r.x * 0.8, r.y * 0.8, r.z * 0.65)) * (1.35 if fix else 1)
    ex.z += {"Eixo Z e mesa": -60, "Portico": 150, "Carro do hotend": 250, "Polias e correias": 180, "Torres e motores CoreXY": 110,
             "Trilhos Y": 70, "Extrusora": 220, "Eletronica e display": -40}.get(ETAPAS[ei][0], 0)
    o.hide_render = True; o.keyframe_insert("hide_render", frame=1)
    o.hide_render = False; o.keyframe_insert("hide_render", frame=f0)
    k_loc(o, f0, L + voo); k_loc(o, f1, L)
    eventos.append((f1, "click" if fix else "chega", 1.0))
    if o.name in pres:                          # meia volta em torno do pino
        P = pino[o.name]; r0 = o.rotation_euler.z
        def ang(f):                             # angulo do giro em cada quadro (suave entre os pontos de GIRO)
            pts = [(F_P, 0.0)] + GIRO + [(F_P + DET, 0.0)]
            for (f0, g0), (f1, g1) in zip(pts, pts[1:]):
                if f0 <= f <= f1:
                    u = 0 if f1 == f0 else (f - f0) / (f1 - f0); return g0 + (g1 - g0) * u * u * (3 - 2 * u)
            return 0.0
        for f in range(F_P - 24, F_P + DET + 17):     # 1 chave por quadro: a origem fica longe do pino, entre 2 chaves ela cortaria caminho
            g = ang(f); th = math.radians(g); q = L - P
            k_loc(o, f, P + zoff(f) + Vector((q.x * math.cos(th) - q.y * math.sin(th), q.x * math.sin(th) + q.y * math.cos(th), q.z)))
            o.rotation_euler.z = r0 + th; o.keyframe_insert("rotation_euler", index=2, frame=f)
    if o.name in mesa_z and o.name not in pres:
        k_loc(o, F_P - 24, L); k_loc(o, F_P, L + zoff(F_P)); k_loc(o, F_P + DET - 12, L + zoff(F_P)); k_loc(o, F_P + DET + 16, L)
    k_loc(o, F_W0, L)
    if o.name in mov:                           # funcionando: segue as poses
        for k, p in enumerate(PZ):
            k_loc(o, f_pose(k), L + desloc(o.name, p["T"][o.name]))
        k_loc(o, F_W1, L)
    k_loc(o, F_E0, L); k_loc(o, F_E1, L + ex); k_loc(o, F_E2, L + ex); k_loc(o, F_E3, L)
    if o.animation_data:
        for fc in o.animation_data.action.fcurves:
            for kp in fc.keyframe_points:
                if fc.data_path == "hide_render": kp.interpolation = 'CONSTANT'
                elif o.name in mov and F_W0 + 10 < kp.co[0] < F_W1 - 10: kp.interpolation = 'LINEAR'
                elif o.name in pres and F_P - 24 <= kp.co[0] <= F_P + DET + 16: kp.interpolation = 'LINEAR'
                else: kp.interpolation = 'BEZIER'; kp.handle_left_type = kp.handle_right_type = 'AUTO_CLAMPED'
eventos += [(f, "giro", 1.0) for f, _ in GIRO[::2]] + [(F_E0 + 5, "explode", 1.0), (F_E2 + 5, "fecha", 1.0), (F_E3, "baque", 1.0)]

# correias por pose (as da montagem somem enquanto a maquina anda)
mat_c = next((s.material for o in objs if o.name.startswith("correia") for s in o.material_slots if s.material), None)
for o in objs:
    if o.name.startswith("correia"):
        for f, h in ((F_W0 + 15, True), (F_W1 - 15, False)): o.hide_render = h; o.keyframe_insert("hide_render", frame=f)
        for fc in o.animation_data.action.fcurves:
            if fc.data_path == "hide_render":
                for kp in fc.keyframe_points: kp.interpolation = 'CONSTANT'
for k in range(len(PZ)):
    for c in ("correiaA", "correiaB"):
        bpy.ops.wm.stl_import(filepath=f"{CX}/out/anim/poses/{c}_{k:03d}.stl"); ob = bpy.context.selected_objects[0]
        ob.name = f"{c}_pose{k}"
        if mat_c: ob.data.materials.append(mat_c)
        a0 = f_pose(k) - PASSO // 2 if k else F_W0 + 15; a1 = f_pose(k) + PASSO - PASSO // 2 if k < len(PZ) - 1 else F_W1 - 15
        for f, h in ((1, True), (a0, False), (a1, True)): ob.hide_render = h; ob.keyframe_insert("hide_render", frame=f)
        for fc in ob.animation_data.action.fcurves:
            for kp in fc.keyframe_points: kp.interpolation = 'CONSTANT'

# ---------------- camera: tomadas em sequencia com transicao suave ----------------
cam = bpy.data.objects.new("cam", bpy.data.cameras.new("cam")); sc.collection.objects.link(cam); sc.camera = cam
cam.data.clip_start = 2; cam.data.clip_end = 50000; cam.data.sensor_width = 36
def orbita(alvo, dist, alt, ang0, ang1, lens=40):
    def f(u):
        t = math.radians(ang0 + (ang1 - ang0) * u)
        return (Vector((alvo[0] + dist * math.sin(t), alvo[1] - dist * math.cos(t), alvo[2] + alt)), Vector(alvo), lens)
    return f
def centro_etapa(i):
    ps = [cent[n] for n in etapa if etapa[n] == (i, False)]
    return sum(ps, Vector()) / len(ps)
TOMADAS = [(1, F_A0, lambda u: (Vector((-500, -1500, 1500 - 600 * u)), Vector((0, 15, 120 + 80 * u)), 35))]
for i in range(len(ETAPAS)):
    c_ = centro_etapa(i); c_ = (c_ * 0.6 + C * 0.4)
    TOMADAS.append((F_A0 + i * DUR_ET, F_A0 + (i + 1) * DUR_ET, orbita(c_, 1350, 520, -40 + 38 * i, -22 + 38 * i, 40)))
TOMADAS += [(F_A1, F_D0, orbita(C, 1500, 600, 302, 395, 38)),
            (F_D0, F_D0 + DET, orbita((176, 47.6, 425), 230, 30, 60, 110, 45)),                      # rodas do carro Y
            (F_D0 + DET, F_D0 + 2 * DET, orbita((0, 40, 480), 330, 90, 200, 140, 42)),              # carro X e hotend
            (F_P, F_P + DET, orbita((pino["mesa_presilha_1"].x - 4, pino["mesa_presilha_1"].y - 4, pino["mesa_presilha_1"].z + 12 - DESCE), 190, 95, 300, 330, 50)),
            (F_D0 + 3 * DET, F_D0 + 4 * DET, lambda u: (Vector((0, 20, 1650)), Vector((0, 21, 400)), 32 + 4 * u)),   # correias de cima
            (F_D0 + 4 * DET, F_W0, orbita((-150, 250, 150), 650, 220, 150, 205, 40)),               # caixa da RAMPS e fonte
            (F_W0, F_W1, orbita((0, 30, 380), 1050, 380, -25, 25, 40)),                              # funcionando
            (F_W1, F_E3, orbita(C, 2300, 900, 40, 220, 38)),                                         # explodida
            (F_E3, F_FIM + 1, orbita(C, 1450, 520, 220, 300, 38))]
TR = 20
CORTE = {F_P, F_D0 + 3 * DET}                 # entra com corte seco (a transicao atravessaria pecas)
def cam_em(f):
    for j, (a0, a1, fn) in enumerate(TOMADAS):
        if a0 <= f < a1:
            u = (f - a0) / (a1 - a0); l, t, ln = fn(u)
            if j and f - a0 < TR and a0 not in CORTE:                # mistura com o fim da tomada anterior
                s = (f - a0) / TR; s = s * s * (3 - 2 * s)
                l0, t0, ln0 = TOMADAS[j - 1][2](1.0)
                l, t, ln = l0.lerp(l, s), t0.lerp(t, s), ln0 + (ln - ln0) * s
            return l, t, ln
    return TOMADAS[-1][2](1.0)
for f in range(1, F_FIM + 1):
    l, t, ln = cam_em(f)
    cam.location = l; cam.rotation_euler = (t - l).to_track_quat('-Z', 'Y').to_euler(); cam.data.lens = ln
    cam.keyframe_insert("location", frame=f); cam.keyframe_insert("rotation_euler", frame=f); cam.data.keyframe_insert("lens", frame=f)

# ---------------- legendas e sons (pro monta.py / som.py) ----------------
LEG = [(1, F_A0 - 6, "MULBOT COREXY 200³", "versão CoreXY da Mulbot DL1, quase toda impressa")]
LEG += [(F_A0 + i * DUR_ET + 4, F_A0 + (i + 1) * DUR_ET - 4, f"{i + 1}/{len(ETAPAS)}  {e[1]}", "") for i, e in enumerate(ETAPAS)]
LEG += [(F_A1 + 6, F_D0 - 6, "Montada", "área de impressão 200 x 200 x 200 mm"),
        (F_D0 + 6, F_D0 + DET - 6, "Guia em V impressa", "roldana de resina com 10 roletes impressos junto, 1 peça só"),
        (F_D0 + DET + 6, F_D0 + 2 * DET - 6, "Carro X", "hotend, extrusora direta, torre das correias e fim de curso numa peça"),
        (F_P + 6, F_P + DET - 6, "Presilha do vidro", "meia volta solta, meia volta trava"),
        (F_D0 + 3 * DET + 6, F_D0 + 4 * DET - 6, "CoreXY", "2 correias de 1418 mm, motores A e B parados no quadro"),
        (F_D0 + 4 * DET + 6, F_W0 - 6, "Eletrônica", "cabos passam por dentro do quadro até a caixa da RAMPS"),
        (F_W0 + 6, F_W1 - 6, "Funcionando", "X e Y pela soma das 2 correias, Z pelos 2 fusos"),
        (F_E0, F_E3 - 6, "Vista explodida", ""),
        (F_E3 + 10, F_FIM, "MULBOT COREXY 200³", "quadro, guias, fusos e parafusos impressos")]
VEL = []                                        # velocidade dos motores A, B e Z por quadro (som de passo)
for k in range(len(PZ) - 1):
    p, q = PZ[k], PZ[k + 1]; dt = PASSO / FPS
    dx, dy, dz = (q["xc"] - p["xc"]) / dt, (q["yg"] - p["yg"]) / dt, (q["zm"] - p["zm"]) / dt
    VEL.append((f_pose(k), f_pose(k + 1), dx + dy, dx - dy, dz))
eventos += [(f_pose(0) - 15, "liga", 1.0), (f_pose(len(PZ) - 1) + 15, "desliga", 1.0)]
os.makedirs(f"{CX}/out/anim", exist_ok=True)
json.dump(dict(fps=FPS, fim=F_FIM, legendas=LEG, eventos=eventos, vel=VEL, etapas=[F_A0 + i * DUR_ET for i in range(len(ETAPAS))]),
          open(f"{CX}/out/anim/linha.json", "w"))

# ---------------- cena / render ----------------
w = bpy.data.worlds.new("w"); sc.world = w; w.use_nodes = True
bg = w.node_tree.nodes["Background"]; bg.inputs[0].default_value = (0.78, 0.82, 0.86, 1); bg.inputs[1].default_value = 0.8
for rot, en in (((50, 10, -35), 3.0), ((60, -10, 140), 1.2)):
    lz = bpy.data.lights.new("s", 'SUN'); lz.energy = en; lz.angle = math.radians(3)
    ob = bpy.data.objects.new("s", lz); sc.collection.objects.link(ob); ob.rotation_euler = [math.radians(x) for x in rot]
bpy.ops.mesh.primitive_plane_add(size=8000, location=(0, 15, -25))
ch = bpy.context.active_object; m = bpy.data.materials.new("chao"); m.use_nodes = True
p_ = m.node_tree.nodes["Principled BSDF"]; p_.inputs["Base Color"].default_value = (0.55, 0.57, 0.6, 1); p_.inputs["Roughness"].default_value = 0.35
ch.data.materials.append(m)
sc.view_settings.view_transform = 'AgX'; sc.view_settings.look = 'AgX - Medium High Contrast'
if MODO in ("cycles", "bench"):
    sc.render.engine = 'CYCLES'; cy = sc.cycles; cy.device = 'CPU'; cy.samples = 24; cy.use_denoising = True
    DEV = os.environ.get("CYCLES_DEVICE", "CPU").upper()        # OPTIX / CUDA / HIP / ONEAPI / METAL: usa a placa de video (mesmo resultado, bem mais rapido)
    if DEV != "CPU":
        pr = bpy.context.preferences.addons["cycles"].preferences; pr.compute_device_type = DEV; pr.get_devices()
        for d in pr.devices: d.use = d.type != "CPU"
        cy.device = 'GPU'
    cy.denoiser = 'OPENIMAGEDENOISE'; cy.max_bounces = 4; cy.use_auto_tile = True; cy.tile_size = 256
    sc.render.resolution_x, sc.render.resolution_y = 1280, 720
else:
    sc.render.engine = 'BLENDER_WORKBENCH'; sh = sc.display.shading
    sh.light = 'STUDIO'; sh.color_type = 'MATERIAL'; sh.show_cavity = True; sh.show_shadows = False
    sc.display.render_aa = 'FXAA'                  # previa: 1 amostra (o padrao 8 deixava 7 s/quadro)
    sc.view_settings.view_transform = 'Standard'; sc.view_settings.look = 'None'
    sc.render.resolution_x, sc.render.resolution_y = 640, 360
sc.render.image_settings.file_format = 'PNG'
sc.render.use_overwrite = False; sc.render.use_placeholder = True      # resumivel: pula quadro que ja existe
sc.render.filepath = f"{OUTD}/f"
if len(a) > 3: sc.frame_start, sc.frame_end = int(a[2]), int(a[3])
if MODO == "bench":                      # cronometra quadros soltos (QUADROS=1,200,...) com o mesmo ajuste do render final
    import time
    sc.render.use_overwrite = True
    for q in [int(x) for x in os.environ["QUADROS"].split(",")]:
        sc.frame_set(q); sc.render.filepath = f"{OUTD}/b{q:04d}.png"; t0 = time.time()
        bpy.ops.render.render(write_still=True); print(f"TEMPO {q} {time.time() - t0:.1f}", flush=True)
elif MODO != "info": bpy.ops.render.render(animation=True)
print("LINHA", F_FIM, "quadros")
