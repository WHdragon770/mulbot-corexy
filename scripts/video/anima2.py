# Video da CoreXY (v2): montagem por etapas com a camera indo em cada conjunto, closes de detalhe, presilha do vidro
# girando, passagem de cabos (quadro translucido), maquina funcionando (poses reais do cxy.py, correias trocadas a cada pose),
# vista explodida (com close das roldanas V e polias abertas) e final. Visual (fundo cinza, materiais) em visual.py.
# blender -b final/corexy_montagem_leve.blend -P anima2.py -- MODO saida_dir [f_ini f_fim]
#   MODO = cycles (720p, render final, PNG resumivel) | previa (workbench 640x360 rapido) | info (so grava a linha do tempo)
# Grava tambem out/anim/linha.json (legendas e eventos de som) pro som.py e o monta.py.
import bpy, sys, math, json, os, random, re
import numpy as np
from mathutils import Vector, Matrix
a = sys.argv[sys.argv.index("--") + 1:]
MODO, OUTD = a[0], a[1]
FPS = 24
CX = os.environ.get("CXY_DIR") or os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))   # raiz do projeto
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import visual
sc = bpy.context.scene
random.seed(7)

# ---------------- linha do tempo (quadros) ----------------
ETAPAS = [("Quadro", "Quadro (oco, com passagem de cabos)"), ("Eixo Z e mesa", "Eixo Z e mesa"),
          ("Torres e motores CoreXY", "Torres e motores A/B"), ("Trilhos Y", "Vigas Y com guia em V"),
          ("Portico", "Pórtico"), ("Carro do hotend", "Carro X e hotend"), ("Polias e correias", "Polias e correias CoreXY"),
          ("Extrusora", "Extrusora direta"), ("Eletronica e display", "Eletrônica, esteira e display")]
FIX = "Fixadores impressos"
F_A0, DUR_ET = 97, 96
F_A1 = F_A0 + DUR_ET * len(ETAPAS)            # 961  montada
F_D0 = F_A1 + 144                             # 1105 closes
DET = 120
F_CB0, DUR_CB = F_D0 + 5 * DET, 192            # 1705 passagem de cabos (quadro translucido)
F_W0 = F_CB0 + DUR_CB                         # 1897 funcionando
F_W1 = F_W0 + 240                             # 2137
F_E0, F_E1 = F_W1 + 10, F_W1 + 60             # explode / aberta
F_SUB, DUR_SUB = F_E1 + 30, 120               # close: roletes saem da roldana V, polia louca se separa
F_E2 = F_SUB + DUR_SUB + 30; F_E3 = F_E2 + 42 # segura / fecha
F_FIM = F_E3 + 143                            # 2562
sc.frame_start, sc.frame_end = 1, F_FIM
sc.render.fps = FPS

# pecas da Mulbot vem do .glb como "DL1-03-04_110 | mesa_suporteMesa": volta pro nome da montagem (cxy.json),
# senao mesa/knobs/polias nao acham as poses e ficam parados enquanto o vidro anda
for o in list(bpy.data.objects):
    if " | " in o.name: o.name = o.name.split(" | ")[-1]
objs = [o for o in bpy.data.objects if o.type == 'MESH']
visual.materiais(MODO)                         # cycles: materiais de verdade (antes das copias fantasma)
def centro(o):
    bb = [o.matrix_world @ Vector(v) for v in o.bound_box]; return sum(bb, Vector()) / 8
cent = {o.name: centro(o) for o in objs}
CHAO = -25.0                                   # onde ficava o chao: na explodida nenhuma peca desce abaixo disso
zmin = {o.name: min((o.matrix_world @ Vector(v)).z for v in o.bound_box) for o in objs}
grupo = {o.name: o.users_collection[0].name for o in objs}
grupo = {n: ("Eletronica e display" if g == "Outros" else g) for n, g in grupo.items()}   # esteira veio em "Outros" no blend da 200
C = Vector((0, 15, 280))
base = [o for o in objs if grupo[o.name] != FIX]
etapa = {}
for o in objs:
    g = grupo[o.name]
    if g == FIX: g = grupo[min(base, key=lambda b: (cent[b.name] - cent[o.name]).length).name]
    etapa[o.name] = ([e[0] for e in ETAPAS].index(g), grupo[o.name] == FIX)
L0 = {o.name: o.location.copy() for o in objs}

