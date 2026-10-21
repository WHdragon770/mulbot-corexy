# Desenhos de montagem da Mulbot CoreXY no estilo das folhas DL1 da Mulbot (wiki RepRap):
# vista(s) do conjunto com baloes numerados, lista de pecas e carimbo. Uma folha por conjunto.
# python3 folhas.py [saida] [CXY-01,CXY-03,...]     (rodar cxy.py com ESFERAS=0 na pose padrao antes)
import sys, os, json, math, subprocess, collections, datetime, numpy as np
from PIL import Image, ImageDraw, ImageFont
from scipy import ndimage

AQUI = os.path.dirname(os.path.abspath(__file__))
OUT = sys.argv[1] if len(sys.argv) > 1 else "/home/lucas/corexy/final/desenhos"
SO = sys.argv[2].split(",") if len(sys.argv) > 2 else None
TMP = "/home/lucas/corexy/out/desenhos"; os.makedirs(TMP, exist_ok=True); os.makedirs(OUT, exist_ok=True)
BL = os.path.expanduser("~/.local/opt/blender-4.2.3-linux-x64/blender")
ENV = dict(os.environ, LD_LIBRARY_PATH=os.path.expanduser("~/.local/opt/blibs/root/usr/lib/x86_64-linux-gnu"))
J = json.load(open("/home/lucas/corexy/out/cxy.json"))
F = "/usr/share/fonts/truetype/dejavu/DejaVuSans"
def fonte(t, b=False): return ImageFont.truetype(F + ("-Bold" if b else "") + ".ttf", t)

# ---------------- pecas: chave do item, descricao, origem
def base(stl): return os.path.splitext(os.path.basename(stl))[0]
VIT = {"lite6": "lite6", "nema17": "nema17", "endstop": "endstop_pcb", "lcd": "lcd_placa", "ramps": "ramps_pcb",
       "rodaV": "rodaV", "rodaZ": "rodaZ"}       # vitaminas com varias malhas: conta so a principal
def chave(stl):
    b = base(stl)
    for k in VIT:
        if b.startswith(k): return "roldanaV" if k in ("rodaV", "rodaZ") else k
    return b
def principal(stl):
    b = base(stl)
    for k, p in VIT.items():
        if b.startswith(k): return b == p
    return True
LADO = {"D": "direito", "E": "esquerdo"}
DESC = {"baseFrente": "Base da frente", "baseTras": "Base de trás", "baseLatF": "Base lateral da frente",
        "baseLatT": "Base lateral de trás", "posteFrenteInf": "Poste da frente, de baixo", "posteFrenteSup": "Poste da frente, de cima",
        "posteTrasInf": "Poste de trás, de baixo", "posteTrasSup": "Poste de trás, de cima", "travFrente": "Travessa de cima, frente",
        "travTras": "Travessa de cima, trás", "torreFrente": "Torre da frente (polias loucas)", "torreTras": "Torre de trás (motor A/B)",
        "trilhoY": "Viga Y com guia em V", "trilhoX": "Viga X com guia em V", "trilhoZ": "Viga Z com guia em V",
        "suportePortico": "Suporte do pórtico (carro Y)", "carroX": "Carro X: prateleira do hotend + correias", "bracoFimCursoX": "Braço do fim de curso X (2x M3 + insertos)",
        "dutoCoreXY": "Duto da ventoinha de peça", "suporteExtrusoraDireta": "Suporte da extrusora direta",
        "baseZInf": "Base Z de baixo (alojamento do motor)", "baseZSup": "Base Z de cima (motor + colar do fuso)", "baseZ": "Base Z (motor + colar do fuso)", "chapaZY": "Chapa de ligação viga Z - viga Y", "bracoMesa": "Braço da mesa (carro Z)",
        "fusoZ": "Fuso Z impresso 250 mm", "porcaZ": "Porca do fuso Z", "presilha_disco": "Presilha do vidro, botão excêntrico",
        "buchaX": "Bucha excêntrica espaçadora", "buchaY": "Bucha excêntrica espaçadora", "buchaZ": "Bucha excêntrica",
        "roldanaV": "Roldana V c/ rolamento de roletes impresso (resina)",
        "DL1-01-08": "Pé de apoio (TPU)", "DL1-03-04_110": "Suporte da mesa (ampliado 10%)", "DL1-03-05": "Knob de nivelamento",
        "DL1-03-06": "Localizador do canto do vidro", "DL1-03-08": "Porca serrilhada da presilha", "DL1-04-07": "Presilha do hotend",
        "DL1-04-08": "Polia motora", "DL1-05-01_cabo": "Base do display (furada p/ o cabo)", "DL1-05-02": "Tampa do display",
        "DL1-05-03": "Botão reset", "DL1-05-04": "Knob do display", "DL1-05-05": "Cabeça do robô (enfeite)",
        "DL1-02-09_caixa_ramps": "Caixa da RAMPS", "DL1-02-10_porta_fechada": "Porta da caixa da RAMPS", "DL1-02-11": "Robô (enfeite da porta)",
        "DL1-02-15": "Proteção da fonte", "DL1-06-01": "Polia louca", "DL1-06-02_L10.0": "Eixo da polia A, 10 mm",
        "DL1-06-02_L14.0": "Eixo da polia A, 14 mm", "DL1-06-03_L10.0": "Eixo da polia B, 10 mm", "DL1-06-03_L14.0": "Eixo da polia B, 14 mm",
        "DL1-06-04": "Gaiola das esferas", "nema17": "Motor de passo NEMA 17", "lite6": "Hotend E3D Lite6 1,75 mm",
        "ventoinha5015": "Ventoinha radial 5015, 12 V", "endstop": "Fim de curso mecânico", "ezr_corpo": "Extrusora EZR (Bondtech)",
        "bowden_direta": "Tubo PTFE 4x2 mm, ~88 mm", "correiaA": "Correia A, 1418 mm", "correiaB": "Correia B, 1418 mm",
        "mega": "Arduino Mega 2560", "ramps": "RAMPS 1.4 + 4 drivers", "fonte_rs150": "Fonte 12 V 150 W",
        "iec_c14": "Tomada IEC C14 com chave", "lcd": "Display RepRapDiscount 128x64", "vidro": "Vidro 235 x 235 mm (Ender 3)",
        "mola": "Mola de compressão 7,5 x 20 mm"}
