# Cenas extras do video da CoreXY 100 (pra renderizar em outro PC, ver RENDER_INSTRUCOES.txt da 100):
#   1) close do bico imprimindo o 3DBenchy em 8x, timelapse ate o fim (cabeca estaciona a cada quadro, como no Octolapse)
#   2) a 100 imprimindo uma peca cortada da 200 (02b) e a 200 montada com a peca acesa
#   3) a 100 e a 200 lado a lado
# blender -b final/corexy_montagem_leve.blend -P scripts/video/extras.py -- <cycles|previa|info> <pasta_quadros> [ini fim]
#   QUADROS=100,700 -> so esses quadros (teste). CXY_200 = _leve.blend da 200 (padrao: ../final/ do repo)
# Le benchy/*_caminho.npz (fatia.py), out/anim/poses, out/cxy.json. Grava out/anim/linha_extras.json (som.py/monta.py com CXY_LINHA).
import bpy, sys, os, json, math, numpy as np
from mathutils import Vector, Matrix
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__))); import visual

a = sys.argv[sys.argv.index("--") + 1:]; MODO, OUTD = a[0], a[1]
FPS = 24
CX = os.environ.get("CXY_DIR") or os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
B200 = os.environ.get("CXY_200") or os.path.join(CX, "..", "final", "corexy_montagem_leve.blend")
PECA = "baseFrente_D"                          # peca da 200 impressa na cena 2 (02b: "baseFrente_D parte 1de2")
sc = bpy.context.scene; sc.render.fps = FPS

# ---------------- linha do tempo ----------------
VEZES = 8                                      # close em 8x a velocidade real
F_B1 = 73                                      # titulo (maquina parada)
F_B2 = F_B1 + 528                              # 22 s de close em 8x
F_B3 = F_B2 + 420                              # timelapse ate o fim do Benchy (17,5 s)
F_B4 = F_B3 + 72                               # Benchy pronto, mesa desce
F_P0 = F_B4 + 48                               # peca da 200: 2 s em 8x e depois timelapse
F_P1 = F_B4 + 288                              # a 200 montada com a peca acesa (10 s)
F_P2 = F_P1 + 240                              # lado a lado (15 s)
F_FIM = F_P2 + 360
sc.frame_start, sc.frame_end = 1, F_FIM
FR = np.arange(1, F_FIM + 1)

def caminho(nome):
    z = np.load(f"{CX}/benchy/{nome}_caminho.npz"); return {k: z[k] for k in z.files}
BEN, PEC = caminho("benchy"), caminho("peca200")
def suave(u): u = np.clip(u, 0, 1); return u * u * (3 - 2 * u)

# tempo de impressao (s reais) em cada quadro: -1 = nada impresso ainda
def tempo(c, f0, f8, f1):                      # 8x de f0 a f8, timelapse de f8 a f1
    t8 = (f8 - f0) / FPS * VEZES; Tf = c["T"][-1]
    t = np.where(FR < f0, -1.0, (FR - f0) / FPS * VEZES)
    u = (FR - f8) / (f1 - f8)
    return np.where(FR >= f8, t8 + (Tf - t8) * (0.35 * np.clip(u, 0, 1) + 0.65 * suave(u)), t), t8
tB, t8B = tempo(BEN, F_B1, F_B2, F_B3)
tP, t8P = tempo(PEC, F_B4, F_P0, F_P1 - 24)

def no_tempo(c, t):                            # posicao do bico (peca) e velocidade real em t
    T, P = c["T"], c["P"].astype(float); t = np.clip(t, 0, T[-1])
    pos = np.stack([np.interp(t, T, P[:, i]) for i in range(3)], 1)
    j = np.clip(np.searchsorted(T, t), 1, len(T) - 1); dt = np.maximum(T[j] - T[j - 1], 1e-6)
    return pos, (P[j] - P[j - 1]) / dt[:, None]
pB, vB = no_tempo(BEN, tB); pP, vP = no_tempo(PEC, tP)