# ---------------- explodida fina: roletes saem da roldana V, polia louca abre em eixo / gaiola / polia ----------------
def eixo(o):                                   # direcao de menor espalhamento dos vertices = eixo de um anel
    X = np.array([(o.matrix_world @ v.co)[:] for v in o.data.vertices]); X -= X.mean(0)
    return Vector(np.linalg.eigh(X.T @ X)[1][:, 0])
SUB = {}
for o in objs:
    if o.name.endswith("_roletes"):
        ax = eixo(o); r = cent[o.name] - C
        if abs(ax.z) > 0.7: ax = ax if ax.z > 0 else -ax
        elif ax.dot(Vector((r.x, r.y, 0))) < 0: ax = -ax
        SUB[o.name] = ax * 32
LOUCAS = {}
for o in objs:
    m_ = re.match(r"(louca\w+?_[AB]_[DE])_", o.name)
    if m_: LOUCAS.setdefault(m_.group(1), []).append(o.name)
for g, ns in LOUCAS.items():
    pol = next(n for n in ns if n.endswith("poliaLouca")); ax = eixo(bpy.data.objects[next(n for n in ns if n.endswith("gaiolaLouca_0"))])
    if ax.z < 0: ax = -ax
    pr = {n: (cent[n] - cent[pol]).dot(ax) for n in ns}
    for lado in (1, -1):
        for k, n in enumerate(sorted([n for n in ns if n != pol and pr[n] * lado > 0], key=lambda n: abs(pr[n]))):
            SUB[n] = ax * lado * (16 + 14 * k)

# ---------------- poses da maquina funcionando ----------------
PZ = json.load(open(f"{CX}/out/anim/poses/poses.json"))["poses"]
PASSO = (F_W1 - F_W0 - 30) // (len(PZ) - 1)    # 15 quadros pra sair/voltar da pose padrao
def f_pose(k): return F_W0 + 15 + k * PASSO
mov = set().union(*(p["T"] for p in PZ))      # elos da esteira so mudam em parte das poses
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
EX = {}
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
    ex.z = max(ex.z, CHAO + 3 - zmin[o.name])   # explodida: nenhuma peca atravessa o chao
    EX[o.name] = ex
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
        M0 = o.matrix_world.copy(); R0 = o.rotation_euler.copy(); ib = Matrix(TB[o.name]).inverted(); r = R0
        o.keyframe_insert("rotation_euler", frame=F_W0)
        for k, p in enumerate(PZ):              # pose completa (elos da esteira giram): W = T_k . T_base^-1 . M0
            W = Matrix(p["T"].get(o.name, TB[o.name])) @ ib @ M0
            k_loc(o, f_pose(k), W.to_translation() if not o.parent else L + desloc(o.name, p["T"].get(o.name, TB[o.name])))
            if not o.parent: r = W.to_euler(o.rotation_mode if o.rotation_mode in ("XYZ", "XZY", "YXZ", "YZX", "ZXY", "ZYX") else "XYZ", r); o.rotation_euler = r; o.keyframe_insert("rotation_euler", frame=f_pose(k))
        k_loc(o, F_W1, L); o.rotation_euler = R0; o.keyframe_insert("rotation_euler", frame=F_W1)
    k_loc(o, F_E0, L); k_loc(o, F_E1, L + ex); k_loc(o, F_E2, L + ex); k_loc(o, F_E3, L)
    if o.name in SUB:                           # abre no close e fecha antes da maquina juntar
        k_loc(o, F_SUB + 20, L + ex); k_loc(o, F_SUB + 50, L + ex + SUB[o.name])
        k_loc(o, F_SUB + DUR_SUB - 30, L + ex + SUB[o.name]); k_loc(o, F_SUB + DUR_SUB, L + ex)
    if o.animation_data:
        for fc in o.animation_data.action.fcurves:
            for kp in fc.keyframe_points:
                if fc.data_path == "hide_render": kp.interpolation = 'CONSTANT'
                elif o.name in mov and F_W0 + 10 < kp.co[0] < F_W1 - 10: kp.interpolation = 'LINEAR'
                elif o.name in pres and F_P - 24 <= kp.co[0] <= F_P + DET + 16: kp.interpolation = 'LINEAR'
                else: kp.interpolation = 'BEZIER'; kp.handle_left_type = kp.handle_right_type = 'AUTO_CLAMPED'
eventos += [(f, "giro", 1.0) for f, _ in GIRO[::2]] + [(F_E0 + 5, "explode", 1.0), (F_E2 + 5, "fecha", 1.0), (F_E3, "baque", 1.0)]
eventos += [(F_SUB + 22, "chega", 1.0), (F_SUB + DUR_SUB - 28, "click", 1.0)]