def descricao(k):
    if k.startswith(("parafuso_", "barril_", "porca_")):
        t, m = k.split("_", 1)
        if t == "parafuso": return f"Parafuso {m.replace('x', ' x ')} impresso"
        if t == "porca": return f"Porca {m} impressa"
        d, dim = m.split("_D"); return f"Porca-barril {d}, D{dim.replace('x', ' x ')} impressa"
    if k in DESC: return DESC[k]
    b, _, l = k.rpartition("_")
    if b in DESC and l in LADO: return f"{DESC[b]}, {LADO[l]}"
    return k
def origem(k, stl):
    if "/fixadores/" in stl: return "Impressa"
    if "/mulbot/vit/" in stl or chave(stl) in ("nema17", "lite6", "endstop", "lcd", "ramps", "mega") or k.startswith(("correia", "bowden")):
        return "Comprada"
    if "/mulbot/" in stl: return "Mulbot"
    return "Nova" if not k.startswith("DL1") else "Mulbot mod."

# ---------------- folhas: prefixos (nome na montagem antes do 1o "_") e vistas
QUADRO = ("baseFrente", "baseTras", "baseLatF", "baseLatT", "posteFrenteInf", "posteFrenteSup", "posteTrasInf", "posteTrasSup",
          "posteFrente", "posteTras", "travFrente", "travTras", "torreFrente", "torreTras", "pe")