# ---------------- legendas e som (linha_extras.json) ----------------
def mmss(s): return f"{s / 60:.0f} min"
LEG = [(1, F_B1 - 6, "BENCHY NA COREXY 100³", "close do bico em 8x a velocidade real"),
       (F_B1 + 12, F_B1 + 150, "Close no bico, 8x a velocidade real", "camadas de 0,2 mm, filete de 0,45 mm, PLA"),
       (F_B2 + 12, F_B2 + 160, "Timelapse até o fim", f"{mmss(BEN['T'][-1])} de impressão em {(F_B3 - F_B2) / FPS:.0f} s"),
       (F_B3 + 6, F_B4 - 4, "3DBenchy pronto", "3DBenchy por Creative Tools, 3dbenchy.com (CC BY-ND 4.0)"),
       (F_B4 + 8, F_P1 - 8, "A 100 imprime as peças da 200", "peças maiores que 95 mm saem cortadas, com pino de encaixe"),
       (F_P1 + 30, F_P2 - 8, f"{PECA}: 1 das 46 peças cortadas", "no lugar dela na CoreXY 200³"),
       (F_P2 + 24, F_FIM - 6, "COREXY 100³  x  COREXY 200³", "área de impressão 100 x 100 x 100 e 200 x 200 x 200 mm")]
VEL = []
for f0, f1, v in ((F_B1, F_B2, vB), (F_B4, F_P0, vP)):
    for f in range(f0, f1): vx, vy = v[f - 1, 0], v[f - 1, 1]; VEL.append((f, f + 1, vx + vy, vx - vy, 0.0))
for f0, f1 in ((F_B2, F_B3), (F_P0, F_P1 - 24)): VEL.append((f0, f1, 0.0, 0.0, 2.0))   # timelapse: so o Z andando
ev = [(F_B1 - 4, "liga", 1.0), (F_B4 - 30, "baque", 1.0), (F_B4 + 2, "liga", 1.0), (F_P1, "explode", 1.0), (F_P2, "fecha", 1.0)]
os.makedirs(f"{CX}/out/anim", exist_ok=True)
json.dump(dict(fps=FPS, fim=F_FIM, legendas=LEG, eventos=ev, vel=VEL, etapas=[]), open(f"{CX}/out/anim/linha_extras.json", "w"))
if MODO == "info": print("LINHA", F_FIM); sys.exit(0)

# ---------------- cena: 100 (aberta) + 200 anexada ao lado ----------------
for o in list(bpy.data.objects):
    if " | " in o.name: o.name = o.name.split(" | ")[-1]
    if o.type in ('CAMERA', 'LIGHT'): bpy.data.objects.remove(o)
objs100 = [o for o in bpy.data.objects if o.type == 'MESH']
LO1, HI1 = Vector((-169.5, -256.0, -24.9)), Vector((198.0, 273.7, 483.4))     # final/limites.json da 100
LO2, HI2 = Vector((-219.5, -293.0, -24.9)), Vector((248.0, 323.7, 583.4))     # e da 200 (igual ao lado_a_lado.py)
DX, DY = HI1.x - LO2.x + 160, LO1.y - LO2.y
with bpy.data.libraries.load(B200, link=False) as (src, dst):
    dst.objects = list(src.objects)
col = bpy.data.collections.new("CoreXY200"); sc.collection.children.link(col)
objs200 = []
for o in dst.objects:
    if o is None or o.type in ('CAMERA', 'LIGHT'): continue
    col.objects.link(o); o.name = o.name.split(" | ")[-1]
    if o.parent is None: o.location += Vector((DX, DY, 0))
    if o.type == 'MESH': objs200.append(o)
    for sl in o.material_slots:                   # mesmo material da 100 (visual.materiais reconhece pelo nome)
        if sl.material and "." in sl.material.name and sl.material.name.rsplit(".", 1)[0] in bpy.data.materials:
            sl.material = bpy.data.materials[sl.material.name.rsplit(".", 1)[0]]
