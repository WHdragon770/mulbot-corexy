# Corta as pecas da CoreXY 200 que nao cabem na area 100x100x100 (CoreXY 100) em partes <= MAXL,
# com furos pra pino nas faces de corte. Uso: python3 cortar_na_100.py <02 STL para imprimir> <saida>
# Pecas que cabem sao copiadas iguais; pinos saem em "00 Pinos" com a quantidade total no nome.
import sys, os, re, glob, math, shutil, numpy as np, trimesh, manifold3d as mf
from shapely.geometry import Point

MAXL = 95.0          # maior medida de cada parte (area 100, sobra pra saia/brim)
PINOS = [(4.0, 8.0), (3.0, 6.0), (2.0, 5.0)]   # (diametro do pino, profundidade do furo em cada lado)
FOLGA = 0.2          # furo = pino + 2*FOLGA
PAREDE = 1.2         # parede minima em volta do furo
LUVA_E, LUVA_L = 2.0, 20.0   # corte sem lugar pra pino: luva por dentro da parede (espessura, comprimento total)
LUVAS = []                   # (nome, manifold em pe) das luvas soltas
RD, PINO_L = 4.6, 24.0   # fuso: pino em D no furo central (igual ao fuso de resina em 2 metades, zv.divide_fuso)
SRC, DST = sys.argv[1], sys.argv[2]

def para_mf(tm):
    return mf.Manifold(mf.Mesh(vert_properties=np.asarray(tm.vertices, np.float32),
                               tri_verts=np.asarray(tm.faces, np.uint32)))

def para_tm(m):
    g = m.to_mesh()
    return trimesh.Trimesh(np.asarray(g.vert_properties)[:, :3], np.asarray(g.tri_verts), process=False)

def cil(eixo, p, r, h):
    """cilindro de raio r e comprimento h centrado no ponto p, alinhado ao eixo (0,1,2)"""
    c = mf.Manifold.cylinder(h, r, r, 32, True)
    if eixo == 0: c = c.rotate([0, 90, 0])
    elif eixo == 1: c = c.rotate([90, 0, 0])
    return c.translate(list(p))

def furo_d(c, z, folga, L):
    """furo/pino em D ao longo de Z centrado em (c, z): chato a 0.7 RD trava o giro (rosca continua)"""
    r = RD + folga
    d = mf.Manifold.cylinder(L, r, r, 48, True) - mf.Manifold.cube([20, 40, L + 2], True).translate([0.7 * RD + folga + 10, 0, 0])
    return d.translate([c[0], c[1], z])

def secao(tm, eixo, pos):
    n = np.zeros(3); n[eixo] = 1; o = np.zeros(3); o[eixo] = pos
    s = tm.section(plane_origin=o, plane_normal=n)
    if s is None: return None, None
    pl, T = s.to_2D()
    polys = pl.polygons_full
    if not polys: return None, None
    from shapely.ops import unary_union
    return unary_union(polys), T

def pinos_no_corte(m, tm, eixo, pos):
    """acha posicoes de pino na secao em 'pos'. Retorna (diam, prof, [pontos 3D]) e area da secao"""
    sec, T = secao(tm, eixo, pos)
    if sec is None: return None, 0.0
    for d, prof in PINOS:
        rr = d / 2 + FOLGA + PAREDE
        dentro = sec.buffer(-rr)
        if dentro.is_empty: continue
        # candidatos: pontos espalhados dentro da area valida, depois testa o furo em 3D
        cands = []
        for g in getattr(dentro, 'geoms', [dentro]):
            cands.append(g.representative_point())
            b = g.bounds
            for fx in (0.15, 0.5, 0.85):
                for fy in (0.15, 0.5, 0.85):
                    p = Point(b[0] + fx * (b[2] - b[0]), b[1] + fy * (b[3] - b[1]))
                    if g.contains(p): cands.append(p)
        ok = []
        for p in cands:
            q = (T @ np.array([p.x, p.y, 0, 1]))[:3]; q[eixo] = pos
            casca = cil(eixo, q, rr, 2 * prof + 2 * PAREDE)
            if (m ^ casca).volume() >= 0.995 * casca.volume():   # furo todo dentro de material
                if all(np.linalg.norm(q - o) >= 2 * rr + 1 for o in ok): ok.append(q)
        if ok:
            # no maximo 2 pinos, os mais afastados
            if len(ok) > 2:
                best = max(((a, b) for i, a in enumerate(ok) for b in ok[i + 1:]), key=lambda ab: np.linalg.norm(ab[0] - ab[1]))
                ok = list(best)
            return (d, prof, ok), sec.area
    return None, sec.area

