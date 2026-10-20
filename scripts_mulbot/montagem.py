# Montagem Mulbot DL1. Mundo: X direita, Y para tras, Z para cima, mm. Frente = -Y.
import sys; sys.path.insert(0, "/home/lucas/mulbot/scripts")
from asm import *
P = []   # (nome_instancia, peca, T, cor)
def add(nome, peca, T, cor): P.append((nome, peca, T, cor)); return T
CINZA, VERM, AZUL = "cinza", "verm", "azul"
RX = 69.45          # centro dos trilhos Y (+-)
YF, YB = -137.5, 137.5
# ---------- DL1-01 chassi Y
add("trilhoY_E", "DL1-01-01", place(rot("-X","-Y","Z"), (17.56,175.09,0), (-RX,YF,0)), CINZA)
add("trilhoY_D", "DL1-01-02", place(rot("-X","-Y","Z"), (11.55,264.44,0), (RX,YF,0)), CINZA)
add("conectorY_frente", "DL1-01-03", place(rot("-X","-Y","Z"), (-21.46,-6.94,0), (0,YF,0)), CINZA)
add("conectorY_tras", "DL1-01-04", place(rot("-Z","-X","Y"), (-6.78,-139.76,0), (RX,YB,41.28)), CINZA)
# ---------- DL1-02 portico Z
add("lateralZ_E", "DL1-02-03", place(rot("-X","-Y","Z"), (-8.73,-46.48,0), (-78.99,92.26,0)), CINZA)
add("lateralZ_D", "DL1-02-04", place(rot("-X","-Y","Z"), (-46.23,109.07,0), (78.95,92.26,0)), CINZA)
add("colunaZ_E", "DL1-02-01", place(rot("-Z","X","-Y"), (45.67,-10.9,7.94), (-193.0,109.72,141.29)), CINZA)
add("colunaZ_D", "DL1-02-02", place(rot("-Z","X","-Y"), (243.26,-10.95,7.94), (132.72,109.72,141.29)), CINZA)
add("travessaZ", "DL1-02-05", place(rot("-Z","X","-Y"), (-195.35,-31.43,9.52), (-126.855,108.14,365.89)), CINZA)
VT = "/home/lucas/mulbot/vit"; DV0 = "/home/lucas/mulbot/derived"
for lado, x in (("E", -7.29), ("D", 318.38)):
    Tm = place(rot("X","-Y","-Z"), (0,0,0), (x,204.11,122.24))
    add("suporteMotorZ_"+lado, "DL1-02-07", Tm, AZUL)
    eixo = (Tm @ np.r_[-155.52,197.58,0,1])[:3]
    add("fusoZ_"+lado, "DL1-02-06", place(rot("X","Y","Z"), (-29.735,90.775,0), (eixo[0],eixo[1],123.0)), VERM)
    add("motorZ_"+lado, VT+"/nema17.stl", place(rot("X","Y","Z"), (0,0,0), (eixo[0],eixo[1],122.24-6.8)), "aco")
    add("motorZ_"+lado+"_corpo", VT+"/nema17_corpo_preto.stl", place(rot("X","Y","Z"), (0,0,-0.0), (eixo[0],eixo[1],122.24-6.8+0.0)), "preto")
    add("eixoSpinner_"+lado, "DL1-02-18", place(rot("X","Y","Z"), (0.475,-0.645,0), (eixo[0],eixo[1],333-6.8)), CINZA)
    add("roboZ_"+lado, "DL1-02-17", place(rot("-X","-Y","Z"), (-10.96,-5.88,0), (eixo[0],eixo[1],333.2)), AZUL)