visual.materiais(MODO)
visual.cena(sc, MODO)
sc.view_settings.view_transform = 'AgX'; sc.view_settings.look = 'AgX - Medium High Contrast'

def anima(idb, path, idx, vals, frames=FR, interp=1):     # 1 chave por quadro, rapido (interp 0 = constante, 1 = linear)
    if idb.animation_data is None: idb.animation_data_create()
    ad = idb.animation_data
    if ad.action is None: ad.action = bpy.data.actions.new(idb.name + "_acao")
    fc = ad.action.fcurves.find(path, index=idx) or ad.action.fcurves.new(path, index=idx)
    vals = np.asarray(vals, float); frames = np.asarray(frames, float)
    if interp == 0:                                # constante: so onde muda
        k = np.r_[True, vals[1:] != vals[:-1]]; vals, frames = vals[k], frames[k]
    n = len(vals); fc.keyframe_points.add(n)
    co = np.empty(2 * n); co[0::2] = frames; co[1::2] = vals
    fc.keyframe_points.foreach_set("co", co); fc.keyframe_points.foreach_set("interpolation", [interp] * n); fc.update()

# ---------------- maquina: movimento a partir das poses (linear nas pecas rigidas, pose mais perto no resto) ----------------
PZ = json.load(open(f"{CX}/out/anim/poses/poses.json"))["poses"]
TB = {j["nome"]: j["T"] for j in json.load(open(f"{CX}/out/cxy.json"))}
DP = np.array([[p["xc"], p["yg"] - 47.63, p["zm"]] for p in PZ])          # deslocamento de cada pose (pose padrao: 0, 47.63, 0)
LIN, NL = {}, []
for n in set().union(*(p["T"] for p in PZ)):
    if n not in TB or n not in bpy.data.objects: continue
    Ts = np.array([p["T"].get(n, TB[n]) for p in PZ]); tb = np.array(TB[n])
    A_, *_ = np.linalg.lstsq(DP, Ts[:, :3, 3] - tb[:3, 3], rcond=None)
    if np.allclose(Ts[:, :3, :3], tb[:3, :3], atol=1e-4) and np.abs(DP @ A_ - (Ts[:, :3, 3] - tb[:3, 3])).max() < 0.05: LIN[n] = A_
    else: NL.append(n)
AB, AM = LIN["hotend_bico"], LIN["mesa_vidro"]
bico = bpy.data.objects["hotend_bico"]; vs = [bico.matrix_world @ v.co for v in bico.data.vertices]
zmin = min(v.z for v in vs); pt = [v for v in vs if v.z < zmin + 0.05]
TIP = sum(pt, Vector()) / len(pt)                                         # ponta do bico na pose padrao
dg = bpy.context.evaluated_depsgraph_get()
ok, hit, _, _, hob, _ = sc.ray_cast(dg, TIP - Vector((0, 0, 0.01)), Vector((0, 0, -1)))
SURF = hit.z                                                              # mesa embaixo do bico na pose padrao
print("BICO", [round(x, 2) for x in TIP], "MESA", round(SURF, 2), hob.name if hob else None, "LIN", len(LIN), "NL", len(NL), NL[:12])
IXY = np.linalg.inv(AB[:2, :2])
def maq(xy, z):                                 # ponto da peca (bico em xy, topo do filete em z) -> deslocamento (xc, yg, zm)
    d = np.zeros((len(z), 3)); d[:, :2] = np.asarray(xy) @ IXY
    d[:, 2] = (TIP.z - SURF - np.asarray(z)) / AM[2, 2]
    return d
