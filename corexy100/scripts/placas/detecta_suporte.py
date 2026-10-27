# Quais pecas precisam de suporte? 1 placa por peca unica (sem conflito entre vizinhas), suporte normal em qualquer lugar,
# angulo 30 (padrao do Orca), pontes nao contam. Depois: python3 detecta_suporte.py ler <pasta_gcode>
# python3 detecta_suporte.py gerar <saida.3mf>   (SRC=<pasta_orient>)
import sys, os, re, json, glob
ARGS = sys.argv[1:]; sys.argv = sys.argv[:1]      # placas.py le SRC do ambiente quando nao tem argumento
import placas as P
modo, alvo = ARGS[0], ARGS[1]
if modo == "gerar":
    base = P.projeto
    def proj(n):
        d = base(n); d.update(enable_support="1", support_type="normal(auto)", support_on_build_plate_only="0", support_threshold_angle=os.environ.get("ANG", "30"), bridge_no_support=os.environ.get("PONTE", "0"))
        return d
    P.projeto = proj
    ks = [k for k, v in P.INFO.items() if not any(r in v["conj"] for r in P.RESINA)]
    LOTE = 24                                    # o Slicer aceita no maximo 36 placas por projeto
    for j in range(0, len(ks), LOTE):
        pls = []
        for k in ks[j:j + LOTE]:
            p = P.empacota([(k, P.INFO[k]["ext"])], k)[0]; p.nome = ""; pls.append(p)
        P.escreve_3mf(f"{alvo}_{j // LOTE + 1}.3mf", pls, "detecta")
        json.dump(ks[j:j + LOTE], open(f"{alvo}_{j // LOTE + 1}.json", "w"), ensure_ascii=False)
else:
    ks = json.load(open(ARGS[2]))
    out = []
    for i, k in enumerate(ks, 1):
        f = f"{alvo}/plate_{i}.gcode"
        if not os.path.exists(f): out.append((k, None, None)); continue
        tipo, e_sup, e_tot, zs = None, 0.0, 0.0, []
        z = 0.0
        for l in open(f, errors="ignore"):
            if l.startswith(";TYPE:"): tipo = l[6:].strip()
            elif l.startswith(";Z:"): z = float(l[3:])
            elif l.startswith("G1") and " E" in l and "X" in l:
                m = re.search(r" E([-\d.]+)", l)
                if m:
                    e = float(m.group(1))
                    if e > 0:
                        e_tot += e
                        if tipo and tipo.startswith("Support"): e_sup += e; zs.append(z)
        mm3 = e_sup * 2.405                          # 1.75 mm: 2.405 mm3 por mm de filamento
        out.append((k, round(mm3), round(100 * e_sup / max(e_tot, 1e-9), 1), (min(zs), max(zs)) if zs else None))
    out.sort(key=lambda x: -(x[1] or 0))
    for o in out: print(o)
    json.dump(out, open(f"{alvo}/suporte.json", "w"), ensure_ascii=False, indent=0)