add("fonte", VT+"/fonte_rs150.stl", place(rot("X","Y","Z"), (0,0,0), (134.6,117.66,86.9)), "alu")
T_pf = add("protecaoFonte", "DL1-02-15", place(rot("-X","-Y","Z"), (0,0,0), (-29.4,346.23,48.0)), AZUL)
# ---------- DL1-01 acionamento Y (suporte motor, motor, pinhao)
TmY = place(rot("-Z","-X","Y"), (-1.3,2.31,7.91), (50.4,-14.32,40.4))
add("suporteMotorY", "DL1-01-07", TmY, VERM)
YM = (TmY @ np.r_[-17.3,59.1,22.23,1])[:3] + [-0.7,0,0]   # centro do motor (ajustado no rasgo p/ engrenar)
add("motorY", VT+"/nema17.stl", place(rot("X","Y","Z"), (0,0,0), YM), "aco")
add("motorY_corpo", VT+"/nema17_corpo_preto.stl", place(rot("X","Y","Z"), (0,0,0), YM), "preto")
add("pinhaoY", "DL1-01-09", place(rotax("Z", 36), (7.86,-20.06,0), (YM[0],YM[1],64.5)), VERM)
# ---------- DL1-03 mesa (carro Y). YBED = posicao Y do centro da mesa
YBED = float(os.environ.get("YBED", 0.0))
ZC = 62.9          # Z do plano x=0 do carrinho (centraliza canais das esferas com os do trilho)
for lado, xr in (("E", -RX), ("D", RX)):
    Tc = place(rot("-Z","X","-Y"), (0,44.07,25.4), (xr, YBED, ZC))
    add("carroY_"+lado, "DL1-03-01", Tc, AZUL)
    T1 = np.eye(4); T1[:3,3] = (8.64, -9.08, -9.525)
    T2 = np.eye(4); T2[:3,:3] = np.diag([1,-1,-1.]); T2[:3,3] = (8.64, 97.23, 60.325)
    add("tampaY_"+lado+"1", "DL1-03-02", Tc @ T1, AZUL)
    add("tampaY_"+lado+"2", "DL1-03-02", Tc @ T2, AZUL)
ZB0 = ZC + 22.71   # topo do carrinho = fundo do suporte da mesa
add("suporteMesa", "DL1-03-04", place(rot("X","Y","Z"), (-17.9,-16.47,0), (0,YBED,ZB0)), VERM)
add("cremalheiraY", "DL1-03-03", place(rot("-X","Y","-Z"), (47.69,9.71,0), (9.53,YBED-109.81+16.47,ZB0)), AZUL)
ZBT = ZB0 + 9.525  # topo do suporte
MOLA = 12.0
ZLOC = ZBT + MOLA
ZVID = ZLOC + 6.35
add("vidro", VT+"/vidro.stl", np.diag([215.9/203.2, 215.9/203.2, 1, 1]) @ place(rot("X","Y","Z"), (0,0,0), (0,YBED*203.2/215.9,ZVID)), "vidro")
for k, (sx, sy) in enumerate(((1,-1), (1,1), (-1,1), (-1,-1))):
    ang = 90*k
    Rz = rotax("Z", ang)
    c = np.array([sx*92.3, YBED+sy*92.3, 0])
    add(f"knob_{k}", "DL1-03-05", place(rot("X","Y","Z"), (2.5,3.23,12.7), (c[0],c[1],ZB0)), AZUL)
    add(f"mola_{k}", VT+"/mola.stl", place(rot("X","Y","Z"), (0,0,0), (c[0],c[1],ZBT)) @ np.diag([1,1,MOLA/20.0,1]), "aco")   # mola comprimida
    Tl = place(Rz, (3.72,45.83,0), (c[0],c[1],ZLOC)); add(f"localizador_{k}", "DL1-03-06", Tl, "branco")
    anel = (Tl @ np.r_[25.6,24.0,0,1])[:3]
    Rcl = rotax("Z", 166+ang) @ np.diag([1,-1,-1.])
    add(f"presilha_{k}", "DL1-03-07", place(Rcl, (-122.2,58.0,6.35), (anel[0],anel[1],ZVID+3.3)), AZUL)
    add(f"porcaPresilha_{k}", "DL1-03-08", place(rot("X","Y","Z"), (-75.3,15.5,7.94), (anel[0],anel[1],ZLOC)), VERM)