PARK = np.array([[-38.0, -31.0]])              # cabeca estacionada na frente/esquerda (fora da peca) no timelapse
def estado():
    d = np.zeros((F_FIM, 3)); xy = np.zeros((F_FIM, 2)); z = np.zeros(F_FIM)
    for i, f in enumerate(FR):
        if f < F_B4:   p, t8f, f8, fim = pB[i], F_B2, F_B2, F_B3
        else:          p, t8f, f8, fim = pP[i], F_P0, F_P0, F_P1 - 24
        k = suave((f - f8) / 12)                 # vai estacionar em 0,5 s
        xy[i] = p[:2] * (1 - k) + PARK[0] * k; z[i] = p[2]
        if fim <= f < (F_B4 if f < F_B4 else F_P1): z[i] = p[2] - 40 * suave((f - fim) / 36)     # acabou: mesa desce 40 mm
        if f >= F_P1: xy[i] = PARK[0]; z[i] = -40.0
    return maq(xy, z)
DF = estado()
for n, A_ in LIN.items():
    o = bpy.data.objects[n]; L0 = np.array(o.location); W = L0 + DF @ A_
    for i in range(3): anima(o, "location", i, W[:, i])
w = np.array([1.0, 1.0, 0.15])                 # pose mais perto (elos da esteira, correias, cabos)
KP = np.argmin((((DF[:, None, :] - DP[None]) * w) ** 2).sum(2), 1)
for n in NL:
    o = bpy.data.objects[n]; M0 = o.matrix_world.copy(); ib = Matrix(TB[n]).inverted(); r = o.rotation_euler.copy()
    loc, rot = [], []
    for k in KP:
        Wm = Matrix(PZ[k]["T"].get(n, TB[n])) @ ib @ M0
        loc.append(Wm.to_translation()); r = Wm.to_euler(o.rotation_mode if len(o.rotation_mode) == 3 else "XYZ", r); rot.append(r.copy())
    for i in range(3): anima(o, "location", i, [v[i] for v in loc], interp=0); anima(o, "rotation_euler", i, [v[i] for v in rot], interp=0)
esc100 = (FR >= F_P1) & (FR < F_P2)            # a 100 some no close da 200
mat_c = next((s.material for o in objs100 if o.name.startswith("correia") for s in o.material_slots if s.material), None)
for o in objs100:
    if o.name.startswith(("correia", "caboEsteira")): o.hide_render = True; o.hide_viewport = True; continue
    anima(o, "hide_render", 0, esc100.astype(float), interp=0)
for k in sorted(set(KP)):
    vis = (KP == k) & ~esc100
    for c in ("correiaA", "correiaB", "caboEsteira_XY", "caboEsteira_Y"):
        bpy.ops.wm.stl_import(filepath=f"{CX}/out/anim/poses/{c}_{k:03d}.stl"); ob = bpy.context.selected_objects[0]
        ob.name = f"{c}_pose{k}"
        mt = next((sl.material for o in objs100 if o.name == c for sl in o.material_slots if sl.material), mat_c)
        if mt: ob.data.materials.append(mt)
        anima(ob, "hide_render", 0, (~vis).astype(float), interp=0)
for o in objs200: anima(o, "hide_render", 0, (FR < F_P1).astype(float), interp=0)