def escolher_cortes(m, tm, eixo):
    lo, hi = tm.bounds[0][eixo], tm.bounds[1][eixo]
    L = hi - lo; n = math.ceil(L / (MAXL - 1))
    cortes, ant = [], lo
    for k in range(1, n):
        resto = n - k
        a = max(ant + 15, hi - resto * (MAXL - 1)); b = min(ant + MAXL - 1, hi - 15)
        ideal = ant + (hi - ant) / (resto + 1)
        melhor = None
        for pos in sorted(np.arange(a, b + 1e-6, 1.0), key=lambda x: abs(x - ideal))[:25]:
            pin, area = pinos_no_corte(m, tm, eixo, pos)
            nota = (0 if pin is None else len(pin[2]) * pin[0] ** 2) * 1000 + area - abs(pos - ideal)
            if melhor is None or nota > melhor[0]: melhor = (nota, pos, pin)
        cortes.append((melhor[1], melhor[2])); ant = melhor[1]
    return cortes

def luva(m, tm, eixo, pos):
    """anel de LUVA_E mm encostado no lado de dentro da parede (dentro do casco convexo da secao), folga FOLGA,
    LUVA_L de comprimento centrado no corte; o que bate em material da peca e removido. Devolve (luva em pe, T)"""
    from shapely.geometry.polygon import orient
    sec, T = secao(tm, eixo, pos)
    if sec is None: return None, None
    anel = sec.buffer(FOLGA + LUVA_E, join_style=2).difference(sec.buffer(FOLGA, join_style=2)).intersection(sec.convex_hull.buffer(-0.5))
    gs = [orient(g, 1.0) for g in getattr(anel, 'geoms', [anel]) if g.geom_type == 'Polygon' and g.area > 4]
    if not gs: return None, None
    cs = mf.CrossSection([np.array(c.coords)[:-1] for g in gs for c in [g.exterior, *g.interiors]], mf.FillRule.EvenOdd)
    Ti = np.linalg.inv(T)
    lu = cs.extrude(LUVA_L) - m.transform(Ti[:3, :4]).translate([0, 0, LUVA_L / 2])
    lu = mf.Manifold.batch_boolean([c for c in lu.decompose() if c.volume() > 20], mf.OpType.Add) if lu.volume() > 20 else None
    return (lu if lu is not None and lu.volume() > 50 else None), T

def cortar(m, nome, pinos_tot, rel):
    """corta recursivamente pelo maior eixo ate tudo caber"""
    tm = para_tm(m)
    ext = tm.extents
    if ext.max() <= MAXL: return [m]
    eixo = int(np.argmax(ext))
    cortes = escolher_cortes(m, tm, eixo)
    machos = []
    for pos, pin in cortes:
        if pin is None and 'fuso' in nome and eixo == 2:
            c = tm.bounds.mean(0)
            m = m - furo_d(c, pos, FOLGA, PINO_L + 2)
            pinos_tot['D'] = pinos_tot.get('D', 0) + 1
            rel.append(f"  {nome}: corte em Z={pos:.0f}, pino em D no furo central")
            continue
        if pin is None:
            lu, T = luva(m, tm, eixo, pos)
            if lu is None:
                rel.append(f"  {nome}: corte em {'XYZ'[eixo]}={pos:.0f} sem pino nem luva (so cola)")
                continue
            if eixo == 2:   # corte horizontal: macho em pe na parte de baixo (imprime sem suporte), entra na de cima
                n = [0, 0, 0]; n[eixo] = 1
                macho = lu.translate([0, 0, -LUVA_L / 2]).transform(T[:3, :4]).trim_by_plane(n, pos)
                machos.append((pos, macho))
                rel.append(f"  {nome}: corte em Z={pos:.0f}, encaixe macho na parte de baixo")
            else:
                LUVAS.append((nome, lu))
                rel.append(f"  {nome}: corte em {'XYZ'[eixo]}={pos:.0f}, luva de emenda por dentro")
            continue
        d, prof, pts = pin
        for q in pts: m = m - cil(eixo, q, d / 2 + FOLGA, 2 * prof)
        pinos_tot[d] = pinos_tot.get(d, 0) + len(pts)
        rel.append(f"  {nome}: corte em {'XYZ'[eixo]}={pos:.0f}, {len(pts)} pino(s) {d:.0f} mm")
    partes, resto = [], m
    for pos, _ in cortes:
        n = [0, 0, 0]; n[eixo] = 1
        a, b = resto.split_by_plane(n, pos)   # a = lado +, b = lado -
        for pm, mc in machos:
            if pm == pos:
                if para_tm(b + mc).extents.max() <= MAXL + 0.5: b = b + mc
                else: LUVAS.append((nome, mc.translate([0, 0, -pos])))   # nao cabe com o macho: vira luva solta
        partes.append(b); resto = a
    partes.append(resto)
    out = []
    for p in partes: out += cortar(p, nome, pinos_tot, rel)
    return out