# ---------------- passagem de cabos: quadro translucido e os cabos correndo do aparelho ate a RAMPS ----------------
FANT = {n for n in etapa if etapa[n][0] == 0 or n.startswith(("trilhoY_", "torre"))}
copias = {}
for n in FANT:
    for sl in bpy.data.objects[n].material_slots:
        if not sl.material: continue
        if sl.material.name not in copias: copias[sl.material.name] = visual.fantasma(sl.material)
        sl.link = 'OBJECT'; sl.material = copias[sl.material.name]
for c in copias.values():
    for f, k in ((F_CB0, 0.0), (F_CB0 + 24, 0.95), (F_W0 - 24, 0.95), (F_W0, 0.0)): visual.chave_fantasma(c, f, k)
    if c.animation_data:
        for fc in c.animation_data.action.fcurves:
            for kp in fc.keyframe_points: kp.interpolation = 'BEZIER'; kp.handle_left_type = kp.handle_right_type = 'AUTO_CLAMPED'
    if c.use_nodes and c.node_tree.animation_data:
        for fc in c.node_tree.animation_data.action.fcurves:
            for kp in fc.keyframe_points: kp.interpolation = 'BEZIER'; kp.handle_left_type = kp.handle_right_type = 'AUTO_CLAMPED'
CABOS = json.load(open(f"{CX}/out/anim/cabos/cabos.json"))
for i, cb in enumerate(CABOS):
    bpy.ops.wm.stl_import(filepath=f"{CX}/out/anim/cabos/{cb['nome']}.stl"); ob = bpy.context.selected_objects[0]
    ob.name = "cabo_" + cb["nome"]; ob.data.materials.append(visual.plastico("cabo_" + cb["nome"], cb["cor"]))
    fa = F_CB0 + 30 + 9 * i                      # cada cabo "e puxado" do aparelho ate a RAMPS (faces em ordem ao longo do tubo)
    bd = ob.modifiers.new("puxa", 'BUILD'); bd.frame_start = fa; bd.frame_duration = 60
    for f, h in ((1, True), (F_CB0, False), (F_W0, True)): ob.hide_render = h; ob.keyframe_insert("hide_render", frame=f)
    for fc in ob.animation_data.action.fcurves:
        for kp in fc.keyframe_points: kp.interpolation = 'CONSTANT'
    eventos.append((fa, "chega", 1.0))

# correias por pose (as da montagem somem enquanto a maquina anda)
mat_c = next((s.material for o in objs if o.name.startswith("correia") for s in o.material_slots if s.material), None)
for o in objs:
    if o.name.startswith(("correia", "caboEsteira")):   # cabos da esteira mudam de forma como as correias
        for f, h in ((F_W0 + 15, True), (F_W1 - 15, False)): o.hide_render = h; o.keyframe_insert("hide_render", frame=f)
        for fc in o.animation_data.action.fcurves:
            if fc.data_path == "hide_render":
                for kp in fc.keyframe_points: kp.interpolation = 'CONSTANT'
for k in range(len(PZ)):
    for c in ("correiaA", "correiaB", "caboEsteira_XY", "caboEsteira_Y"):
        bpy.ops.wm.stl_import(filepath=f"{CX}/out/anim/poses/{c}_{k:03d}.stl"); ob = bpy.context.selected_objects[0]
        ob.name = f"{c}_pose{k}"
        mt = next((sl.material for o in objs if o.name == c for sl in o.material_slots if sl.material), mat_c)
        if mt: ob.data.materials.append(mt)
        a0 = f_pose(k) - PASSO // 2 if k else F_W0 + 15; a1 = f_pose(k) + PASSO - PASSO // 2 if k < len(PZ) - 1 else F_W1 - 15
        for f, h in ((1, True), (a0, False), (a1, True)): ob.hide_render = h; ob.keyframe_insert("hide_render", frame=f)
        for fc in ob.animation_data.action.fcurves:
            for kp in fc.keyframe_points: kp.interpolation = 'CONSTANT'

