# Estimativa de termino do render que leva em conta o PESO de cada quadro (triangulos visiveis, out/anim/custo.json):
# ajusta tempo = a + b * triangulos nos quadros ja feitos (pelo horario de cada PNG), soma o previsto dos que faltam
# + a carga do Blender em cada bloco de 120 que falta + a montagem do MP4, e da o horario COM MARGEM (o pior caso realista).
# python3 estimativa.py quadros_dir [--vigiar arquivo_progresso]   (--vigiar grava arquivo_progresso.eta a cada 30 s)
import sys, os, json, time, datetime, numpy as np
CX = os.environ.get("CXY_DIR") or os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))   # raiz do projeto
Q = sys.argv[1]; BLOCO = 120; MONTA_S = 240
C = np.array(json.load(open(f"{CX}/out/anim/custo.json")), float) / 1e6     # milhoes de triangulos
TOT = len(C)

def calcula():
    fs = {}
    for n in os.listdir(Q):
        if n.startswith("f") and n.endswith(".png") and os.path.getsize(f"{Q}/{n}") > 0: fs[int(n[1:5])] = os.path.getmtime(f"{Q}/{n}")
    if len(fs) < 30: return None
    feitos = sorted(fs); dt, x, cargas = [], [], []
    for a, b in zip(feitos, feitos[1:]):
        if b != a + 1: continue
        d = fs[b] - fs[a]
        if (b - 1) % BLOCO == 0: cargas.append((b, d)); continue      # 1o quadro do bloco: inclui abrir o Blender
        if d <= 0: continue
        dt.append(d); x.append(C[b - 1])
    dt, x = np.array(dt), np.array(x)
    # tempo = k * (C0 + triangulos): 1 parametro, mediana do trecho recente (robusto a peso constante e a quadro anomalo)
    C0 = 0.3
    rec = slice(max(0, len(dt) - 240), len(dt))
    k = float(np.median(dt[rec] / (C0 + x[rec])))
    a, b = k * C0, k
    sd = float(np.std(dt[rec] - (a + b * x[rec])))
    carga = float(np.median([max(0.0, d - (a + b * C[q - 1])) for q, d in cargas])) if cargas else 30.0
    faltam = [q for q in range(1, TOT + 1) if q not in fs]
    prev = float(sum(a + b * C[q - 1] for q in faltam))
    blocos = len({(q - 1) // BLOCO for q in faltam} - {(max(feitos) - 1) // BLOCO})
    resto = prev + blocos * max(carga, 0) + MONTA_S
    margem = 1.08 * resto + 2 * sd * np.sqrt(max(len(faltam), 1)) + 300  # +8 %, ruido e 5 min de folga
    agora = time.time()
    return dict(feitos=len(fs), faltam=len(faltam), seg_quadro_agora=a + b * C[max(feitos) - 1],
                previsto=datetime.datetime.fromtimestamp(agora + resto), garantido=datetime.datetime.fromtimestamp(agora + margem),
                a=a, b=b, carga=carga)

if __name__ == "__main__":
    if "--vigiar" in sys.argv:
        arq = sys.argv[sys.argv.index("--vigiar") + 1]
        while True:
            r = calcula()
            if r: open(arq + ".eta", "w").write(r["garantido"].strftime("%H:%M"))
            try:
                if open(arq).read().strip().startswith(("FIM", "ERRO")): break
            except OSError: pass
            time.sleep(30)
    else:
        r = calcula()
        if not r: sys.exit("poucos quadros ainda")
        print(f"feitos {r['feitos']} | faltam {r['faltam']} | agora ~{r['seg_quadro_agora']:.1f} s/quadro | carga do bloco {r['carga']:.0f} s")
        print(f"modelo: {r['a']:.2f} s + {r['b']:.2f} s por milhao de triangulos")
        print(f"previsto {r['previsto']:%H:%M} | GARANTIDO ate {r['garantido']:%H:%M}")