# ---------------- filete impresso: malha com o tempo de cada trecho, aparece com geometry nodes ----------------
ng = bpy.data.node_groups.new("revela", 'GeometryNodeTree')
ng.interface.new_socket("Geometry", in_out='INPUT', socket_type='NodeSocketGeometry')
ng.interface.new_socket("Geometry", in_out='OUTPUT', socket_type='NodeSocketGeometry')
SOCK = ng.interface.new_socket("Tempo", in_out='INPUT', socket_type='NodeSocketFloat').identifier
gi, go = ng.nodes.new("NodeGroupInput"), ng.nodes.new("NodeGroupOutput")
na = ng.nodes.new("GeometryNodeInputNamedAttribute"); na.data_type = 'FLOAT'; na.inputs["Name"].default_value = "t"
cp = ng.nodes.new("FunctionNodeCompare"); cp.data_type = 'FLOAT'; cp.operation = 'GREATER_THAN'
dl = ng.nodes.new("GeometryNodeDeleteGeometry"); dl.domain = 'FACE'
ng.links.new(na.outputs["Attribute"], cp.inputs[0]); ng.links.new(gi.outputs["Tempo"], cp.inputs[1])
ng.links.new(gi.outputs["Geometry"], dl.inputs["Geometry"]); ng.links.new(cp.outputs["Result"], dl.inputs["Selection"])
ng.links.new(dl.outputs["Geometry"], go.inputs["Geometry"])
vidro = bpy.data.objects["mesa_vidro"]
def filete(c, nome, cor, t, vis):
    P, E, T = c["P"].astype(float), c["E"], c["T"]; H, Wd = float(c["H"]), float(c["W"])
    i = np.nonzero(E[1:])[0] + 1
    A_, B_ = P[i - 1].copy(), P[i].copy(); d = B_ - A_; L = np.linalg.norm(d, axis=1); k = L > 1e-4
    i, A_, B_, d, L = i[k], A_[k], B_[k], d[k], L[k]
    u = d / L[:, None]; A_ -= u * Wd * 0.3; B_ += u * Wd * 0.3              # emenda os trechos
    nr = np.c_[-u[:, 1], u[:, 0], np.zeros(len(u))]; th = np.arange(8) * np.pi / 4
    pr = np.cos(th)[None, :, None] * nr[:, None] * Wd / 2 + np.sin(th)[None, :, None] * np.array([0, 0, H / 2])
    off = np.array([TIP.x, TIP.y, SURF - H / 2])
    V = np.concatenate([(A_ + off)[:, None] + pr, (B_ + off)[:, None] + pr], 1).reshape(-1, 3)
    S = len(i); j = np.arange(8)
    q = np.stack([j, (j + 1) % 8, (j + 1) % 8 + 8, j + 8], 1).ravel()
    lp = np.concatenate([q, j[::-1], j + 8])[None] + np.arange(S)[:, None] * 16          # 8 lados + 2 tampas = 48 lacos
    st = (np.r_[np.arange(0, 33, 4), 40][None] + np.arange(S)[:, None] * 48).ravel()
    me = bpy.data.meshes.new(nome); me.vertices.add(len(V)); me.vertices.foreach_set("co", V.ravel())
    me.loops.add(lp.size); me.loops.foreach_set("vertex_index", lp.ravel())
    me.polygons.add(len(st)); me.polygons.foreach_set("loop_start", st); me.update()
    me.polygons.foreach_set("use_smooth", [True] * len(st))
    at = me.attributes.new("t", 'FLOAT', 'FACE'); at.data.foreach_set("value", np.repeat(T[i], 10))
    ob = bpy.data.objects.new(nome, me); sc.collection.objects.link(ob)
    ob.data.materials.append(visual.plastico(nome, cor))
    m = ob.data.materials[0].node_tree.nodes["Principled BSDF"]; m.inputs["Emission Strength"].default_value = 0.0
    ob.parent = vidro; ob.matrix_parent_inverse = vidro.matrix_world.inverted()
    md = ob.modifiers.new("revela", 'NODES'); md.node_group = ng
    anima(ob, f'modifiers["revela"]["{SOCK}"]', 0, t)
    anima(ob, "hide_render", 0, (~vis).astype(float), interp=0)
    ob.cycles.use_motion_blur = False
    print("FILETE", nome, S, "trechos", len(V), "vertices")
    return ob
# cor da peca da 200 = cor dela na montagem
p200 = next(o for o in objs200 if o.name.split(".")[0] == PECA)
cor_p = tuple(p200.active_material.diffuse_color[:3]) if p200.active_material else (0.1, 0.3, 0.8)
filete(BEN, "benchy", (0.85, 0.22, 0.03), np.where(FR >= F_B3, BEN["T"][-1] + 1, tB), (FR < F_B4))
filete(PEC, "peca200", cor_p, np.where(FR >= F_P1 - 24, PEC["T"][-1] + 1, tP), (FR >= F_B4) & (FR < F_P1))

