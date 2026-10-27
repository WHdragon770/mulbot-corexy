# 3MF em streaming: carrega um STL por vez e grava direto no zip (nao estoura a RAM)
import json, sys, zipfile, gc, numpy as np, trimesh
J = json.load(open(sys.argv[1])); out = sys.argv[2]
CT = '<?xml version="1.0" encoding="UTF-8"?><Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types"><Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/><Default Extension="model" ContentType="application/vnd.ms-package.3dmanufacturing-3dmodel+xml"/></Types>'
RL = '<?xml version="1.0" encoding="UTF-8"?><Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships"><Relationship Target="/3D/3dmodel.model" Id="rel0" Type="http://schemas.microsoft.com/3dmanufacturing/2013/01/3dmodel"/></Relationships>'
def esc(s): return s.replace("&", "&amp;").replace('"', "&quot;").replace("<", "&lt;")
ids = {}
with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED, allowZip64=True) as z:
    z.writestr("[Content_Types].xml", CT); z.writestr("_rels/.rels", RL)
    with z.open("3D/3dmodel.model", "w", force_zip64=True) as f:
        w = lambda s: f.write(s.encode())
        w('<?xml version="1.0" encoding="UTF-8"?>\n<model unit="millimeter" xml:lang="en-US" xmlns="http://schemas.microsoft.com/3dmanufacturing/core/2015/02">\n<resources>\n')
        for it in J:
            st = it["stl"]
            if st in ids: continue
            m = trimesh.load(st, process=True); ids[st] = len(ids) + 1
            w(f'<object id="{ids[st]}" type="model" name="{esc(it["peca"])}"><mesh><vertices>\n')
            V = m.vertices
            for i in range(0, len(V), 50000):
                w("".join('<vertex x="%.4f" y="%.4f" z="%.4f"/>\n' % tuple(v) for v in V[i:i+50000]))
            w('</vertices><triangles>\n')
            F = m.faces
            for i in range(0, len(F), 50000):
                w("".join('<triangle v1="%d" v2="%d" v3="%d"/>\n' % tuple(t) for t in F[i:i+50000]))
            w('</triangles></mesh></object>\n')
            del m, V, F; gc.collect()
        w('</resources>\n<build>\n')
        for it in J:
            T = np.asarray(it["T"])
            mt = " ".join("%.6f" % T[r][c] for c in range(4) for r in range(3))
            w(f'<item objectid="{ids[it["stl"]]}" transform="{mt}"/>\n')
        w('</build>\n</model>\n')
print("OK 3mf", out, len(ids), "malhas,", len(J), "pecas")
