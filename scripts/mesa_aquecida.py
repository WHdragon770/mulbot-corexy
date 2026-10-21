# Mesa aquecida (MESA=220 ou MESA=235; MESA=fria = vidro direto no localizador, como a Mulbot)
#   235: placa de aluminio 235x235x3 24 V (mesa da Ender 3) entra no lugar do vidro no bolso dos 4 localizadores; vidro por cima
#   220: placa de aluminio 220x220x3 12 V; calco em L no localizador (mesma altura da placa) segura o canto dela e apoia o canto do vidro
# O topo do vidro fica onde estava (bico); tudo abaixo desce HM. Bordas do localizador sobem HM p/ continuar travando o vidro
# (menos em volta do pino da presilha); a presilha ganha HM no espacador (presilha_mesa.py com HM).
# Localizador encosta na placa quente: imprimir em ASA/ABS (PETG so ate ~70 graus na mesa).
import os, subprocess, numpy as np, manifold3d as mf
from base import caixa, cil, salva, mesh, M, DER

MESA = os.environ.get("MESA", "fria")
LADO = {"220": 220.0, "235": 235.0}.get(MESA)
HM = 3.0 if LADO else 0.0                  # espessura da placa de aluminio
TENSAO = {"220": "12V", "235": "24V"}.get(MESA)
PINO = np.array([123.15, 123.15])          # eixo do pino da presilha no canto +X+Y (mundo)
FOLGA = 0.4

def _sobe(m, dz, passo=1.0):
    """extruda m pra cima ate dz empilhando copias (m tem que ser mais grosso que o passo)"""
    r = m
    for k in range(1, int(np.ceil(dz / passo)) + 1): r += m.translate([0, 0, min(k * passo, dz)])
    return r

def localizador(T1, zchao):
    """DL1-03-06 com bordas mais altas (+ calco p/ a placa de 220). T1 = transformacao do localizador_1 (canto +X+Y);
    zchao = fundo do bolso no mundo. Devolve o arquivo no quadro local da peca."""
    fn = f"{DER}/localizador_aq{MESA}.stl"
    m = M(mesh("DL1-03-06").copy().apply_transform(T1))
    borda = m ^ (caixa((80, 80, zchao + 0.1), (140, 140, zchao + 3)) - cil((*PINO, zchao - 1), (*PINO, zchao + 5), 8.0))
    novo = m + _sobe(borda, HM)
    novo -= caixa((80, 80, zchao), (117.5 + 0.2, 117.5 + 0.2, zchao + HM + 6))   # bolso p/ 235 nominal (o original prensava 0,09 mm)
    if LADO == 220.0:
        chao = _sobe(m ^ caixa((80, 80, zchao - 0.6), (140, 140, zchao - 0.1)), HM + 0.1, 0.4).translate([0, 0, 0.1])
        a, b = LADO / 2 + FOLGA, 117.5 - FOLGA             # do canto da placa ate a parede do vidro
        L = caixa((a, 80, zchao - 1), (b, b, zchao + HM)) + caixa((80, a, zchao - 1), (b, b, zchao + HM))
        novo += chao ^ L
    novo = novo.transform(np.linalg.inv(T1)[:3].tolist())
    p = [c for c in novo.decompose() if c.volume() > 0.05]      # descarta lascas de 0,01 mm3 das copias empilhadas
    assert len(p) == 1, "localizador em pedacos"; novo = p[0]
    return salva(novo, f"localizador_aq{MESA}")

def placa(zv):
    """placa de aluminio (zv = fundo do vidro) com os 4 furos M3 dos cantos (furos da 235 aproximados)"""
    h = LADO / 2; c = h - (5.5 if LADO == 220.0 else 9.0); r = 4.0       # cantos arredondados (entra no canto do bolso)
    m = mf.Manifold.batch_hull([cil((sx * (h - r), sy * (h - r), zv - HM), (sx * (h - r), sy * (h - r), zv), r, 32) for sx in (-1, 1) for sy in (-1, 1)])
    for sx in (-1, 1):
        for sy in (-1, 1): m -= cil((sx * c, sy * c, zv - HM - 1), (sx * c, sy * c, zv + 1), 1.6, 24)
    return salva(m, f"mesa_aquecida_{MESA}_{TENSAO}")

def presilha(nome):
    """presilha com espacador HM mais alto (gera na 1a vez)"""
    fn = f"{DER}/presilha_{nome}_aq.stl"
    if not os.path.exists(fn):
        subprocess.run(["python3", "/home/lucas/corexy/scripts/presilha_mesa.py"], env={**os.environ, "HM": str(HM)}, check=True)
    return fn