CABOS = [  # item, prefixos na montagem, cabo, caminho por dentro do quadro
    (1, ("caixaRAMPS",), "Caixa da RAMPS", "entra pela janela de baixo, vindo do poste de trás esquerdo"),
    (2, ("motorA",), "Motor A (X na RAMPS)", "parede da torre de trás dir. > poste de trás dir. > bases > poste esq."),
    (3, ("motorB",), "Motor B (Y na RAMPS)", "atravessa a placa > parede da torre esq. > poste de trás esq."),
    (4, ("motorZ",), "Motores Z esq. e dir.", "base Z > base lateral de trás (dir.: + base de trás) > poste esq."),
    (5, ("fonte",), "Fonte 12 V", "poste de trás dir. > base lat. de trás > base de trás > poste esq."),
    (6, ("displayBase",), "Display (2 cabos flat)", "base da frente > poste da frente esq. > alma da viga Y > poste de trás"),
    (7, ("fimCursoZ",), "Fim de curso Z", "furo embaixo da viga Y esq. > alma da viga Y > poste de trás esq."),
    (8, ("fimCursoY",), "Fim de curso Y", "parede da torre de trás esq. > poste de trás esq."),
    (9, ("carroX", "hotend", "ventoinha5015", "motorE", "fimCursoX"), "Cabeça: aquecedor, termistor, 2 ventoinhas, motor E, fim de curso X",
        "esteira X > esteira Y > parede de fora da torre de trás dir. > travessa de trás > torre esq. > poste esq."),
    (10, (), "Canais (ar dentro do quadro)", "parede 2 mm; ~4 mm livres ao lado das porcas-barril"),
]
FOLHAS = [
    dict(id="CXY-01", arquivo="Quadro", titulo="QUADRO", pref=QUADRO,
         vistas=[dict(dir=[1, -1.25, 0.85]), dict(dir=[-1.1, 1.2, 0.7], legenda="VISTA DE TRÁS")],
         notas=["Bases, postes e travessas são ocos (parede 2 mm) com passagem de cabo: ver folha CXY-10.",
                "Postes vêm em 2 metades (Inf/Sup) com emenda sobreposta + 2 parafusos M10."]),
    dict(id="CXY-02", arquivo="Eixo Y e portico", titulo="EIXO Y E PÓRTICO", pref=("trilhoY", "suportePortico", "rodaY", "buchaY", "fimCursoY"),
         vistas=[dict(dir=[1, -1.2, 0.9]), dict(dir=[1, -0.7, -0.35], centro=[176, 47.6, 432], escala=150, legenda="DETALHE: CARRO Y DIREITO (RODAS)")],
         notas=["Carro Y: 2 roldanas fixas por dentro + 1 excêntrica por fora (bucha espaçadora, chave 14).",
                "Fim de curso Y fica na torre de trás esquerda: a lingueta do suporte aperta com Y = +152."]),
    dict(id="CXY-03", arquivo="Eixo X e cabeca", titulo="EIXO X E CABEÇA", pref=("trilhoX", "carroX", "bracoFimCursoX", "rodaX", "buchaX", "hotend", "presilhaHotend", "ventoinha5015",
                                                      "dutoCoreXY", "suporteExtrusoraDireta", "ezr", "motorE", "bowden", "fimCursoX"),
         vistas=[dict(dir=[0.9, -1.2, 0.7]), dict(dir=[-0.8, 1.2, 0.6], centro=[0, 47.6, 505], escala=210, legenda="DETALHE: CARRO X POR TRÁS")],
         notas=["Carro X: 2 roldanas fixas embaixo + 1 excêntrica em cima, atrás da torre das correias.",
                "Fim de curso X: na parede do suporte esquerdo, o braço do carro aperta com X = -101,5."]),
    dict(id="CXY-04", arquivo="Eixo Z", titulo="EIXO Z", pref=("baseZ", "trilhoZ", "chapaZY", "bracoMesa", "rodaZ", "buchaZ", "fusoZ", "porcaZ", "motorZ", "fimCursoZ"),
         vistas=[dict(dir=[1, -1.1, 0.7], desloca={"motorZ": [0, 0, -110]}), dict(dir=[1, -0.9, 0.5], centro=[176, -40, 60], escala=190, legenda="DETALHE: BASE Z DIREITA")],
         notas=["Fuso e porca: imprimir a versão FDM OU a de resina (2 metades + pino D).",
                "Fim de curso Z embaixo da viga Y esquerda: o braço da mesa aperta no topo do curso.",
                "Na vista grande o motor Z aparece descido (explodido): ele entra por baixo da base Z."]),
    dict(id="CXY-05", arquivo="Mesa", titulo="MESA", pref=("mesa",),
         vistas=[dict(dir=[1, -1.2, 0.9]), dict(dir=[1, -1.25, 0.85], centro=[121, 121, 385], escala=55, legenda="DETALHE: PRESILHA DO VIDRO")],
         notas=["Presilha: meia volta solta o vidro. Risco em relevo apontando pro vidro = travado.",
                "Imprimir a presilha de cabeça pra baixo (topo na mesa, pino pra cima)."]),
    dict(id="CXY-06", arquivo="CoreXY - correias e polias", titulo="COREXY: CORREIAS E POLIAS", pref=("motorA", "motorB", "loucaFrente", "loucaPortico", "correiaA", "correiaB"),
         vistas=[dict(dir=[1, -1.2, 1.1]), dict(dir=[0.0001, -0.0001, 1], legenda="VISTA DE CIMA: CAMINHO DAS CORREIAS")],
         notas=["Correia A (de cima) no motor A (trás direito); correia B (de baixo) no motor B (trás esquerdo).",
                "As 2 correias têm 1418 mm. As pontas prendem na torre do carro X, dando a volta no pino."],
         extra=[("Esfera de aço 4,5 mm (polia louca)", "Comprada", 12 * 8, "esfera_4.5")]),
    dict(id="CXY-08", arquivo="Roldana V", titulo="ROLDANA V (X, Y E Z)", pref=(), objetos=lambda: roldana_itens(),
         vistas=[dict(dir=[1, -1.3, 0.55], margem=1.25, legenda="MONTAGEM (EXPLODIDA NO EIXO)"),
                 dict(dir=[0.0001, -1, 0.0001], legenda="CORTE A-A: 10 ROLETES IMPRESSOS JUNTO")],
         notas=["15 roldanas iguais na máquina: 3 no X, 6 no Y, 6 no Z. Imprimir em resina ABS-like/tough, 1 peça só.",
                "Os roletes nascem presos por pontes de 0,4 mm: lavar no IPA, girar com força até soltar, lavar de novo girando, curar.",
                "Excêntrica (1 por carro): girar a bucha com chave 14 até a roda encostar no V sem folga, depois apertar o M6."]),
    dict(id="CXY-10", arquivo="Passagem de cabos", titulo="PASSAGEM DE CABOS", pref=(), objetos=lambda: cabos_itens(),
         vistas=[dict(dir=[-1.0, -1.15, 0.75]), dict(imagem="/home/lucas/corexy/out/cabos/corte/canto.png", legenda="CORTE: CANTO DE TRÁS ESQUERDO")],
         tabela=([("Nº", 70), ("CABO", 400), ("CAMINHO POR DENTRO DO QUADRO", 710)], [(n, c, r) for n, _, c, r in CABOS]),
         titulo_tabela="ROTAS DOS CABOS",
         notas=["Azul = canal oco. Tudo converge no poste de trás esquerdo e entra na caixa da RAMPS pela janela de baixo.",
                "Conferido por script: cabo de 4,5 mm passa de todos os pontos até a RAMPS (scripts/cabos_check.py).",
                "Passar o fio sem conector ao lado das porcas-barril e crimpar depois. Ligações: folha CXY-09."]),
    dict(id="CXY-11", arquivo="Esteira porta-cabos", titulo="ESTEIRA PORTA-CABOS (CABEÇA)",
         pref=("eloX", "eloY", "pontaFixaX", "pontaFixaY", "bandejaX", "bandejaY", "bracoEsteiraX", "suporteEsteiraY", "caboEsteira"),
         vistas=[dict(dir=[0.9, -1.2, 0.8]), dict(dir=[1, -0.9, 0.55], centro=[232, 40, 462], escala=150, legenda="DETALHE: ESTEIRA Y (LADO DIREITO, POR FORA)")],
         notas=["Esteira X atrás da viga X (11 elos) e esteira Y por fora do lado direito (12 elos): o mesmo elo nas 2. Imprimir em PETG, em pé.",
                "Pino de cada junta: pedaço de filamento 1,75 mm (2 por junta, 4 mm), entra apertado na placa de fora; derreter a ponta.",
                "Bandeja X: 4x M3x10 em insertos na viga X. Suporte Y: 2x M3x10 em insertos no suporte do pórtico D. Pontas fixas: 2x M3x10 + porca.",
                "Braço do carro: o M3 da direita do suporte da extrusora vira M3x18. O cabo sai da esteira Y e entra na torre de trás direita."]),
    dict(id="CXY-07", arquivo="Eletronica e display", titulo="ELETRÔNICA E DISPLAY", pref=("caixaRAMPS", "portaRAMPS", "roboGrande", "mega", "ramps", "fonte", "protecaoFonte",
                                                          "tomadaIEC", "displayBase", "displayTampa", "lcd", "botaoReset", "knobDisplay", "roboDisplay"),
         vistas=[dict(dir=[-1.0, 1.1, 0.55], filtro=("caixaRAMPS", "portaRAMPS", "roboGrande", "mega", "ramps", "fonte", "protecaoFonte", "tomadaIEC"),
                      desloca={"portaRAMPS": [-90, 0, 0], "roboGrande": [-90, 0, 0], "fonte": [-215, 0, 60], "protecaoFonte": [-215, 0, -40], "tomadaIEC": [-215, 0, -40]},
                      legenda="CAIXA DA RAMPS E FONTE (ATRÁS, VISTA EXPLODIDA)"),
                 dict(dir=[0.5, -1.2, 0.7], filtro=("displayBase", "displayTampa", "lcd", "botaoReset", "knobDisplay", "roboDisplay"),
                      legenda="DISPLAY (FRENTE)")],
         notas=["Ligações: folha CXY-09. Os cabos entram na caixa pela janela de baixo, vindos do poste de trás esquerdo."]),
]

