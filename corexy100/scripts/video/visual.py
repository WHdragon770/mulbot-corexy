# Visual do render final (Cycles): fundo cinza liso sem chao, luz de estudio e materiais de verdade
# (plastico com brilho + linhas de camada de impressao + realce nas quinas, metal escovado, vidro, PCB, LCD aceso).
# Usado pelo anima2.py: visual.materiais(modo), visual.fantasma(mat) (copia translucida pra cena dos cabos), visual.cena(sc, modo).
import bpy, math

FUNDO = (0.42, 0.43, 0.45)                        # cinza do fundo (linear, antes do AgX)
PLASTICO = {"azul", "branco", "cinza", "preto", "verm"}
METAL = {"aco": (0.30, 0.0), "alu": (0.34, 0.5), "latao": (0.25, 0.0)}   # rugosidade, anisotropia

def _no(nt, tipo, x, y, **inp):
    n = nt.nodes.new(tipo); n.location = (x, y)
    for k, v in inp.items(): n.inputs[k].default_value = v
    return n

def material(m):                                  # reescreve o material no lugar (mesma cor base)
    nt = m.node_tree; cor = tuple(nt.nodes["Principled BSDF"].inputs["Base Color"].default_value)
    for n in list(nt.nodes): nt.nodes.remove(n)
    out = _no(nt, "ShaderNodeOutputMaterial", 600, 0)
    p = _no(nt, "ShaderNodeBsdfPrincipled", 300, 0, **{"Base Color": cor})
    bev = _no(nt, "ShaderNodeBevel", -200, -250, Radius=0.5); bev.samples = 6     # quinas pegam luz (mm)
    nt.links.new(p.outputs[0], out.inputs[0])
    if m.name in PLASTICO:
        p.inputs["Roughness"].default_value = 0.42 if m.name == "preto" else 0.33
        p.inputs["Coat Weight"].default_value = 0.15; p.inputs["Coat Roughness"].default_value = 0.2
        tc = _no(nt, "ShaderNodeTexCoord", -600, 0)
        wv = _no(nt, "ShaderNodeTexWave", -400, 0, Scale=1.26, Distortion=0.0)     # 0,25 mm por camada
        wv.wave_type = 'BANDS'; wv.bands_direction = 'Z'
        bu = _no(nt, "ShaderNodeBump", 0, -100, Strength=0.25, Distance=0.04)
        nt.links.new(tc.outputs["Object"], wv.inputs["Vector"]); nt.links.new(wv.outputs["Fac"], bu.inputs["Height"])
        nt.links.new(bev.outputs[0], bu.inputs["Normal"]); nt.links.new(bu.outputs[0], p.inputs["Normal"])
    elif m.name in METAL:
        r, an = METAL[m.name]
        p.inputs["Metallic"].default_value = 1.0; p.inputs["Roughness"].default_value = r
        p.inputs["Anisotropic"].default_value = an; nt.links.new(bev.outputs[0], p.inputs["Normal"])
    elif m.name == "vidro":
        p.inputs["Base Color"].default_value = (0.88, 0.97, 0.95, 1)
        p.inputs["Transmission Weight"].default_value = 1.0; p.inputs["Roughness"].default_value = 0.02; p.inputs["IOR"].default_value = 1.52
    elif m.name == "pcb":
        p.inputs["Roughness"].default_value = 0.38; p.inputs["Coat Weight"].default_value = 0.4
    elif m.name == "lcd":
        p.inputs["Roughness"].default_value = 0.1
        p.inputs["Emission Color"].default_value = cor; p.inputs["Emission Strength"].default_value = 1.5
    else:
        p.inputs["Roughness"].default_value = 0.4
    return p

def plastico(nome, cor):                          # material novo de plastico/borracha (cabos)
    m = bpy.data.materials.new(nome); m.use_nodes = True; m.diffuse_color = (*cor, 1)
    p = m.node_tree.nodes["Principled BSDF"]; p.inputs["Base Color"].default_value = (*cor, 1)
    p.inputs["Roughness"].default_value = 0.45; p.inputs["Coat Weight"].default_value = 0.3
    p.inputs["Emission Color"].default_value = (*cor, 1); p.inputs["Emission Strength"].default_value = 2.5   # brilha atraves do quadro translucido
    return m

