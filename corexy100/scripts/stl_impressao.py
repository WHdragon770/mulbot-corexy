# Monta a pasta "02 STL para imprimir" a partir do out/cxy.json (rodar cxy.py com ESFERAS=0 antes), separada por conjunto da maquina
# Eixo Z novo (fuso, porca, roldana com rolamento impresso, bucha) sai deitado p/ impressao em 2 versoes: FDM e Resina
# python3 stl_impressao.py <pasta_destino>
import sys, os, json, csv, shutil, collections, numpy as np
sys.path.insert(0, "/home/lucas/corexy100/scripts")
from base import Tm, tr, DER, VT
import zv

DST = sys.argv[1]
J = json.load(open("/home/lucas/corexy100/out/cxy.json"))
Z_NOVO = ("fusoZ_", "porcaZ_", "rodaZ", "buchaZ", "rodaX", "rodaY", "buchaX", "buchaY")   # saem nas pastas por material
# pastas por conjunto da maquina (na ordem de montagem); a chave e o comeco do nome na montagem (antes do 1o "_")
G_QUA, G_Y, G_X, G_Z, G_MOT, G_ELE = "01 Quadro", "02 Eixo Y e portico", "03 Eixo X e cabeca", "04 Eixo Z e mesa", "05 Motores e polias", "06 Eletronica e display"
G_ROL, G_FIX = "07 Roldanas V (X, Y e Z) - Resina", "08 Parafusos e porcas impressos"
G_EST = "09 Esteira porta-cabos"
CONJ = {G_QUA: ("baseFrente", "baseTras", "baseLatF", "baseLatT", "posteFrenteInf", "posteFrenteSup", "posteTrasInf", "posteTrasSup",
                "travFrente", "travTras", "torreFrente", "torreTras", "pe"),
        G_Y: ("trilhoY", "suportePortico"),
        G_X: ("trilhoX", "carroX", "bracoFimCursoX", "dutoCoreXY", "suporteExtrusoraDireta", "presilhaHotend"),
        G_Z: ("baseZ", "baseZInf", "baseZSup", "trilhoZ", "chapaZY", "bracoMesa", "mesa", "calcoFimCursoZ"),
        G_MOT: ("loucaFrente", "loucaPortico", "motorA", "motorB"),
        G_EST: ("eloX", "eloY", "pontaFixaX", "pontaFixaY", "bandejaX", "bandejaY", "bracoEsteiraX", "suporteEsteiraY"),
        G_ELE: ("caixaRAMPS", "portaRAMPS", "roboGrande", "protecaoFonte", "protecaoFonte360", "displayBase", "displayTampa", "botaoReset", "knobDisplay", "roboDisplay")}
GRUPO = {k: g for g, ks in CONJ.items() for k in ks}
def origem(f): return "Mulbot original" if "/mulbot/" in f else "Mulbot modificada" if os.path.basename(f).startswith("DL1-") else "nova"
cont = collections.OrderedDict()
for e in J:
    n, f = e["nome"], e["stl"]
    if n.startswith(Z_NOVO + ("esfera", "correia", "bowden", "caboEsteira", "mesa_aquecida", "fonte", "moduloMOSFET")) or f.startswith(VT): continue   # correias, bowden, mesa aquecida e fonte sao comprados
    g = G_FIX if "/fixadores/" in f else GRUPO.get(n.split("_")[0], "10 Outros")
    if g == "10 Outros": print("AVISO sem conjunto:", n)
    cont.setdefault((g, f), 0); cont[(g, f)] += 1
linhas = []   # (pasta, peca, qtd, material, origem)
for (g, f), q in cont.items():
    os.makedirs(f"{DST}/{g}", exist_ok=True)
    base = os.path.splitext(os.path.basename(f))[0]
    shutil.copy(f, f"{DST}/{g}/{base} [{q}x].stl"); linhas.append((g, base, q, "FDM", origem(f)))

# ---------- eixo Z: pecas no lugar de impressao, por material
RODAS = sum(1 for e in J if e["nome"].startswith(("rodaZ_", "rodaX_", "rodaY_")) and not e["nome"].endswith("_roletes"))
NB = lambda p: sum(1 for e in J if e["nome"].startswith(p))
# ---------- roldanas V (X, Y e Z): rolamento de roletes impresso em RESINA, 1 peca so (pontes de quebra) + buchas excentricas
g = f"{DST}/{G_ROL}"; os.makedirs(g, exist_ok=True)
for m, nome, q in ((zv.roldana_resina().translate([0, 0, zv.HW]), "roldanaV_rolamento_1peca_resina", RODAS),
                   (zv.bucha_esp(3.0, "resina").translate([0, 0, 3.0]), "buchaX_excentrica_espacador", NB("buchaX")),
                   (zv.bucha_esp(8.0, "resina").translate([0, 0, 8.0]), "buchaY_excentrica_espacador", NB("buchaY_")),
                   (zv.bucha(11.5, "resina").translate([0, 0, 4.0]), "buchaZ_excentrica", NB("buchaZ_"))):
    Tm(m).export(f"{g}/{nome} [{q}x].stl"); linhas.append((G_ROL, nome, q, "Resina", "nova"))
BUCHAS = sum(1 for e in J if e["nome"].startswith("buchaZ_"))
Tf = tr((29.735, -90.775, 0))                     # DL1-02-06_longo: eixo no centro, cubo em z = 0
for mat, pasta in (("fdm", G_Z + "/Fuso e porca - FDM"), ("resina", G_Z + "/Fuso e porca - Resina (alternativa)")):
    g = f"{DST}/{pasta}"; os.makedirs(g, exist_ok=True)
    def sv(m, nome, q):
        Tm(m).export(f"{g}/{nome} [{q}x].stl"); linhas.append((pasta, nome, q, "FDM" if mat == "fdm" else "Resina", "nova"))
    f, eixo = zv.fuso(Tf, mat)
    p = zv.porca(np.eye(4), (99.5354, -42.5672), mat)
    sv(p.translate([-99.5354, 42.5672, 0]), "porcaZ_DL1-04-06_rosca_nova", 2)
    if mat == "fdm":
        sv(f, "fusoZ_250mm", 2)
    else:                                         # 2 metades de 125 mm (cabe em Photon Mono M7 Pro) + pino D
        a, b2, pino = zv.divide_fuso(f, eixo, 125.0, mat)
        sv(a, "fusoZ_metade_baixo_125mm", 2); sv(b2.translate([0, 0, -125.0]), "fusoZ_metade_cima_125mm", 2)
        sv(pino.translate([0, 0, -(125.0 - zv.PINO_L / 2)]), "fusoZ_pino_D", 2)
with open(f"{DST}/lista_de_impressao.csv", "w", newline="", encoding="utf-8-sig") as fh:
    w = csv.writer(fh, delimiter=";"); w.writerow(["pasta", "peca", "qtd", "material", "origem", "impresso"])
    for l in sorted(linhas, key=lambda l: (l[0], l[1])): w.writerow(list(l) + [""])
for g in sorted({l[0] for l in linhas}):
    print(f"{g}: {sum(1 for l in linhas if l[0] == g)} arquivos, {sum(l[2] for l in linhas if l[0] == g)} pecas")