# ---------------- camera: tomadas em sequencia com transicao suave ----------------
cam = bpy.data.objects.new("cam", bpy.data.cameras.new("cam")); sc.collection.objects.link(cam); sc.camera = cam
cam.data.clip_start = 2; cam.data.clip_end = 50000; cam.data.sensor_width = 36
K = 1.3                                         # 200: tomadas gerais 1000-2000 mais longe (1.0 cortava a maquina embaixo); 100: 0.75
def orbita(alvo, dist, alt, ang0, ang1, lens=40):
    if 1000 <= dist < 2000: dist, alt = dist * K, alt * K   # explodida (2300) fica igual
    def f(u):
        t = math.radians(ang0 + (ang1 - ang0) * u)
        return (Vector((alvo[0] + dist * math.sin(t), alvo[1] - dist * math.cos(t), alvo[2] + alt)), Vector(alvo), lens)
    return f
def centro_etapa(i):
    ps = [cent[n] for n in etapa if etapa[n] == (i, False)]
    return sum(ps, Vector()) / len(ps)
TOMADAS = [(1, F_A0, lambda u: (Vector((-500, -1500, 1500 - 600 * u)), Vector((0, 15, 120 + 80 * u)), 35))]
for i in range(len(ETAPAS)):
    c_ = centro_etapa(i); c_ = (c_ * 0.4 + C * 0.6)   # 200: 0.6/0.4 subia demais e cortava embaixo
    TOMADAS.append((F_A0 + i * DUR_ET, F_A0 + (i + 1) * DUR_ET, orbita(c_, 1350, 520, -40 + 38 * i, -22 + 38 * i, 40)))
def alvo_sub():                                 # roldana V e polia louca do portico direito, ja na posicao explodida
    ps = [cent[n] + EX[n] for n in ("rodaY_D0", "loucaPortico_A_D_poliaLouca")]
    return tuple((ps[0] + ps[1]) / 2)
TOMADAS += [(F_A1, F_D0, orbita(C, 1500, 600, 302, 395, 38)),
            (F_D0, F_D0 + DET, orbita((-176, 47.6, 425), 230, 30, -60, -110, 45)),  # lado E (esteira Y tapa o D)       # rodas do carro Y
            (F_D0 + DET, F_D0 + 2 * DET, orbita((0, 40, 480), 330, 90, 200, 140, 42)),              # carro X e hotend
            (F_P, F_P + DET, orbita((pino["mesa_presilha_1"].x - 4, pino["mesa_presilha_1"].y - 4, pino["mesa_presilha_1"].z + 12 - DESCE), 190, 95, 300, 330, 50)),
            (F_D0 + 3 * DET, F_D0 + 4 * DET, lambda u: (Vector((0, 20, 1650)), Vector((0, 21, 400)), 32 + 4 * u)),   # correias de cima
            (F_D0 + 4 * DET, F_CB0, orbita((-150, 250, 150), 650, 220, 150, 205, 40)),              # caixa da RAMPS e fonte
            (F_CB0, F_W0, orbita((-20, 90, 260), 1350, 430, 205, 255, 38)),                        # passagem de cabos
            (F_W0, F_W1, orbita((0, 30, 300), 1050, 380, -25, 25, 40)),                              # funcionando
            (F_W1, F_SUB, orbita(C, 2300, 900, 40, 110, 38)),                                       # explodida
            (F_SUB, F_SUB + DUR_SUB, orbita(alvo_sub(), 420, 150, 55, 85, 50)),                      # close: roldana e polia abertas
            (F_SUB + DUR_SUB, F_E3, orbita(C, 2300, 900, 120, 220, 38)),
            (F_E3, F_FIM + 1, orbita(C, 1450, 520, 220, 300, 38))]
