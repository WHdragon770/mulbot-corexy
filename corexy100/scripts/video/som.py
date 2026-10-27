# Trilha sonora do video, sintetizada (numpy): musica de fundo + efeitos sincronizados com out/anim/linha.json
# (pecas chegando, parafusos, presilha girando, motores de passo com o tom pela velocidade real, explodida, sino).
# python3 som.py [saida.wav]
import sys, os, json, wave, numpy as np
CX = os.environ.get("CXY_DIR") or os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))   # raiz do projeto
from scipy import signal
SR = 48000
L = json.load(open(os.environ.get("CXY_LINHA") or f"{CX}/out/anim/linha.json"))
FPS = L["fps"]; DUR = L["fim"] / FPS + 1.0
N = int(DUR * SR); mix = np.zeros((N, 2))
rng = np.random.default_rng(3)
def t_(n): return np.arange(n) / SR
def poe(x, t0, g=1.0, pan=0.0):
    i = int(t0 * SR)
    if i >= N or i + len(x) <= 0: return
    x = x[: N - i]
    mix[i:i + len(x), 0] += x * g * (1 - max(pan, 0)); mix[i:i + len(x), 1] += x * g * (1 + min(pan, 0))
def env(n, a, r):
    e = np.ones(n); na, nr = int(a * SR), int(r * SR)
    e[:na] = np.linspace(0, 1, na) if na else 1
    if nr: e[-nr:] *= np.linspace(1, 0, nr) ** 2
    return e
def passa(x, lo, hi, ordem=2):
    sos = signal.butter(ordem, [lo, hi], btype="band", fs=SR, output="sos"); return signal.sosfilt(sos, x)
def baixa(x, fc, ordem=2):
    sos = signal.butter(ordem, fc, btype="low", fs=SR, output="sos"); return signal.sosfilt(sos, x)

# ---------------- musica: Am - F - C - G, 96 bpm, pad + baixo + arpejo ----------------
BPM = 96; BAT = 60 / BPM; COMP = 4 * BAT
NOTA = lambda m: 440 * 2 ** ((m - 69) / 12)
ACORDES = [(57, 60, 64), (53, 57, 60), (48, 52, 55), (55, 59, 62)]
musica = np.zeros(N)
def pad(freqs, d):
    n = int(d * SR); t = t_(n); x = np.zeros(n)
    for f in freqs:
        for det in (-0.12, 0.0, 0.11):          # 3 serras levemente desafinadas
            x += signal.sawtooth(2 * np.pi * f * (1 + det / 100) * t + rng.uniform(0, 6))
    return baixa(x / (3 * len(freqs)), 900) * env(n, 0.6, 0.8)
def pluck(f, d=0.5):
    n = int(d * SR); t = t_(n)
    return (np.sin(2 * np.pi * f * t) + 0.3 * np.sin(4 * np.pi * f * t)) * np.exp(-t * 7)
c = 0; tm = 0.0
while tm < DUR:
    ac = ACORDES[c % 4]
    p = pad([NOTA(m) for m in ac], 2 * COMP + 0.8); i = int(tm * SR); musica[i:i + len(p)] += p[: N - i] * 0.55
    for b in range(8):                            # baixo em seminimas
        nb = pluck(NOTA(ac[0] - 12), BAT * 0.95) * 0.9; j = int((tm + b * BAT) * SR); musica[j:j + len(nb)] += nb[: max(0, N - j)]
    for b in range(16):                           # arpejo em colcheias
        nn = ac[[0, 1, 2, 1][b % 4]] + 12; pl = pluck(NOTA(nn), 0.45) * 0.28; j = int((tm + b * BAT / 2) * SR)
        musica[j:j + len(pl)] += pl[: max(0, N - j)]
    tm += 2 * COMP; c += 1
fade = np.ones(N); fi, fo = int(2 * SR), int(4 * SR); fade[:fi] = np.linspace(0, 1, fi); fade[-fo:] = np.linspace(1, 0, fo)
musica *= fade * 0.22
mix += np.stack([musica, musica], 1)

# ---------------- efeitos ----------------
def whoosh(d=0.55, f0=300, f1=3000):
    n = int(d * SR); x = rng.standard_normal(n); out = np.zeros(n); B = 8
    for k in range(B):                            # filtro de banda varrendo (por blocos)
        a, b = k * n // B, (k + 1) * n // B; fc = f0 * (f1 / f0) ** (k / B)
        out[a:b] = passa(x, fc * 0.7, min(fc * 1.4, SR / 2 - 100))[a:b]
    return out * np.sin(np.linspace(0, np.pi, n)) ** 1.5
