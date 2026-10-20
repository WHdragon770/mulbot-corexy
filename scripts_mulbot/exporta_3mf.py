# junta todas as pecas posicionadas num 3MF (um objeto por peca)
import json, trimesh, numpy as np, sys, gc
J = json.load(open(sys.argv[1])); out = sys.argv[2]
cache = {}
sc = trimesh.Scene()
for it in J:
    f = it["stl"]
    if f not in cache: cache[f] = trimesh.load(f, process=False)
    nm = f'{it["peca"]}__{it["nome"]}'.replace(" ", "_")
    sc.add_geometry(cache[f], node_name=nm, geom_name=it["peca"].replace(" ", "_"), transform=np.asarray(it["T"]))
sc.export(out)
print("OK 3mf", out)