# ---------- DL1-04 eixo X. ZX = altura (Z) da face inferior dos carros Z
ZX = float(os.environ.get("ZX", 160.0))
TzE = place(rot("-X","-Y","Z"), (6.875,-94.19,0), (-162.81,49.4,ZX)); add("carroZ_E", "DL1-04-01", TzE, VERM)
TzD = place(rot("-X","-Y","Z"), (-36.065,-139.68,0), (162.885,49.4,ZX)); add("carroZ_D", "DL1-04-02", TzD, VERM)
TxR = place(rot("X","-Y","-Z"), (0,0,0), (27.68,47.15,ZX+50.8)); add("trilhoX", "DL1-04-04", TxR, CINZA)
XPOS = float(os.environ.get("XPOS", 0.0))
YHX = -2.386 + 47.15          # centro da cabeca do trilho X (Y)
Th = place(rot("-Z","-Y","-X"), (-71.6,-129.06,25.4), (XPOS, YHX, ZX-17.46)); add("carroHotend", "DL1-04-03_HEAVY PRELOAD", Th, VERM)
Rz = np.eye(4); Rz[:3,:3] = np.diag([-1,-1,1.]); Rz[:3,3] = (-76.84,-84.99,0)   # quadro do carro Y -> carro hotend
T1 = np.eye(4); T1[:3,3] = (8.64, -9.08, -9.525)
T2 = np.eye(4); T2[:3,:3] = np.diag([1,-1,-1.]); T2[:3,3] = (8.64, 97.23, 60.325)
Tsw = np.eye(4); Tsw[:3,3] = (-129.21, 170.05, 0)
Bsw = np.eye(4); Bsw[:3,:3] = np.diag([1,-1,-1.]); Bsw[:3,3] = (-192.66,-245.94,60.325)   # 04-13 e espelho da 03-02, vai direto no carro do hotend (ponta -X)
add("tampaX_chave", "DL1-04-13", Th @ Bsw, AZUL)
add("tampaX", "DL1-03-02", Th @ Rz @ T1, AZUL)
HOT = (Th @ np.r_[-107.1,-81.43,25.4,1])[:3]   # topo do groove mount no eixo do hotend
add("hotend", VT+"/lite6.stl", place(rot("X","Y","Z"), (0,0,0), HOT), "alu")
add("hotend_bloco", VT+"/lite6_bloco.stl", place(rot("X","Y","Z"), (0,0,0), HOT+[0,0,0.01]), "alu")
add("hotend_bico", VT+"/lite6_bico.stl", place(rot("X","Y","Z"), (0,0,0), HOT+[0,0,0.01]), "latao")
Tcl = place(rot("-Z","-X","Y"), (8.12,-135.41,12.7), (XPOS, HOT[1], HOT[2]-6.35)); add("presilhaHotend", "DL1-04-07", Tcl, AZUL)
Tn = np.eye(4); Tn[:3,:3] = rot("-X","-Y","Z"); Tn[:3,3] = (78.07+XPOS, 31.42, ZX-31.75-10.8)
add("bicoRefrigeracao", "DL1-04-15", Tn, AZUL)
Tbc = np.eye(4); Tbc[:3,:3] = rot("-Z","-X","Y"); Tbc[:3,3] = (-102.48+XPOS, 8.24, ZX+59.95)
add("presilhaCorreia", "DL1-04-09", Tbc, AZUL)
# porcas Z (grease zerk para frente)
for lado, Tz in (("E", TzE), ("D", TzD)):
    p = (Tz @ np.r_[(-12.17 if lado == "E" else -55.11), (-51.45 if lado == "E" else -96.94), 0, 1])[:3]
    q = (Tz @ np.r_[(25.93 if lado == "E" else -17.01), (-51.45 if lado == "E" else -96.94), 0, 1])[:3]
    mid = (p+q)/2
    add("porcaZ_"+lado, "DL1-04-06", place(rot("-X","-Y","Z"), (99.54,-42.57,20.64), mid), AZUL)
# motor X (atras da placa do carro Z esquerdo, eixo para -Y)
MX = (TzE @ np.r_[59.25,-92.8,25.4,1])[:3]
add("motorX", VT+"/nema17.stl", place(rot("X","Z","-Y"), (0,0,0), MX), "aco")
add("motorX_corpo", VT+"/nema17_corpo_preto.stl", place(rot("X","Z","-Y"), (0,0,0), MX), "preto")
YPF = MX[1] - 10.0          # face frontal da placa do motor (Y)
YBELT = 8.24 + 16.75        # centro do rebaixo da presilha da correia (04-09)
add("poliaX", "DL1-04-08", place(rot("X","-Z","Y"), (-7.74,-100.09,15.0), (MX[0], YBELT, MX[2])), VERM)   # polia invertida: dentes centrados na correia
# suporte do esticador no carro Z direito
Tb = place(rot("Z","Y","-X"), (-26.98,-73.44,50.8), ((TzD @ np.r_[-61.45,-129.79,6.35,1])[:3]))
add("suporteEsticador", "DL1-04-10", Tb, VERM)
XID = 205.0
add("poliaLouca", "DL1-06-01", place(rot("X","-Z","Y"), (74.77,-119.42,18.1), (XID, YBELT, MX[2])), VERM)
add("eixoLoucaA", "DL1-06-02", place(rot("X","Z","-Y"), (63.5,-100.0,0), (XID, YBELT-18.1, MX[2])), VERM)
add("eixoLoucaB", "DL1-06-03", place(rot("X","-Z","Y"), (64.5,-140.5,0), (XID, YBELT+18.1, MX[2])), VERM)
for k, (yb, sg) in enumerate(((YBELT-18.1, 1), (YBELT+18.1, -1))):
    add(f"gaiolaLouca_{k}", "DL1-06-04", place(rot("X","-Z","Y") if sg > 0 else rot("X","Z","-Y"), (-13.41,4.45,0), (XID, yb+sg*1.0, MX[2])), AZUL)
    for j in range(6):
        a_ = np.radians(23.3+60*j) * (-1 if sg > 0 else 1)
        add(f"esferaLouca_{k}_{j}", VT+"/esfera45.stl", place(rot("X","Y","Z"), (0,0,0), (XID+6.6*np.cos(a_), yb+sg*5.0, MX[2]+6.6*np.sin(a_))), "aco")