def roldana_itens():
    """CXY-08: roldana V explodida no eixo + corte (gera as metades cortadas em TMP)"""
    sys.path.insert(0, "/home/lucas/corexy/scripts")
    import trimesh, manifold3d as mf
    from base import M, Tm, caixa
    D = "/home/lucas/corexy/derived"
    def T(z, rx=False, x=0.0):
        t = np.eye(4); t[:3, 3] = (x, 0, z)
        if rx: t[:3, :3] = np.diag([1, -1, -1])
        return t.tolist()
    it = [dict(nome="parafuso_M6x30", stl=f"{D}/fixadores/parafuso_M6x30.stl", T=T(48, True), cor="azul"),
          dict(nome="buchaY", stl=f"{D}/buchaY.stl", T=T(22), cor="latao"),
          dict(nome="rodaV", stl=f"{D}/rodaV.stl", T=T(0), cor="verm"),
          dict(nome="rodaV_roletes", stl=f"{D}/rodaV_roletes.stl", T=T(0), cor="cinza"),
          dict(nome="porca_M6", stl=f"{D}/fixadores/porca_M6.stl", T=T(-30), cor="azul")]
    for n, cor in (("rodaV", "verm"), ("rodaV_roletes", "cinza")):     # metade (corte no plano y=0)
        m = M(trimesh.load(f"{D}/{n}.stl")) - caixa((-50, -50, -50), (50, 0, 50)); fn = f"{TMP}/{n}_corte.stl"; Tm(m).export(fn)
        it.append(dict(nome=n + "_corte", stl=fn, T=T(0), cor=cor, so_vista=1))
    for j in it: j.setdefault("so_vista", 0)
    return it

def cabos_itens():
    it = []
    for n, pref, _, _ in CABOS:
        for j in J:
            if pref_de(j["nome"]) in pref and principal(j["stl"]) and not j["nome"].startswith("fix_"): it.append(dict(j, item=n))
    it.append(dict(nome="canais", stl="/home/lucas/corexy/derived/cabos_ar.stl", T=np.eye(4).tolist(), cor="azul", item=10))
    for j in J:     # quadro em cinza bem claro so na vista de cima (referencia)
        if pref_de(j["nome"]) in QUADRO and not j["nome"].startswith("fix_"): it.append(dict(j, cor="branco", so_vista=1, item=0))
    for j in it:
        if j["cor"] == "vidro": j["cor"] = "branco"
        j.setdefault("so_vista", 0) if j["item"] else None
    return it

def pref_de(n):
    if n.startswith("fix_"):
        t = [x for x in n[4:].split("_") if x not in ("D", "E", "")]
        t = t[1:] if t[0] in ("barril", "porca") else t
        return t[1] if len(t) > 1 else ""
    return n.split("_")[0]

# ---------------- render
def renderiza(fid, k, itens, v):
    ij, vj, png = f"{TMP}/{fid}_{k}_itens.json", f"{TMP}/{fid}_{k}_vista.json", f"{TMP}/{fid}_{k}.png"
    json.dump(itens, open(ij, "w")); json.dump(v, open(vj, "w"))
    r = subprocess.run([BL, "-b", "--factory-startup", "-P", f"{AQUI}/render_folha.py", "--", ij, vj, png], env=ENV, capture_output=True, text=True)
    if not os.path.exists(png): sys.exit(r.stdout[-2000:] + r.stderr[-2000:])
    return png, json.load(open(png[:-4] + ".json"))