TR = 20
TR_LONGA = {F_SUB: 30, F_SUB + DUR_SUB: 30}   # mergulho ate o close da explodida e volta
CORTE = {F_P, F_D0 + 3 * DET}                 # entra com corte seco (a transicao atravessaria pecas)
def cam_em(f):
    for j, (a0, a1, fn) in enumerate(TOMADAS):
        if a0 <= f < a1:
            u = (f - a0) / (a1 - a0); l, t, ln = fn(u)
            tr = TR_LONGA.get(a0, TR)
            if j and f - a0 < tr and a0 not in CORTE:                # mistura com o fim da tomada anterior
                s = (f - a0) / tr; s = s * s * (3 - 2 * s)
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
        (F_D0 + 4 * DET + 6, F_CB0 - 6, "Eletrônica", "RAMPS, Mega e fonte na caixa de trás"),
        (F_CB0 + 10, F_W0 - 8, "Passagem de cabos", f"{len(CABOS)} cabos por dentro do quadro oco até a caixa da RAMPS"),
        (F_W0 + 6, F_W1 - 6, "Funcionando", "X e Y pela soma das 2 correias, Z pelos 2 fusos"),
        (F_E0, F_SUB - 4, "Vista explodida", ""),
        (F_SUB + 24, F_SUB + DUR_SUB - 6, "Roldana V e polia louca", "10 roletes impressos dentro da roldana; polia com gaiola de esferas"),
        (F_SUB + DUR_SUB + 6, F_E3 - 6, "Vista explodida", ""),
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
visual.cena(sc, MODO)                            # fundo cinza liso, sem chao, luz de estudio
sc.view_settings.view_transform = 'AgX'; sc.view_settings.look = 'AgX - Medium High Contrast'
if MODO in ("cycles", "bench"):
    sc.render.engine = 'CYCLES'; cy = sc.cycles; cy.device = 'CPU'; cy.samples = int(os.environ.get("CXY_SAMPLES", 24)); cy.use_denoising = True
    DEV = os.environ.get("CYCLES_DEVICE", "CPU").upper()        # OPTIX / CUDA / HIP / ONEAPI / METAL: usa a placa de video (mesmo resultado, bem mais rapido)
    if DEV != "CPU":
        pr = bpy.context.preferences.addons["cycles"].preferences; pr.compute_device_type = DEV; pr.get_devices()
        for d in pr.devices: d.use = d.type != "CPU"
        cy.device = 'GPU'
    cy.denoiser = 'OPENIMAGEDENOISE'; cy.denoising_quality = os.environ.get("CXY_DENOISE", "HIGH"); cy.max_bounces = int(os.environ.get("CXY_BOUNCES", 4)); cy.use_auto_tile = True; cy.tile_size = int(os.environ.get("CXY_TILE", 256))
    cy.adaptive_threshold = float(os.environ.get("CXY_NOISE", cy.adaptive_threshold)); sc.render.use_persistent_data = os.environ.get("CXY_PERSIST") == "1"
    sc.render.resolution_x, sc.render.resolution_y = 1280, 720
else:
    sc.render.engine = 'BLENDER_WORKBENCH'; sh = sc.display.shading
    sh.light = 'STUDIO'; sh.color_type = 'MATERIAL'; sh.show_cavity = True; sh.show_shadows = False
    sc.display.render_aa = 'FXAA'                  # previa: 1 amostra (o padrao 8 deixava 7 s/quadro)
    sc.view_settings.view_transform = 'Standard'; sc.view_settings.look = 'None'
    sh.show_shadows = False; sc.render.film_transparent = False
    sc.render.resolution_x, sc.render.resolution_y = 640, 360
sc.render.image_settings.file_format = 'PNG'
sc.render.use_overwrite = False; sc.render.use_placeholder = True      # resumivel: pula quadro que ja existe
sc.render.filepath = f"{OUTD}/f"
if len(a) > 3: sc.frame_start, sc.frame_end = int(a[2]), int(a[3])
if MODO in ("bench", "folha"):                    # cronometra quadros soltos (QUADROS=1,200,...) com o mesmo ajuste do render final
    import time
    sc.render.use_overwrite = True
    for q in [int(x) for x in os.environ["QUADROS"].split(",")]:
        sc.frame_set(q); sc.render.filepath = f"{OUTD}/b{q:04d}.png"; t0 = time.time()
        if MODO == "folha":                  # diagnostico: onde a camera esta e dentro de que peca
            dg = bpy.context.evaluated_depsgraph_get(); cl = cam.matrix_world.translation
            den = [o.name for o in objs if not o.hide_render and o.type == 'MESH' and all(min(v[i] for v in [o.matrix_world @ Vector(b) for b in o.bound_box]) < cl[i] < max(v[i] for v in [o.matrix_world @ Vector(b) for b in o.bound_box]) for i in range(3))]
            print("CAM", q, [round(x) for x in cl], "DENTRO", den[:6], flush=True)
        bpy.ops.render.render(write_still=True); print(f"TEMPO {q} {time.time() - t0:.1f}", flush=True)
elif MODO != "info": bpy.ops.render.render(animation=True)
print("CENT", {n: [round(x) for x in cent[n]] for n in ("rodaY_D0", "rodaY_E0", "carroX", "mesa_presilha_1") if n in cent}, "PINO", [round(x) for x in pino.get("mesa_presilha_1", (0,0,0))])
print("LINHA", F_FIM, "quadros", "SUB", len(SUB), "LOUCAS", len(LOUCAS), "FANT", len(FANT), "ALVO", [round(x) for x in alvo_sub()])
