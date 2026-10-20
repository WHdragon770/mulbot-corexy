# Correias x pecas (exceto polias/pinos onde enrolam) em varias poses
import sys, os, subprocess, json
sys.path.insert(0, "/home/lucas/corexy/scripts")
codigo = r'''
import sys, os; os.environ["ESFERAS"]="0"; sys.argv=["x"]; sys.path.insert(0,"/home/lucas/corexy/scripts")
exec(open("/home/lucas/corexy/scripts/cxy.py").read())
res=[]
for cn in ("correiaA","correiaB"):
    cm = peca_mf([p for n,p,t,c in P if n==cn][0], np.eye(4)); cb = cm.bounding_box()
    for n,p,t,c in P:
        if n.startswith(("correia","louca","motorA","motorB","presilhaCoreXY","carroX")): continue
        m = peca_mf(p,t); b = m.bounding_box()
        if any(b[3+i] < cb[i] or cb[3+i] < b[i] for i in range(3)): continue
        v = (m ^ cm).volume()
        if v > 0.5: res.append((cn, n, round(v,1)))
print("RES", res)
'''
for xc, yg in ((-108, -60.9), (108, -60.9), (-108, 156.1), (108, 156.1), (0, 47.63)):
    env = dict(os.environ, XC=str(xc), YG=str(yg), ZM="3")
    out = subprocess.run([sys.executable, "-c", codigo], env=env, capture_output=True, text=True).stdout
    print((xc, yg), [l for l in out.splitlines() if l.startswith("RES")][0])