def main():
    os.makedirs(DST, exist_ok=True)
    pinos_tot, rel, ncort = {}, [], 0
    for f in sorted(glob.glob(os.path.join(SRC, '**', '*.stl'), recursive=True)):
        r = os.path.relpath(f, SRC); dest = os.path.join(DST, r)
        os.makedirs(os.path.dirname(dest), exist_ok=True)
        tm = trimesh.load(f, force='mesh')
        if tm.extents.max() <= MAXL + 5 or 'Resina' in r:   # ate 100 cabe inteira; resina vai na impressora de resina
            shutil.copy2(f, dest); continue
        mq = re.search(r'\[(\d+)x\]', r); q = int(mq.group(1)) if mq else 1
        base = re.sub(r'\s*\[\d+x\]\.stl$', '', os.path.basename(f))
        tot = {}
        partes = cortar(para_mf(tm), base, tot, rel)
        for d, c in tot.items(): pinos_tot[d] = pinos_tot.get(d, 0) + c * q
        partes = [p for p in partes if p.volume() > 1]
        for i, p in enumerate(partes, 1):
            t = para_tm(p); t.apply_translation([-t.bounds[0][0], -t.bounds[0][1], -t.bounds[0][2]])
            t.export(os.path.join(os.path.dirname(dest), f"{base} parte {i}de{len(partes)} [{q}x].stl"))
            assert t.extents.max() <= MAXL + 0.5, (base, i, t.extents)
        luv = [l for n_, l in LUVAS if n_ == base]
        for i, l in enumerate(luv, 1):
            t = para_tm(l); t.apply_translation(-t.bounds[0])
            t.export(os.path.join(os.path.dirname(dest), f"{base} luva {i} [{q}x].stl"))
        ncort += 1
        print(f"{base}: {len(partes)} partes", flush=True)
    pd = os.path.join(DST, '00 Pinos'); os.makedirs(pd, exist_ok=True)
    if 'D' in pinos_tot:
        c = pinos_tot.pop('D')
        para_tm(furo_d((0, 0), PINO_L / 2, 0.0, PINO_L)).export(os.path.join(pd, f"pino D fuso {2*RD:.1f}x{PINO_L:.0f} mm [{c + 1}x].stl"))
    for d, c in sorted(pinos_tot.items()):
        prof = dict(PINOS)[d]
        p = mf.Manifold.cylinder(2 * prof - 0.6, d / 2, d / 2, 32)
        para_tm(p).export(os.path.join(pd, f"pino {d:.0f}x{2*prof-0.6:.1f} mm [{c + c // 10 + 2}x].stl"))
    with open(os.path.join(DST, 'cortes.txt'), 'w') as fh:
        fh.write(f"{ncort} pecas cortadas em partes <= {MAXL:.0f} mm\n" + "\n".join(rel) + "\n")
    print("pinos:", pinos_tot)

main()