XFL = (Tb @ np.r_[-7.93,-79.0,9.6,1])[:3]    # face interna do fundo do U
add("placaEsticador", "DL1-04-11", place(rot("Y","X","-Z"), (-39.3,-106.24,11.11), (XFL[0]-6.35-0.5, XFL[1], MX[2])), AZUL)
add("knobEsticador", "DL1-04-12", place(rot("-Z","Y","X"), (-12.94,-98.53,0), ((Tb @ np.r_[-7.93,-84.56,0,1])[:3])), VERM)
# correia X impressa em TPU (gerada no caminho real)
from correia import correia
_mb, _Lb = correia(MX[0], XID, MX[2], YBELT, XPOS-12.0, XPOS+12.0)
_mb.export("/home/lucas/mulbot/derived/correiaX_montada.stl")
add("correiaX", "/home/lucas/mulbot/derived/correiaX_montada.stl", np.eye(4), VERM)
# pes TPU (DL1-01-08, aparece como 02-08 na BOM)
for k, (x, y) in enumerate(((127.98,-147.03), (-127.97,-147.03), (-175.51,158.93), (-175.51,25.58), (175.57,158.93), (175.57,25.58))):
    add(f"pe_{k}", "DL1-01-08", place(rot("X","-Y","-Z"), (-58.32,7.1,0), (x, y, 0)), VERM)
# ventoinha 5015 deitada no verso da rampa do duto, saida descendo a rampa ate a entrada do duto (atras do trilho X)
_d = np.array([0, 40.0, 44.0]); _d /= np.linalg.norm(_d); _nb = np.array([0, _d[2], -_d[1]])
Rf = np.column_stack([np.cross(_d, _nb), _d, _nb])
P0 = (Tn @ np.r_[78.07, -42.0, 10.0, 1])[:3]
Tf = np.eye(4); Tf[:3,:3] = Rf; Tf[:3,3] = P0 + _d*45.0 + _nb*2.5 + np.array([-15.0, 0, 0])
add("ventoinha5015", VT+"/ventoinha5015.stl", Tf, "preto")
# ---------- DL1-05 display (na frente do conector Y frontal)
Tdb = place(rot("-X","-Y","Z"), (0,0,0), (18.1,-219.59,0)); add("displayBase", "DL1-05-01", Tdb, VERM)
_n = np.array([0, 0.5, np.sqrt(3)/2])          # normal da tampa (quadro da base)
_e1 = np.array([1.,0,0]); _e3 = -_n; _e2 = np.cross(_e3, _e1)
_u1 = np.array([np.cos(np.radians(-30)), np.sin(np.radians(-30)), 0]); _u2 = np.array([np.cos(np.radians(60)), np.sin(np.radians(60)), 0]); _u3 = np.array([0,0,1.])
OPT = int(os.environ.get("LIDOPT", 2)); SL = float(os.environ.get("LIDS", 23.0))
if OPT == 1:
    Rl = np.column_stack([_e1, _e2, _e3]) @ np.column_stack([_u1, _u2, _u3]).T; PL = np.array([-25.87, 0.66, 10.3])
else:
    Rl = np.column_stack([-_e1, -_e2, _e3]) @ np.column_stack([_u1, _u2, _u3]).T; PL = np.array([62.08, -55.92, 42.3])
Tl_ = np.eye(4); Tl_[:3,:3] = Rl; Tl_[:3,3] = PL + _n*SL - Rl @ np.array([-81.37, 14.66, 0])
add("displayTampa", "DL1-05-02", Tdb @ Tl_, VERM)
TL = Tdb @ Tl_
def lidT(Rloc, ploc):   # transform em coords locais da tampa
    t = np.eye(4); t[:3,:3] = Rloc; t[:3,3] = ploc; return TL @ t
