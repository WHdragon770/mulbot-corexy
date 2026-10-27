# Poses da maquina "funcionando" p/ o video: roda o cxy.py em N poses (X/Y/Z andando), guarda a matriz das pecas
# que se mexem e as correias de cada pose. Saida: out/anim/poses/poses.json + correiaA_k.stl / correiaB_k.stl
# python3 poses.py [N=60]
import os, sys, json, math, shutil, subprocess, numpy as np
N = int(sys.argv[1]) if len(sys.argv) > 1 else 60
CX = "/home/lucas/corexy"; OUT = f"{CX}/out/anim/poses"; PR = f"{CX}/out/anim/progresso_poses.txt"
def caminho(t):
    """t 0..1 -> (XC, YG, ZM): cabeca desenhando um laco (Lissajous) e mesa descendo devagar"""
    return (78 * math.sin(2 * math.pi * 1.5 * t), 47.63 + 62 * math.sin(2 * math.pi * t + math.pi / 4),
            10 + 110 * math.sin(1.5 * math.pi * t) ** 2)          # mesa desce, sobe e desce de novo (10 a 120 mm)
def roda(env):
    subprocess.run(["python3", f"{CX}/scripts/cxy.py"], env=dict(os.environ, ESFERAS="0", **env), check=True, capture_output=True)
    return {j["nome"]: j["T"] for j in json.load(open(f"{CX}/out/cxy.json"))}
base = roda({})
PAR = f"{OUT}/poses_parcial.json"                       # retoma se cair no meio
poses = json.load(open(PAR)) if os.path.exists(PAR) else []
for k in range(len(poses), N):
    open(PR, "w").write(f"{k + 1} {N + 1} pose {k + 1} de {N}")
    xc, yg, zm = caminho(k / (N - 1))
    T = roda(dict(XC=f"{xc:.3f}", YG=f"{yg:.3f}", ZM=f"{zm:.3f}"))
    mov = {n: t for n, t in T.items() if not n.startswith(("correia", "caboEsteira")) and not np.allclose(t, base.get(n, t), atol=1e-4)}
    for c in ("correiaA", "correiaB", "caboEsteira_XY", "caboEsteira_Y"): shutil.copy(f"{CX}/derived/{c}.stl", f"{OUT}/{c}_{k:03d}.stl")
    poses.append(dict(xc=xc, yg=yg, zm=zm, T=mov)); json.dump(poses, open(PAR, "w"))
json.dump(dict(caminho="lissajous", poses=poses), open(f"{OUT}/poses.json", "w"))
os.remove(PAR); roda({})                                   # volta a montagem na pose padrao
open(PR, "w").write(f"FIM poses do video prontas ({N}), {len(poses[-1]['T'])} pecas se mexem")
print("ok", N, len(poses[-1]["T"]))
