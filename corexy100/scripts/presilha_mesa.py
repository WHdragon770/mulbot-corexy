# Trava baixa do vidro (substitui o ganchinho DL1-03-07): aba chata giratoria, 2.4 mm acima do vidro.
# Reaproveita o pino roscado da DL1-03-07 e a porca serrilhada DL1-03-08. Girar 90 graus solta o vidro.
# Saida: derived/presilha_baixa.stl no mesmo quadro local da DL1-03-07 (as 4 transformacoes da Mulbot continuam valendo)
import sys, os, json; sys.path.insert(0, "/home/lucas/corexy100/scripts")
from base import *
import manifold3d as mf

J = {j["nome"]: j for j in json.load(open("/home/lucas/corexy100/out/cxy.json"))}
T1 = np.array(J["mesa_presilha_1"]["T"])        # canto +X+Y, em coordenadas de mundo
HM = float(os.environ.get("HM", 0))            # mesa aquecida: placa de HM mm entre o localizador e o vidro (scripts/mesa_aquecida.py)
SUF = "_aq" if HM else ""
ZLOC = 389.05 - T1[2, 3]; ZVID = 389.81 + HM - T1[2, 3]   # topo do localizador e do vidro, relativos a T1 (independe da pose da mesa)
Ti = np.linalg.inv(T1)[:3].tolist()
original = peca_mf(J["mesa_presilha_1"]["stl"], np.eye(4))   # fica no quadro local: transformar a rosca arredonda vertices e abre a malha
z0 = T1[2, 3]
ZL, ZV = z0 + ZLOC, z0 + ZVID
P = np.array([123.15, 123.15])                  # eixo do pino
Q = np.array([114.6, 114.6])                    # centro da aba em cima do canto do vidro (canto em 117.5)
H = 2.4                                         # espessura da aba acima do vidro
PRE = 0.25                                      # aperto do calco no vidro (a aba flexiona)

pino = original ^ caixa((P[0] - 10, P[1] - 10, z0 - 50), (P[0] + 10, P[1] + 10, ZL - 0.05)).transform(Ti)   # corta 0.05 abaixo da face do colar (no plano dela sobra triangulo degenerado)
pino = max(pino.decompose(), key=lambda c: c.volume())   # descarta lasca do gancho antigo que descia abaixo do localizador
def disco(c, r, za, zb, r1=None): return cil((c[0], c[1], za), (c[0], c[1], zb), r, 64, r1)
CH = 0.6
aba = (disco(P, 6.5, ZV + 0.05, ZV + 0.05 + H - CH) + disco(Q, 4.5, ZV + 0.05, ZV + 0.05 + H - CH)).hull()
aba += (disco(P, 6.5, ZV + H - CH, ZV + 0.05 + H, 5.9) + disco(Q, 4.5, ZV + H - CH, ZV + 0.05 + H, 3.9)).hull()
espacador = disco(P, 6.0, ZL, ZV + 0.6) + disco(P, 5.6, ZL - 0.3, ZL + 0.1)   # pescoco r5.6 entra no pino (r6) e solda; r6 sem sobrepor a parede do pino (cilindros coincidentes abrem a malha)
calco = disco(Q, 3.2, ZV - PRE, ZV + 0.1, 4.2)   # cone: entra no vidro rampando quando gira
def fecha(novo, nome):
    # pecas novas (feitas no mundo) vao pro quadro local e unem no pino; confere que sai 1 corpo fechado
    m = pino + novo.transform(Ti)
    m = mf.Manifold.batch_boolean([c for c in m.decompose() if c.volume() > 0.01], mf.OpType.Add)
    assert len(m.decompose()) == 1, nome + " em pedacos"
    t = Tm(m.simplify(1e-3)); assert t.is_watertight, nome + " aberta"   # mesma malha que o salva() grava
    return salva(m, nome)
m = espacador + aba + calco
if not HM:                                      # mesa aquecida: so o disco (padrao)
    fn = fecha(m, "presilha_baixa" + SUF)
    print(fn, "topo acima do vidro:", round(H + 0.05, 2), "mm (original 6.35)")

# ---------- disco: botao excentrico serrilhado. Centro deslocado E do pino para dentro do vidro; meia volta solta.
d = np.array([-1.0, -1.0]) / np.sqrt(2)          # do pino para o canto do vidro
E, R, HD = 4.5, 10.8, 3.2                        # excentricidade, raio (cobre o espacador r6 do lado de fora), altura acima do vidro
C = P + E * d
N = 72
ang = np.linspace(0, 2 * np.pi, 2 * N, endpoint=False)
rr = np.where(np.arange(2 * N) % 2 == 0, R, R - 0.6)   # serrilhado na borda
estrela = mf.CrossSection([np.column_stack([C[0] + rr * np.cos(ang), C[1] + rr * np.sin(ang)]).tolist()])
z1 = ZV + 0.05
disco_m = mf.Manifold.extrude(estrela, HD - 0.8).translate([0, 0, z1])
disco_m += cil((C[0], C[1], z1 + HD - 0.8), (C[0], C[1], z1 + HD), R - 0.7, 96, R - 1.5)   # topo chanfrado (r abaixo do fundo do serrilhado: nao coincide)
disco_m -= cil((C[0], C[1], z1 + HD - 0.5), (C[0], C[1], z1 + HD + 1), R - 3.2, 96)        # rebaixo raso no topo
seta = (   # risco em relevo apontando para o vidro: mostra se esta travado
    disco(P + 5.0 * d, 0.9, z1 + HD - 0.6, z1 + HD - 0.1) + disco(P + 10.0 * d, 0.9, z1 + HD - 0.6, z1 + HD - 0.1)).hull()
CQ = P + 11.0 * d                                # calco sobre o vidro (canto em 8.0 do pino)
fn = fecha(espacador + disco_m + seta + disco(CQ, 2.2, ZV - PRE, ZV + 0.1, 3.0), "presilha_disco" + SUF)
print(fn, "sobre o vidro:", round(E + R - 8.0, 1), "mm no canto; solto apos meia volta, folga", round(8.0 + E - R, 1), "mm")