_U1 = np.array([np.cos(np.radians(-30)), np.sin(np.radians(-30)), 0]); _U2 = np.array([np.cos(np.radians(60)), np.sin(np.radians(60)), 0]); _Z = np.array([0,0,1.])
Rlcd = np.column_stack([_U1, -_U2, -_Z])
add("lcd_placa", VT+"/lcd_placa.stl", lidT(Rlcd, (-27.0, 20.75, 18.7)), "pcb")
add("lcd_tela", VT+"/lcd_tela.stl", lidT(Rlcd, (-27.0, 20.75, 18.7)), "lcd")
add("lcd_moldura", VT+"/lcd_moldura.stl", lidT(Rlcd, (-27.0, 20.75, 18.69)), "preto")
Rout = np.column_stack([_U1, -_U2, -_Z])     # z da peca para fora da tampa
add("botaoReset", "DL1-05-03", lidT(Rout, (-2.19, 57.11, -0.3)) @ place(rot("X","Y","Z"), (41.24,-109.51,0), (0,0,0)), AZUL)
add("knobDisplay", "DL1-05-04", lidT(Rout, (26.39, 40.61, -0.5)) @ place(rot("X","Y","Z"), (27.58,-96.11,0), (0,0,0)), AZUL)
_Ab = np.array([-81.37, 14.66, 0]) + 20.0*_U1 + 76.4*_U2
add("roboDisplay", "DL1-05-05", lidT(np.column_stack([-_U2, -_U1, -_Z]), (_Ab[0], _Ab[1], 0.0)) @ place(rot("X","Y","Z"), (24.08,-11.15,0), (0,0,0)), AZUL)
DV = "/home/lucas/mulbot/derived"
Tbox = place(rot("-Z","-Y","-X"), (0,0,0), (-111.88,208.84,151.45))
add("caixaRAMPS", DV+"/DL1-02-09_caixa_ramps.stl", Tbox, VERM)
add("portaRAMPS", DV+"/DL1-02-10_porta_fechada.stl", Tbox, VERM)
import os, json
if os.environ.get("TESTE"):
    for i, c in enumerate(os.environ["TESTE"].split(";")):
        pc, rc, tc = c.split("|")
        T_ = np.eye(4); T_[:3,:3] = rot(*rc.split(",")); T_[:3,3] = [float(v) for v in tc.split(",")]
        add(f"teste{i}", pc, T_, ["verm","azul","preto","latao"][i])
# robos da mesa (sobre os blocos dos carrinhos)
for k, xr in enumerate((-RX, RX)):
    add(f"roboMesa_{k}", "DL1-05-05", place(rot("Y","-X","Z"), (24.08,-11.15,0), (xr, YBED, ZBT)), AZUL)
# cabeca de robo grande na porta da RAMPS
_mp = mesh(DV0+"/DL1-02-10_porta_fechada.stl").copy(); _mp.apply_transform(Tbox); _Xd = _mp.bounds[0][0]
add("roboGrande", "DL1-02-11", place(rot("-Y","Z","-X"), (-74.33,61.9,34.58), (_Xd, 163.25, 185.0)), AZUL)
# Arduino Mega + RAMPS dentro da caixa
Tmega = Tbox @ place(rot("X","Y","Z"), (13.97,2.54,0), (-28.92,23.71,31.3))
add("mega", VT+"/mega.stl", Tmega, "pcb"); add("ramps_pcb", VT+"/ramps_pcb.stl", Tmega, "pcb"); add("ramps_comp", VT+"/ramps_comp.stl", Tmega, "preto")
# tomada IEC na protecao da fonte
_pi = (T_pf @ np.r_[-205.91, 180.0, 27.5, 1])[:3]
add("tomadaIEC", VT+"/iec_c14.stl", place(rot("Y","Z","X"), (0,0,0), _pi), "preto")
# suporte da extrusora + EZR (motor do lado de fora, eixo acima da placa)
Tex = place(rot("-Z","Y","X"), (-26.49,-47.09,12.7), (-175.54,117.66,346.84)); add("suporteExtrusora", "DL1-02-16", Tex, VERM)
_ezc = np.array([-188.24, 146.61, 346.84-15.5])     # placa | corpo EZR | motor (parafusos M3x35 atravessam)
RzE = rot("Y","Z","X")                                 # z do modelo -> +X
add("ezr_corpo", VT+"/ezr_corpo.stl", place(rot("Y","-Z","-X"), (0,0,0), _ezc), AZUL)
add("motorE", VT+"/nema17.stl", place(RzE, (0,0,0), _ezc - [25.0,0,0]), "aco")
add("motorE_corpo", VT+"/nema17_corpo_preto.stl", place(RzE, (0,0,0), _ezc - [25.0,0,0]), "preto")
add("roboExtrusora", "DL1-02-14", place(rot("X","Y","Z"), (-31.9,102.24,8.25), _ezc - [25.0+40.0+13.0,0,0]), AZUL)
# alivio de tensao dos cabos (coluna esquerda, face traseira)
Tws = place(rot("-Z","-X","Y"), (-56.63,-0.95,0), (-193.0,117.66,271.85)); add("alivioBase", "DL1-02-13", Tws, AZUL)
R180 = np.eye(4); R180[:3,:3] = np.diag([-1,-1,1.]); R180[:3,3] = (-89.47,-8.83,7.94)
add("alivioTampa", "DL1-02-12", Tws @ R180, AZUL)
# batentes Y nas pontas dos trilhos
for k, xr in enumerate((-RX, RX)):
    add(f"batenteY_f{k}", "DL1-01-06", place(rot("X","-Z","Y"), (12.17,4.98,8.9), (xr,-137.5,60.32)), AZUL)
    add(f"batenteY_t{k}", "DL1-01-06", place(rot("X","Z","-Y"), (12.17,4.98,8.9), (xr,137.5,60.32)), AZUL)
