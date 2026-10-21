# Converte as ilhas (coordenadas de impressao do rapido.sh) de volta pro quadro da peca na montagem e lista os furos de junta perto
# python3 ilha_mundo.py check.json peca [...]
import sys, json, os, numpy as np, trimesh
sys.argv, ARG = sys.argv[:1], sys.argv[1:]
C = json.load(open(ARG[0])); R = json.load(open("/home/lucas/corexy/scripts/placas/impressao_rot.json"))
os.environ["CABOS"] = "1"
import io, contextlib
with contextlib.redirect_stdout(io.StringIO()):
    sys.path.insert(0, "/home/lucas/corexy/scripts"); import cxy
from juntas import FUROS, GOTAS
for p in ARG[1:]:
    Rm = np.array(R[p]); m = trimesh.load(f"/home/lucas/corexy/derived/{p}.stl", process=False)
    v = m.vertices @ Rm.T; off = v.min(0)
    for f, r in C.items():
        if os.path.basename(f)[:-4] != p: continue
        for o in r[:5]:
            c = np.array([np.mean(o["x"]), np.mean(o["y"]), np.mean(o["z"])]) + off
            w = Rm.T @ c
            cs = np.array([[x, y, z] for x in o["x"] for y in o["y"] for z in o["z"]]) + off
            ws = cs @ Rm                                     # R ortogonal: mundo = R^T p
            print(f"{p} {o['mm3']:.0f} mm3 centro mundo {w.round(1)}  caixa mundo {ws.min(0).round(1)} .. {ws.max(0).round(1)}  (cima = {np.round(Rm.T @ [0, 0, 1], 2)})")
            for p0, p1, rr in GOTAS.get(p, []) + [(a, b, r_) for a, b, r_ in FUROS]:
                d = np.linalg.norm(np.cross(w - p0, p1 - p0)) / np.linalg.norm(p1 - p0)
                t = (w - p0) @ (p1 - p0) / np.linalg.norm(p1 - p0) ** 2
                if d < rr + 6 and -0.3 < t < 1.3:
                    print(f"      furo r={rr:.2f} {p0.round(1)} -> {p1.round(1)}  dist={d:.1f}")