# ---------------- baloes: em volta da silhueta, ordem angular (sem cruzar setas), afastados entre si
RB = 26
def baloes(mask, ancs, caixa):
    """ancs: [(item, x, y)] -> [(item, x, y, bx, by)]"""
    if not ancs: return []
    cy, cx = ndimage.center_of_mass(mask)
    dil = ndimage.binary_dilation(mask, iterations=12)
    ys, xs = np.nonzero(dil[::3, ::3]); ys, xs = ys * 3, xs * 3
    ang = np.arctan2(ys - cy, xs - cx); dist = np.hypot(ys - cy, xs - cx)
    NB = 720; rmax = np.zeros(NB); b = ((ang + np.pi) / (2 * np.pi) * NB).astype(int) % NB
    np.maximum.at(rmax, b, dist); rmax = ndimage.maximum_filter1d(rmax, 9, mode="wrap")
    def pos(t):
        r = rmax[int((t + np.pi) / (2 * np.pi) * NB) % NB] + 55
        x, y = cx + r * math.cos(t), cy + r * math.sin(t)
        return min(max(x, caixa[0] + RB + 4), caixa[2] - RB - 4), min(max(y, caixa[1] + RB + 4), caixa[3] - RB - 4)
    L = sorted(ancs, key=lambda a: math.atan2(a[2] - cy, a[1] - cx))
    t = [math.atan2(a[2] - cy, a[1] - cx) for a in L]
    for _ in range(800):
        mexeu = False
        for i in range(len(t)):
            j = (i + 1) % len(t)
            if j == i: break
            p, q = pos(t[i]), pos(t[j])
            if math.hypot(p[0] - q[0], p[1] - q[1]) < 2 * RB + 10:
                t[i] -= 0.004; t[j] += 0.004; mexeu = True
        if not mexeu: break
    return [(a[0], a[1], a[2]) + pos(tt) for a, tt in zip(L, t)]