def click(f=1800):
    n = int(0.05 * SR); t = t_(n)
    return (np.sin(2 * np.pi * f * t) * np.exp(-t * 120) + 0.4 * rng.standard_normal(n) * np.exp(-t * 300))
def thud(f=70, d=0.5):
    n = int(d * SR); t = t_(n); return np.sin(2 * np.pi * f * t * (1 - 0.3 * t)) * np.exp(-t * 8)
def sino(f=880, d=2.5):
    n = int(d * SR); t = t_(n); x = np.zeros(n)
    for r, g, dk in ((1, 1, 2.5), (2.76, 0.5, 4), (5.4, 0.25, 6), (8.9, 0.12, 9)): x += g * np.sin(2 * np.pi * f * r * t) * np.exp(-t * dk)
    return x * env(n, 0.003, 0.2)
ev = L["eventos"]
chegadas = sorted(f for f, tp, _ in ev if tp == "chega")
balde = {}
for f in chegadas: balde[f // 5] = balde.get(f // 5, 0) + 1
for b, n_ in balde.items():                       # 1 whoosh por grupo de pecas que chegam juntas
    poe(whoosh(0.5, 250, 2600), b * 5 / FPS - 0.45, 0.10 * min(1 + np.log1p(n_), 3), rng.uniform(-0.5, 0.5))
    poe(thud(95, 0.25), b * 5 / FPS, 0.10 * min(1 + np.log1p(n_), 3))
ultimo = -1
for f in sorted(f for f, tp, _ in ev if tp == "click"):
    if f - ultimo < 2: continue                   # no maximo 1 tique a cada 2 quadros
    ultimo = f; poe(click(rng.uniform(1500, 2400)), f / FPS, 0.12, rng.uniform(-0.6, 0.6))
for f, tp, _ in ev:
    if tp == "giro":                              # catraca da presilha
        for k in range(10): poe(click(2600), f / FPS + k * 0.07, 0.09)
    elif tp == "explode": poe(whoosh(1.4, 120, 4000), f / FPS, 0.45); poe(thud(45, 1.2), f / FPS + 0.2, 0.5)
    elif tp == "fecha": poe(whoosh(1.2, 4000, 150), f / FPS, 0.35)
    elif tp == "baque": poe(thud(60, 0.7), f / FPS, 0.6); poe(click(900), f / FPS, 0.3)
    elif tp == "liga": poe(click(700), f / FPS, 0.25)
poe(sino(660), 0.4, 0.25); poe(sino(880), L["legendas"][-1][0] / FPS, 0.25)
for f in L["etapas"]: poe(sino(1320, 1.2), f / FPS, 0.06)

# ---------------- motores de passo: tom = velocidade (80 passos/mm, 1/16 -> ~5 Hz por mm/s) ----------------
def motor(velocidade, hz_mm=5.0, ganho=0.10, pan=0.0):
    """velocidade: array por amostra (mm/s) -> onda quadrada suave com fase continua"""
    f = np.abs(velocidade) * hz_mm + 40 * (np.abs(velocidade) > 1)
    fase = 2 * np.pi * np.cumsum(f) / SR
    x = np.tanh(3 * np.sin(fase)) + 0.25 * np.sin(2 * fase) + 0.05 * rng.standard_normal(len(f))
    liga = baixa((np.abs(velocidade) > 0.5).astype(float), 30)
    return passa(x, 60, 6000) * liga * ganho
va, vb, vz = np.zeros(N), np.zeros(N), np.zeros(N)
for f0, f1, a_, b_, z_ in L["vel"]:
    i0, i1 = int(f0 / FPS * SR), int(f1 / FPS * SR); va[i0:i1], vb[i0:i1], vz[i0:i1] = a_, b_, z_
sua = lambda v: baixa(v, 6)                       # aceleracao suave entre poses
poe(motor(sua(va), pan=0.4), 0); poe(motor(sua(vb), pan=-0.4), 0); poe(motor(sua(vz), hz_mm=25, ganho=0.05), 0)

# ---------------- normaliza e grava ----------------
mix = np.tanh(mix / max(1e-9, np.abs(mix).max()) * 1.6) * 0.89
out = sys.argv[1] if len(sys.argv) > 1 else f"{CX}/out/anim/som.wav"
with wave.open(out, "wb") as w:
    w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR); w.writeframes((mix * 32767).astype("<i2").tobytes())
print("som", out, f"{DUR:.1f} s")