# fins de curso
add("fimCursoY_pcb", VT+"/endstop_pcb.stl", place(rot("X","Y","Z"), (0,0,0), (-44.7,140.5,52.39)), "verm")
add("fimCursoY", VT+"/endstop_chave.stl", place(rot("X","Y","Z"), (0,0,0), (-44.7,140.5,52.39)), "preto")
add("fimCursoZ_pcb", VT+"/endstop_pcb.stl", place(rot("Y","-Z","-X"), (0,0,0), (-201.1,50.33,157.34)), "verm")
add("fimCursoZ", VT+"/endstop_chave.stl", place(rot("Y","-Z","-X"), (0,0,0), (-201.1,50.33,157.34)), "preto")
# fitas de LED (trilho X e travessa superior)
add("ledX", VT+"/led_fita.stl", place(rot("X","Z","-Y"), (120,0,0), (0, 35.2, ZX+42.0)), "branco")
add("ledTopo", VT+"/led_fita.stl", place(rot("X","-Y","-Z"), (120,0,0), (0, 92.0, 365.88)), "branco")
# tubo bowden (extrusora -> hotend)
from correia import tubo
_bt = tubo([(_ezc[0]-12, _ezc[1]-8, _ezc[2]+30), (_ezc[0]-14, _ezc[1]-20, 405), (-120, 30, 425), (XPOS-30, HOT[1]+5, HOT[2]+120), (XPOS, HOT[1], HOT[2]+35), (XPOS, HOT[1], HOT[2]+2)], r=2.0)
_bt.export(DV0+"/bowden_montado.stl"); add("bowden", DV0+"/bowden_montado.stl", np.eye(4), "azul")
# ---------- esferas 4.5 mm recirculantes (28 por circuito, 4 circuitos por rolamento = 112)
def circuito(L, R, n=28, z0=0.0, z1=50.8):
    L = np.array(L, float); R = np.array(R, float); c = (L+R)/2; r = np.linalg.norm(L-R)/2; e = (L-R)/(2*r)
    seg = [("lin", L, z0, z1), ("arc", c, z1, +1), ("lin", R, z1, z0), ("arc", c, z0, -1)]
    Ltot = 2*(z1-z0) + 2*np.pi*r; pts = []
    for i in range(n):
        s_ = (i+0.5)*Ltot/n
        if s_ < (z1-z0): pts.append((L[0], L[1], z0+s_)); continue
        s_ -= (z1-z0)
        if s_ < np.pi*r:
            a_ = s_/r; q = c + r*np.cos(a_)*e; pts.append((q[0], q[1], z1 + r*np.sin(a_))); continue
        s_ -= np.pi*r
        if s_ < (z1-z0): pts.append((R[0], R[1], z1-s_)); continue
        s_ -= (z1-z0); a_ = s_/r; q = c - r*np.cos(a_)*e; pts.append((q[0], q[1], z0 - r*np.sin(a_)))
    return pts
CY = [((-5.64,34.32),(-8.72,25.39)), ((0.75,34.32),(3.97,25.39)), ((-5.64,53.82),(-8.72,62.76)), ((0.75,53.82),(3.97,62.76))]
def esferas(nome, Tc, circ):
    k_ = 0
    for L, R in circ:
        for p in circuito(L, R):
            add(f"esfera_{nome}_{k_:03d}", VT+"/esfera45.stl", Tc @ place(rot("X","Y","Z"), (0,0,0), p), "aco"); k_ += 1
for lado in ("E", "D"):
    esferas("carroY_"+lado, T_[lado] if False else [t for n_, p_, t, c_ in P if n_ == "carroY_"+lado][0], CY)