def fantasma(m):                                  # copia do material com um "quanto translucido" animavel (no Value "fantasma")
    c = m.copy(); c.name = m.name + "_quadro"
    if c.use_nodes:
        nt = c.node_tree; out = next(n for n in nt.nodes if n.type == 'OUTPUT_MATERIAL')
        sh = out.inputs[0].links[0].from_socket
        v = nt.nodes.new("ShaderNodeValue"); v.name = v.label = "fantasma"; v.outputs[0].default_value = 0.0
        fr = nt.nodes.new("ShaderNodeLayerWeight"); fr.inputs["Blend"].default_value = 0.35
        mu = nt.nodes.new("ShaderNodeMath"); mu.operation = 'MULTIPLY'
        mi = nt.nodes.new("ShaderNodeMath"); mi.operation = 'SUBTRACT'; mi.use_clamp = True
        tr = nt.nodes.new("ShaderNodeBsdfTransparent"); mx = nt.nodes.new("ShaderNodeMixShader")
        nt.links.new(v.outputs[0], mi.inputs[0]); nt.links.new(fr.outputs["Facing"], mu.inputs[0]); mu.inputs[1].default_value = 0.4
        nt.links.new(mu.outputs[0], mi.inputs[1])            # a borda continua um pouco visivel (contorno da peca)
        nt.links.new(mi.outputs[0], mx.inputs[0]); nt.links.new(sh, mx.inputs[1]); nt.links.new(tr.outputs[0], mx.inputs[2])
        nt.links.new(mx.outputs[0], out.inputs[0])
    return c

def chave_fantasma(c, f, k):                      # k = 0 solido .. ~0.9 quase invisivel (Cycles e previa)
    if c.use_nodes:
        v = c.node_tree.nodes["fantasma"].outputs[0]; v.default_value = k; v.keyframe_insert("default_value", frame=f)
    c.diffuse_color[3] = 1 - 0.75 * k; c.keyframe_insert("diffuse_color", index=3, frame=f)

def cena(sc, modo):
    w = bpy.data.worlds.new("w"); sc.world = w; w.use_nodes = True; w.color = FUNDO
    nt = w.node_tree; nt.nodes.clear()
    out = nt.nodes.new("ShaderNodeOutputWorld")
    luz = nt.nodes.new("ShaderNodeBackground"); luz.inputs[0].default_value = (0.82, 0.86, 0.92, 1); luz.inputs[1].default_value = 0.55
    liso = nt.nodes.new("ShaderNodeBackground"); liso.inputs[0].default_value = (*FUNDO, 1); liso.inputs[1].default_value = 1.0
    lp = nt.nodes.new("ShaderNodeLightPath"); mx = nt.nodes.new("ShaderNodeMixShader")
    nt.links.new(lp.outputs["Is Camera Ray"], mx.inputs[0])          # a camera ve cinza liso; as pecas recebem luz de estudio
    nt.links.new(luz.outputs[0], mx.inputs[1]); nt.links.new(liso.outputs[0], mx.inputs[2]); nt.links.new(mx.outputs[0], out.inputs[0])
    for rot, en, ang in (((48, 8, -38), 3.2, 6), ((62, -12, 150), 2.2, 3), ((75, 0, 60), 0.7, 20)):   # chave, contraluz, preenchimento
        lz = bpy.data.lights.new("s", 'SUN'); lz.energy = en; lz.angle = math.radians(ang)
        ob = bpy.data.objects.new("s", lz); sc.collection.objects.link(ob); ob.rotation_euler = [math.radians(x) for x in rot]
    if modo in ("cycles", "bench"): sc.cycles.transparent_max_bounces = 24   # quadro translucido: varias paredes na frente dos cabos
    else: sc.display.shading.background_type = 'WORLD'

def materiais(modo):                              # chamar ANTES de criar as copias fantasma
    if modo not in ("cycles", "bench"): return
    for m in list(bpy.data.materials):
        if m.use_nodes and "Principled BSDF" in m.node_tree.nodes: material(m)