# ---------------- folha
SW, SH = 3508, 2480                 # A4 deitada a 300 dpi
M0, CAR = 40, 190                   # margem e largura do carimbo (direita)
COLW = 1180                         # coluna da tabela
def folha(fd):
    fid = fd["id"]
    obj = fd["objetos"]() if "objetos" in fd else [j for j in J if pref_de(j["nome"]) in fd["pref"] and not j["nome"].startswith("esfera")]
    # itens: chave -> objetos
    itens = collections.OrderedDict()
    for j in obj:
        if j.get("item") == 0: continue          # so referencia visual, sem balao
        k = j["item"] if "item" in j else chave(j["stl"]); k = "fix:" + k if j["nome"].startswith("fix_") else k
        itens.setdefault(k, []).append(j)
    ordem = sorted(itens) if all(isinstance(k, int) for k in itens) else sorted(itens, key=lambda k: (k.startswith("fix:"), origem(k.replace("fix:", ""), itens[k][0]["stl"]) == "Comprada", k.lower()))
    num = {k: (k if isinstance(k, int) else i + 1) for i, k in enumerate(ordem)}
    # vistas
    W0 = SW - CAR - COLW - 3 * M0
    img = Image.new("RGB", (SW, SH), "white"); dr = ImageDraw.Draw(img)
    vistas = fd["vistas"]
    areas = [(M0, M0, M0 + W0, SH - M0)]
    if len(vistas) > 1:
        tab_h = 120 + 40 * (len(ordem) + len(fd.get("extra", [])))
        if "tabela" in fd: tab_h = tabela(ImageDraw.Draw(Image.new("RGB", (10, 10))), 0, 0, "", *fd["tabela"]) + 10
        areas.append((SW - CAR - M0 - COLW, M0 + tab_h + 40, SW - CAR - M0, SH - M0 - 80 * len(fd.get("notas", [])) - 70))
    melhor = {}                        # item -> (vista, x, y, nvis)
    imgs = []
    for vi, (v, ar) in enumerate(zip(vistas, areas)):
        sub = [j for j in obj if (not v.get("filtro") or pref_de(j["nome"]) in v["filtro"]) and j.get("so_vista", vi) == vi]
        if v.get("desloca"):                   # vista explodida: afasta pecas pra mostrar o que esta atras
            sub = [dict(j) for j in sub]
            for j in sub:
                dlt = v["desloca"].get(pref_de(j["nome"]))
                if dlt: T = np.array(j["T"]); T[:3, 3] += dlt; j["T"] = T.tolist()
        w, h = ar[2] - ar[0], ar[3] - ar[1] - (50 if v.get("legenda") else 0)
        if w < 300 or h < 300: continue
        if v.get("imagem"):                    # imagem pronta (ex.: corte), sem baloes
            im = Image.open(v["imagem"]).convert("RGBA"); im.thumbnail((int(w), int(h)))
            fundo = Image.new("RGBA", (int(w), int(h)), (255, 255, 255, 0)); fundo.paste(im, ((int(w) - im.size[0]) // 2, (int(h) - im.size[1]) // 2))
            imgs.append((vi, ar, fundo, v)); continue
        vv = dict(v, res=[int(w), int(h)]); [vv.pop(c, None) for c in ("filtro", "legenda", "desloca")]
        png, anc = renderiza(fid, vi, sub, vv)
        im = Image.open(png).convert("RGBA"); imgs.append((vi, ar, im, v))
        for k, js in itens.items():
            for j in js:
                if j["nome"] in anc and (principal(j["stl"]) or "item" in j):
                    n, ps = anc[j["nome"]]
                    peso = n * (3 if vi == 0 else 1)
                    if k not in melhor or peso > melhor[k][3]: melhor[k] = (vi, ps, None, peso)
    for vi, ar, im, v in imgs:
        img.paste(im, (ar[0], ar[1]), im)
        if v.get("legenda"):
            f = fonte(30, True); tw = dr.textlength(v["legenda"], font=f)
            dr.text((ar[0] + (ar[2] - ar[0] - tw) / 2, ar[3] - 44), v["legenda"], fill="black", font=f)
        mask = np.array(im)[:, :, 3] > 10
        # ponto da seta: o visivel mais longe do centro da silhueta (seta curta), mas com 10 px de peca em volta
        dentro = ndimage.binary_erosion(mask, iterations=10); cy, cx = ndimage.center_of_mass(mask)
        ancs = []
        for k, (vj, ps, _, _) in melhor.items():
            if vj != vi: continue
            ok = [p for p in ps if dentro[min(int(p[1]), mask.shape[0] - 1), min(int(p[0]), mask.shape[1] - 1)]] or ps
            x, y = max(ok, key=lambda p: (p[0] - cx) ** 2 + (p[1] - cy) ** 2); ancs.append((k, x, y))
        cx = (0, 0, im.size[0], im.size[1])
        for k, x, y, bx, by in baloes(mask, ancs, cx):
            X, Y, BX, BY = ar[0] + x, ar[1] + y, ar[0] + bx, ar[1] + by
            d = math.hypot(X - BX, Y - BY) or 1
            dr.line((BX + (X - BX) * RB / d, BY + (Y - BY) * RB / d, X, Y), fill="black", width=3)
            dr.ellipse((X - 6, Y - 6, X + 6, Y + 6), fill="black")
            dr.ellipse((BX - RB, BY - RB, BX + RB, BY + RB), fill="white", outline="black", width=3)
            t = str(num[k]); f = fonte(28); tw = dr.textlength(t, font=f)
            dr.text((BX - tw / 2, BY - 17), t, fill="black", font=f)
    # tabela
    x0 = SW - CAR - M0 - COLW
    if "tabela" in fd: cols, linhas = fd["tabela"]
    else:
        cols = [("ITEM", 90), ("QTD", 90), ("PEÇA", 310), ("DESCRIÇÃO", 520), ("ORIGEM", 170)]
        linhas = []
        for k in ordem:
            js = itens[k]; kk = k.replace("fix:", "")
            q = sum(1 for j in js if principal(j["stl"]))
            linhas.append((num[k], q, kk, descricao(kk), origem(kk, js[0]["stl"])))
        for i, (d, o, q, p) in enumerate(fd.get("extra", [])): linhas.append((len(ordem) + i + 1, q, p, d, o))
    tabela(dr, x0, M0, fd.get("titulo_tabela", "LISTA DE PEÇAS"), cols, linhas)
    notas(dr, x0, fd.get("notas", []))
    carimbo(img, dr, fid, fd["titulo"])
    fn_out = f"{OUT}/{fid} - {fd['arquivo']}.png"
    img.save(fn_out, dpi=(300, 300)); print(fn_out, len(ordem), "itens")
    return fn_out

def tabela(dr, x0, y0, titulo, cols, linhas, hl=40):
    f, fb = fonte(22), fonte(23, True); L = sum(w for _, w in cols)
    dr.rectangle((x0, y0, x0 + L, y0 + 44), outline="black", width=2)
    tw = dr.textlength(titulo, font=fb); dr.text((x0 + (L - tw) / 2, y0 + 9), titulo, font=fb, fill="black")
    y = y0 + 44; x = x0
    for c, w in cols:
        dr.rectangle((x, y, x + w, y + hl), outline="black", width=2); tw = dr.textlength(c, font=fb)
        dr.text((x + (w - tw) / 2, y + 8), c, font=fb, fill="black"); x += w
    def quebra(t, w):                      # texto em linhas que cabem na celula
        out, lin = [], ""
        for p in str(t).split():
            if lin and dr.textlength(lin + " " + p, font=f) > w - 14: out.append(lin); lin = p
            else: lin = (lin + " " + p).strip()
        return out + [lin]
    y += hl
    for ln in linhas:
        cel = [quebra(val, w) for (c, w), val in zip(cols, ln)]
        h = hl + 28 * (max(len(c) for c in cel) - 1); x = x0
        for (c, w), ls in zip(cols, cel):
            dr.rectangle((x, y, x + w, y + h), outline="black", width=1)
            for i, t in enumerate(ls):
                tx = x + (w - dr.textlength(t, font=f)) / 2 if c in ("ITEM", "QTD", "Nº") else x + 8
                dr.text((tx, y + 8 + 28 * i), t, font=f, fill="black")
            x += w
        y += h
    return y

def notas(dr, x0, nts):
    fn = fonte(26); ln_n = []
    for i, t in enumerate(nts):
        pal, lin = f"{i + 1}. {t}".split(), ""
        for w in pal:
            if dr.textlength(lin + " " + w, font=fn) > COLW - 10: ln_n.append(lin); lin = "    " + w
            else: lin = (lin + " " + w).strip() if not lin.startswith("    ") else lin + " " + w
        ln_n.append(lin)
    yn = SH - M0 - 38 * len(ln_n) - 50
    if ln_n:
        dr.text((x0, yn), "NOTAS:", font=fonte(26, True), fill="black")
        for i, t in enumerate(ln_n): dr.text((x0, yn + 38 * (i + 1)), t, font=fn, fill="black")

def carimbo(img, dr, fid, titulo):
    dr.rectangle((M0 / 2, M0 / 2, SW - M0 / 2, SH - M0 / 2), outline="black", width=3)
    x0 = SW - CAR - M0 / 2; dr.line((x0, M0 / 2, x0, SH - M0 / 2), fill="black", width=3)
    blocos = [("MULBOT COREXY 200³", 46, True, 900), ("versão CoreXY da Mulbot DL1", 26, False, 520),
              (f"{datetime.date.today():%d/%m/%Y}", 26, False, 260), (f"FOLHA: {fid}", 34, True, 330), (f"TÍTULO: {titulo}", 34, True, 0)]
    y = M0 / 2
    for i, (t, s, b, h) in enumerate(blocos):
        if h == 0: h = SH - M0 / 2 - y
        txt = Image.new("RGBA", (int(h), CAR - 10), (255, 255, 255, 0)); d2 = ImageDraw.Draw(txt)
        f = fonte(s, b); tw = d2.textlength(t, font=f)
        while tw > h - 30: s -= 2; f = fonte(s, b); tw = d2.textlength(t, font=f)
        d2.text(((h - tw) / 2, (CAR - 10 - s) / 2 - 4), t, font=f, fill="black")
        txt = txt.rotate(90, expand=True); img.paste(txt, (int(x0 + 5), int(y)), txt)
        y += h
        if y < SH - M0: dr.line((x0, y, SW - M0 / 2, y), fill="black", width=3)

# ---------------- CXY-09: diagrama de ligacao (esquema desenhado)
LIG = [  # conector RAMPS, aparelho, rota (CXY-10)
    ("X", "Motor A (trás direito)", 2), ("Y", "Motor B (trás esquerdo)", 3), ("Z (2 conectores)", "Motores Z esq. e dir.", 4),
    ("E0", "Motor E (extrusora direta)", 9), ("D10", "Aquecedor do hotend 12 V", 9), ("D9", "Ventoinha 5015 (peça)", 9),
    ("D8", "Ventoinha do dissipador (ou 12 V direto)", 9), ("T0", "Termistor do hotend", 9), ("X-MIN", "Fim de curso X", 9),
    ("Y-MAX", "Fim de curso Y", 8), ("Z-MIN", "Fim de curso Z", 7), ("EXP1 / EXP2", "Display (adaptador + 2 cabos flat)", 6),
    ("12 V 11 A / 5 A", "Fonte 12 V 150 W", 5), ("-", "Tomada IEC C14 com chave > fonte (L, N, terra)", 5)]
def ligacoes(fd):
    img = Image.new("RGB", (SW, SH), "white"); dr = ImageDraw.Draw(img)
    f, fb, fg = fonte(30), fonte(32, True), fonte(44, True)
    W0 = SW - CAR - COLW - 3 * M0
    def caixa_(x, y, w, h, t, cor="#f2f2f2", borda="black", sub=None):
        dr.rounded_rectangle((x, y, x + w, y + h), 18, fill=cor, outline=borda, width=4)
        ls = t.split("\n"); yy = y + h / 2 - 20 * len(ls) - (14 if sub else 0)
        ft = fb
        while max(dr.textlength(l, font=ft) for l in ls) > w - 24: ft = fonte(ft.size - 2, True)
        for l in ls: tw = dr.textlength(l, font=ft); dr.text((x + (w - tw) / 2, yy), l, font=ft, fill="black"); yy += 40
        if sub: tw = dr.textlength(sub, font=f); dr.text((x + (w - tw) / 2, yy + 2), sub, font=f, fill="#333")
    def fios(p0, p1, cores, esp=7):          # feixe reto (horizontal ou vertical), fios paralelos
        n = len(cores); hor = abs(p1[0] - p0[0]) > abs(p1[1] - p0[1])
        for i, c in enumerate(cores):
            o = (i - (n - 1) / 2) * (esp + 4)
            dr.line(((p0[0], p0[1] + o), (p1[0], p1[1] + o)) if hor else ((p0[0] + o, p0[1]), (p1[0] + o, p1[1])), fill=c, width=esp)
    MOT = ["#111", "#1a8f2e", "#1f5fd6", "#d21f1f"]; PWR = ["#d21f1f", "#111"]; SIN = ["#d21f1f", "#111", "#1a8f2e"]
    RX, RY, RW, RH = 700, 760, 760, 1060          # placa
    YM = [860, 1070, 1280, 1490]                  # motores (direita), alinhados com os drivers
    XT = [RX + 130, RX + 375, RX + 620]           # conectores de cima e de baixo
    pinos = {}
    def pino(nome, x, y):
        pinos[nome] = (x, y); w = max(130, dr.textlength(nome, font=f) + 30)
        dr.rectangle((x - w / 2, y - 26, x + w / 2, y + 26), fill="#222", outline="white", width=2)
        tw = dr.textlength(nome, font=f); dr.text((x - tw / 2, y - 18), nome, font=f, fill="white")
    # 1o os fios (ficam por baixo das caixas e conectores)
    XB = RX + RW + 330
    for y in YM: fios((RX + RW - 70, y), (XB, y), MOT)
    fios((RX + RW - 70, 1690), (XB, 1690), ["#111", "#111"])
    for x in XT: fios((x, RY + 30), (x, 540), PWR); fios((x, RY + RH - 30), (x, 2060), SIN)
    fios((520, 990), (RX + 70, 990), PWR + PWR, esp=8); fios((520, 1420), (RX + 70, 1420), ["#888", "#888"], esp=14)
    fios((300, 640), (300, 880), ["#8a5a00", "#1f5fd6", "#1a8f2e"], esp=8)
    dr.rounded_rectangle((RX, RY, RX + RW, RY + RH), 20, fill="#b3261e", outline="black", width=5)
    for t, yy, ff in (("RAMPS 1.4", RY + RH / 2 - 60, fg), ("+ Arduino Mega 2560", RY + RH / 2, fb)):
        tw = dr.textlength(t, font=ff); dr.text((RX + (RW - tw) / 2 - 40, yy), t, font=ff, fill="white")
    for n, y in zip(("X", "Y", "Z", "E0"), YM): pino(n, RX + RW - 70, y)
    pino("T0", RX + RW - 70, 1690)
    for n, x in zip(("D10", "D9", "D8"), XT): pino(n, x, RY + 30)
    for n, x in zip(("X-MIN", "Y-MAX", "Z-MIN"), XT): pino(n, x, RY + RH - 30)
    pino("12V", RX + 70, 990); pino("EXP1/2", RX + 90, 1420)
    for t, y in zip(("MOTOR A\n(trás direito)", "MOTOR B\n(trás esquerdo)", "MOTOR Z ESQ.\n+ MOTOR Z DIR.", "MOTOR E\n(extrusora)"), YM):
        caixa_(XB, y - 85, 380, 170, t, "#d9d9d9")
    caixa_(XB, 1620, 380, 140, "TERMISTOR\n(hotend)", "#e8e0c8")
    for t, x in zip(("AQUECEDOR\nHOTEND", "VENTOINHA\n5015 (peça)", "VENT. DO\nDISSIPADOR"), XT): caixa_(x - 118, 390, 236, 150, t, "#f5c9b8")
    for t, x in zip(("FIM DE\nCURSO X", "FIM DE\nCURSO Y", "FIM DE\nCURSO Z"), XT): caixa_(x - 118, 2060, 236, 140, t, "#f5d2d2")
    caixa_(80, 880, 440, 220, "FONTE 12 V\n150 W", "#e6e6e6")
    caixa_(80, 1310, 440, 220, "DISPLAY\nRepRapDiscount", "#c8d4f0", sub="adaptador + 2 flat")
    caixa_(80, 440, 440, 200, "TOMADA IEC C14\ncom chave", "#cfcfcf", sub="L, N, terra")
    dr.text((80, 2270), "Motores: preto/verde/azul/vermelho = bobinas A+ A- B+ B- (conferir no motor). Potência: vermelho = +12 V, preto = GND.", font=f, fill="black")
    dr.text((80, 2320), "Fins de curso: S / GND / + (o + só se a placa do fim de curso tiver LED).", font=f, fill="black")
    tabela(dr, SW - CAR - M0 - COLW, M0, "LIGAÇÕES NA RAMPS", [("CONECTOR", 260), ("APARELHO", 760), ("ROTA", 160)],
           [(a, b, f"CXY-10 nº {c}") for a, b, c in LIG])
    notas(dr, SW - CAR - M0 - COLW, fd["notas"])
    carimbo(img, dr, fd["id"], fd["titulo"])
    fn_out = f"{OUT}/{fd['id']} - {fd['arquivo']}.png"; img.save(fn_out, dpi=(300, 300)); print(fn_out); return fn_out
FOLHAS.append(dict(id="CXY-09", arquivo="Diagrama de ligacao", titulo="DIAGRAMA DE LIGAÇÃO", desenho=ligacoes,
     notas=["Firmware (Marlin): #define COREXY. Motor A no driver X, motor B no driver Y.",
            "Teste: G1 X+10 tem que andar só em X pra direita. Se andar em Y, troque os cabos A e B; se andar ao contrário, inverta INVERT_X_DIR / INVERT_Y_DIR.",
            "Fins de curso: X no MIN (X = -101,5), Y no MAX (Y = +152), Z no MIN (topo do curso da mesa).",
            "Os 2 motores Z vão nos 2 conectores do Z (em paralelo), sem driver extra.",
            "Sem mesa aquecida: a saída D8 fica pra ventoinha do dissipador (E0_AUTO_FAN_PIN 8) ou ligue a ventoinha direto em 12 V."]))
def capa(fd):
    img = Image.new("RGB", (SW, SH), "white"); dr = ImageDraw.Draw(img)
    her = Image.open("/home/lucas/corexy/final/render/heroi.png").convert("RGB")
    W0, H0 = SW - CAR - COLW - 3 * M0, SH - 2 * M0 - 260
    k = min(W0 / her.size[0], H0 / her.size[1]); her = her.resize((int(her.size[0] * k), int(her.size[1] * k)), Image.LANCZOS)
    img.paste(her, (M0 + (W0 - her.size[0]) // 2, M0 + 230 + (H0 - her.size[1]) // 2))
    dr.text((M0 + 30, M0 + 20), "MULBOT COREXY 200³", font=fonte(110, True), fill="#b3261e")
    dr.text((M0 + 36, M0 + 160), "versão CoreXY da Mulbot DL1: guia em V impressa, extrusora direta, quadro oco com passagem de cabos", font=fonte(36), fill="black")
    lin = [(f["id"], f["titulo"]) for f in FOLHAS if f["id"] != fd["id"]]
    tabela(dr, SW - CAR - M0 - COLW, M0, "FOLHAS DE MONTAGEM", [("FOLHA", 220), ("TÍTULO", 960)], lin, hl=56)
    notas(dr, SW - CAR - M0 - COLW, fd["notas"])
    carimbo(img, dr, fd["id"], fd["titulo"])
    fn_out = f"{OUT}/{fd['id']} - {fd['arquivo']}.png"; img.save(fn_out, dpi=(300, 300)); print(fn_out); return fn_out
FOLHAS.append(dict(id="CXY-00", arquivo="Capa e indice", titulo="CAPA E ÍNDICE", desenho=capa,
     notas=["Área de impressão 200 x 200 x 200 mm. Quadro, guias e fixadores impressos (M10 no chassi, M6 nas médias).",
            "Peças: pasta 02 STL para imprimir (separada pelos mesmos conjuntos destas folhas).",
            "Mulbot DL1 original: 3D Printing World. Esta versão CoreXY muda quadro, eixos, mesa e cabos."]))
FOLHAS.sort(key=lambda f: f["id"])

if __name__ == "__main__":
    for fd in FOLHAS:
        if SO and fd["id"] not in SO: continue
        (fd["desenho"] if "desenho" in fd else folha)(fd)
    if not SO:      # PDF com todas as folhas, na ordem
        fs = [Image.open(f"{OUT}/{fd['id']} - {fd['arquivo']}.png").convert("RGB") for fd in FOLHAS]
        fs[0].save(f"{OUT}/Mulbot CoreXY - desenhos de montagem.pdf", save_all=True, append_images=fs[1:], resolution=300)
        print("PDF", len(fs), "folhas")