CH = [((-71.21,-138.81),(-68.12,-147.74)), ((-77.6,-138.81),(-80.81,-147.74)), ((-71.21,-119.31),(-68.12,-110.37)), ((-77.6,-119.31),(-80.81,-110.37))]
esferas("carroHotend", Th, CH)
for lado, Tz, (cx, cy) in (("E", TzE, (-37.195,-99.55)), ("D", TzD, (-80.135,-145.05))):
    M4 = np.array([[0,1,0,cx],[-1,0,0,cy],[0,0,1,0],[0,0,0,1.]])
    add(f"tampaZ_{lado}1", "DL1-03-02", Tz @ M4 @ T1, AZUL)
    add(f"tampaZ_{lado}2", "DL1-03-02", Tz @ M4 @ T2, AZUL)
    esferas("carroZ_"+lado, Tz @ M4, CY)
# calha de fios entre os trilhos Y (ganchos nos furos quadrados, atras do suporte do motor)
add("calhaFios", "DL1-01-05", place(rot("X","Y","Z"), (-62.55,6.5,0), (0, 53.1, -7.5)), AZUL)
# fim de curso X (no carro Z esquerdo, atras do trilho) + espacador da bandeira (bico envolvente)
add("fimCursoX_pcb", VT+"/endstop_pcb.stl", place(rot("X","-Y","Z") @ rot("X","Z","-Y") if False else rot("X","Z","-Y"), (0,0,0), (-118.0, 66.5, ZX+33.0)), "verm")
add("fimCursoX", VT+"/endstop_chave.stl", place(rot("X","Z","-Y"), (0,0,0), (-118.0, 66.5, ZX+33.0)), "preto")
add("espacadorChaveX", "DL1-04-05", place(rot("X","Y","Z"), (3.65,-12.26,8.6), (XPOS-34.9, 55.95, ZX+27.0)), AZUL)
# ---------- versao modificada (parafusos impressos): MOD=1 usa pecas de ~/mulbot/mod e adiciona os fixadores
if os.environ.get("MOD") and not os.environ.get("MOD_BUILD"):
    import glob as _g
    for fj in sorted(_g.glob("/home/lucas/mulbot/mod/etapa*.json")):
        _E = json.load(open(fj)) if "json" in dir() else __import__("json").load(open(fj))
        for i_, (n_, p_, t_, c_) in enumerate(P):
            if n_ in _E["pecas"]: P[i_] = (n_, _E["pecas"][n_], t_, c_)
        for a_, f_, t_, c_ in _E["fix"]: add(a_, f_, np.array(t_), c_)
T = {n: t for n, p, t, c in P}; PART = {n: p for n, p, t, c in P}
def chk(a, b, **k):
    r = coax(PART[a], T[a], PART[b], T[b], **k)
    best = {}
    for off, da, db, p, gap in r:
        key = tuple(np.round(p, 0))
        if key not in best or abs(gap) < abs(best[key][-1]): best[key] = (float(off), da, db, gap)
    # agrupa por linha de eixo
    lines = {}
    for p, v in best.items():
        lk = tuple(round(c/2) for c in p)
        if lk not in lines or abs(v[-1]) < abs(lines[lk][1][-1]): lines[lk] = (p, v)
    print(f"{a} x {b}: {len(lines)} eixos coaxiais")
    for p, v in lines.values(): print(f"    em {p}  off={v[0]:.2f} dA={v[1]} dB={v[2]} gap={float(v[3])}")
if __name__ == "__main__":
    for a,b in [("trilhoY_E","lateralZ_E"),("trilhoY_D","lateralZ_D"),("lateralZ_E","colunaZ_E"),("lateralZ_D","colunaZ_D"),("colunaZ_E","travessaZ"),("colunaZ_D","travessaZ")]: chk(a,b)
def export(fn="/home/lucas/mulbot/out/montagem.json", so=None):
    import json
    L = []
    for n, p, t, c in P:
        if so and not any(s in n for s in so): continue
        f = p if p.startswith("/") else f"{MD}/{p}.stl"
        b = os.path.basename(f)
        g = {"DL1-01": "DL1-01 Chassi Y", "DL1-02": "DL1-02 Portico Z", "DL1-03": "DL1-03 Mesa", "DL1-04": "DL1-04 Eixo X",
             "DL1-05": "DL1-05 Display", "DL1-06": "DL1-06 Polia louca"}.get(b[:6], "Comprados (modelos simplificados)")
        if b.startswith("correiaX"): g = "DL1-04 Eixo X"
        L.append(dict(nome=n, stl=f, T=np.asarray(t).tolist(), cor=c, grupo=g, peca=b[:-4]))
    json.dump(L, open(fn, "w")); return fn