# peca da 200 acende na montagem da 200
dm = p200.active_material.copy(); dm.name = "destaque"; p200.active_material = dm
pb = dm.node_tree.nodes.get("Principled BSDF") or next(n for n in dm.node_tree.nodes if n.type == 'BSDF_PRINCIPLED')
pb.inputs["Emission Color"].default_value = (1.0, 0.45, 0.08, 1)
s = pb.inputs["Emission Strength"]
for f, v in ((F_P1 + 40, 0.0), (F_P1 + 70, 2.5), (F_P2 - 30, 2.5), (F_P2, 0.0)): s.default_value = v; s.keyframe_insert("default_value", frame=f)

# ---------------- camera ----------------
cam = bpy.data.objects.new("cam", bpy.data.cameras.new("cam")); sc.collection.objects.link(cam); sc.camera = cam
cam.data.clip_start = 1; cam.data.clip_end = 50000; cam.data.sensor_width = 36
alvo = bpy.data.objects.new("alvo", None); sc.collection.objects.link(alvo)
tr = cam.constraints.new('TRACK_TO'); tr.target = alvo; tr.track_axis = 'TRACK_NEGATIVE_Z'; tr.up_axis = 'UP_Y'
TIPW = np.array(TIP) + np.c_[DF[:, :2] @ AB[:2, :2], np.zeros(F_FIM)]   # ponta do bico em cada quadro
SURFW = SURF + DF @ AM[:, 2]                                               # mesa embaixo do bico em cada quadro
def media(x, n=25): p = np.pad(x, ((n // 2, n // 2), (0, 0)), mode="edge"); return np.stack([np.convolve(p[:, i], np.ones(n) / n, "valid") for i in range(3)], 1)
TIPS = media(TIPW)
PECA_C = np.c_[np.full(F_FIM, TIP.x), np.full(F_FIM, TIP.y), SURFW + 15]   # centro da peca na mesa
b1 = np.array([[o.matrix_world @ Vector(c) for c in o.bound_box] for o in objs100]).reshape(-1, 3)
b2 = np.array([[o.matrix_world @ Vector(c) for c in o.bound_box] for o in objs200]).reshape(-1, 3)
C1, C2 = (b1.min(0) + b1.max(0)) / 2, (b2.min(0) + b2.max(0)) / 2
PC200 = np.array(sum((p200.matrix_world @ Vector(c) for c in p200.bound_box), Vector()) / 8)
def lerp(x, y, u): u = np.asarray(u)[..., None] if np.ndim(x) else u; return x + (y - x) * u
POS, ALV, LEN = np.zeros((F_FIM, 3)), np.zeros((F_FIM, 3)), np.zeros(F_FIM)
def orb(t, dist, az, el): az, el = math.radians(az), math.radians(el); return t + dist * np.array([math.cos(az) * math.cos(el), math.sin(az) * math.cos(el), math.sin(el)])
for i, f in enumerate(FR):
    if f < F_B1:                                   # titulo: maquina inteira, aproxima devagar
        u = (f - 1) / (F_B1 - 1); t = lerp(C1, TIPW[i], 0.3 * u); p = orb(t, 1500 - 350 * u, 245 + 10 * u, 20 - 4 * u); ln = 40
    elif f < F_B2:                                 # close do bico em 8x
        u = (f - F_B1) / (F_B2 - F_B1); t = TIPS[i] - np.array([0, 0, 2]); p = orb(t, 85, 188 + 14 * u, 12 + 5 * u); ln = 50
    elif f < F_B4:                                 # timelapse: abre ate a maquina toda e depois chega no Benchy pronto
        u = suave((f - F_B2) / 120); v = (f - F_B2) / (F_B4 - F_B2); w2 = suave((f - F_B3) / 60)
        t0 = TIPS[i] - np.array([0, 0, 2]); t1 = lerp(PECA_C[i], C1, 0.25)
        t = lerp(lerp(t0, t1, u), PECA_C[i], w2)
        p = orb(t, (85 + (250 - 85) * u) * (1 - w2) + 190 * w2, 202 + 78 * suave(v * 1.3), 17 - 5 * v); ln = 50 - 5 * u
    elif f < F_P1:                                 # peca da 200: close em 8x, abre no timelapse
        u = suave((f - F_P0) / 72); v = (f - F_B4) / (F_P1 - F_B4)
        t = lerp(TIPS[i] - np.array([0, 0, 2]), PECA_C[i], u); p = orb(t, 100 + 150 * u, 190 + 90 * suave(v * 1.4), 15); ln = 50
    elif f < F_P2:                                 # a 200 montada, camera gira e chega perto da peca acesa
        u = suave((f - F_P1) / (F_P2 - F_P1)); t = lerp(C2, PC200, 0.5 * u); p = orb(t, 1500 - 500 * u, 250 + 45 * u, 20 - 4 * u); ln = 40
    else:                                          # lado a lado
        u = suave((f - F_P2) / (F_FIM - F_P2)); t = (C1 + C2) / 2; p = orb(t, 1750 - 300 * u, 262 + 16 * u, 12); ln = 40
    POS[i], ALV[i], LEN[i] = p, t, ln
for i in range(3): anima(cam, "location", i, POS[:, i]); anima(alvo, "location", i, ALV[:, i])
anima(cam.data, "lens", 0, LEN)

# ---------------- render ----------------
if MODO == "cycles":
    sc.render.engine = 'CYCLES'; cy = sc.cycles; cy.device = 'CPU'; cy.samples = int(os.environ.get("CXY_SAMPLES", 24)); cy.use_denoising = True
    DEV = os.environ.get("CYCLES_DEVICE", "CPU").upper()        # OPTIX / CUDA / HIP / ONEAPI / METAL
    if DEV != "CPU":
        pr = bpy.context.preferences.addons["cycles"].preferences; pr.compute_device_type = DEV; pr.get_devices()
        for d in pr.devices: d.use = d.type != "CPU"
        cy.device = 'GPU'
    cy.denoiser = 'OPENIMAGEDENOISE'; cy.denoising_quality = os.environ.get("CXY_DENOISE", "HIGH"); cy.max_bounces = 4
    cy.use_auto_tile = True; cy.tile_size = 256
    sc.render.resolution_x, sc.render.resolution_y = 1280, 720
    sc.render.use_motion_blur = True               # so no 8x (cabeca anda ~20 mm por quadro); fora dele obturador 0
    sh = (((FR >= F_B1) & (FR < F_B2)) | ((FR >= F_B4) & (FR < F_P0))) * 0.5
    anima(sc, "render.motion_blur_shutter", 0, sh, interp=0)
else:
    sc.render.engine = 'BLENDER_WORKBENCH'; sh = sc.display.shading
    sh.light = 'STUDIO'; sh.color_type = 'MATERIAL'; sh.show_cavity = True; sh.show_shadows = False
    sc.display.render_aa = 'FXAA'; sc.view_settings.view_transform = 'Standard'; sc.view_settings.look = 'None'
    sc.render.resolution_x, sc.render.resolution_y = 640, 360
sc.render.image_settings.file_format = 'PNG'
sc.render.use_overwrite = False; sc.render.use_placeholder = True      # resumivel: pula quadro que ja existe
os.makedirs(OUTD, exist_ok=True); sc.render.filepath = f"{OUTD}/f"
if len(a) > 3: sc.frame_start, sc.frame_end = int(a[2]), int(a[3])
if os.environ.get("QUADROS"):
    import time
    for q in [int(x) for x in os.environ["QUADROS"].split(",")]:
        sc.frame_set(q); sc.render.filepath = f"{OUTD}/b{q:04d}.png"; t0 = time.time()
        bpy.ops.render.render(write_still=True); print(f"TEMPO {q} {time.time() - t0:.1f}", flush=True)
else: bpy.ops.render.render(animation=True)