if __name__ == "__main__" and "export" in sys.argv: export()
def world_lines(excl=()):
    from matcher import lines
    W = []
    for n, p, t, c in P:
        if n in excl: continue
        for ax, pp, cl, lo, hi in lines(p, t): W.append((n, ax, pp, cl, lo, hi))
    return W
def find(part, minn=3, top=8, near=None):
    from matcher import match, ROTS, lines
    W = world_lines()
    if near: W = [w for w in W if any(s in w[0] for s in near)]
    for nb, ri, ax, t, names, v in match(part, W, minn=minn, top=top):
        R = ROTS[ri]
        cols = ["".join(("-" if R[:,i][j] < 0 else "") + "XYZ"[j] for j in range(3) if R[:,i][j] != 0) for i in range(3)]
        # alcance axial dos furos casados
        wr = [(x[1][4], x[1][5]) for x in v]; 
        Bl = lines(part, np.block([[R, np.zeros((3,1))],[np.zeros((1,3)),1]]))
        br = [(Bl[x[0]][3], Bl[x[0]][4]) for x in v] if False else None
        print(f"{nb} furos | rot({cols}) eixo={'XYZ'[ax]} t_perp={np.round(t,2).tolist()} com {names}  faixa_mundo={np.round(wr[0],1).tolist()}")
if __name__ == "__main__" and "find" in sys.argv:
    i = sys.argv.index("find"); find(sys.argv[i+1], minn=int(sys.argv[i+2]) if len(sys.argv) > i+2 else 3)
def interf_all(part, T, excl=(), minv=1.0):
    """interferencia de part(T) com todas as pecas colocadas (bbox overlap)"""
    m = mesh(part).copy(); m.apply_transform(T); bb = m.bounds
    out = []
    for n, p, t, c in P:
        if n in excl: continue
        mm = mesh(p).copy(); mm.apply_transform(t); b2 = mm.bounds
        if np.any(bb[1] < b2[0]) or np.any(b2[1] < bb[0]): continue
        v = interf(part, T, p, t)
        if v > minv: out.append((n, round(v,1)))
    return out
def solve(part, rotcols, ax, tperp, excl=()):
    """acha deslocamento axial: candidatos pelos furos casados; testa interferencia"""
    from matcher import lines
    R = rot(*rotcols); T0 = np.eye(4); T0[:3,:3] = R; T0[:3,3] = tperp
    a = "XYZ".index(ax)
    B = [l for l in lines(part, T0) if l[0] == a]
    W = [w for w in world_lines() if w[1] == a]
    cands = set()
    for b in B:
        for w in W:
            if np.linalg.norm(b[1]-w[2]) < 0.5 and (b[2] & w[3]):
                cands.add(round(w[5]-b[3], 1)); cands.add(round(w[4]-b[4], 1))
    res = []
    def vol(s):
        T = T0.copy(); T[a,3] += s; r = interf_all(part, T, excl, minv=0.05); return sum(v for n, v in r), r
    for s0 in sorted(cands):
        v0, r0 = vol(s0)
        if v0 == 0:
            # aproxima ate encostar (ambos lados) -> lado que encosta em <=2mm
            best = s0
            for d in (1, -1):
                lo, hi = 0.0, 2.0
                if vol(s0 + d*hi)[0] == 0: continue
                for _ in range(10):
                    mid = (lo+hi)/2
                    if vol(s0 + d*mid)[0] == 0: lo = mid
                    else: hi = mid
                res.append((round(s0 + d*lo, 2), vol(s0 + d*lo)[1], "encosta"))
            res.append((s0, r0, "livre"))
        else:
            # recua ate zerar nos dois sentidos
            for d in (1, -1):
                lo, hi = 0.0, 4.0
                if vol(s0 + d*hi)[0] > 0: continue
                for _ in range(12):
                    mid = (lo+hi)/2
                    if vol(s0 + d*mid)[0] > 0: lo = mid
                    else: hi = mid
                res.append((round(s0 + d*hi, 2), vol(s0 + d*hi)[1], f"recuo{d*hi:+.2f}"))
    for s, r, k in res: print(f"  desloc {ax}={s}: {k} interf {r}")
    return res
if __name__ == "__main__" and "solve" in sys.argv:
    i = sys.argv.index("solve"); a = sys.argv[i+1:]
    solve(a[0], a[1].split(","), a[2], [float(x) for x in a[3].split(",")])
