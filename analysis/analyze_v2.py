import glob,json,os,numpy as np
from scipy.stats import wilcoxon
W="/workspace/flp_rerun/win_results/bench"; A="/workspace/flp_rerun/ablation_v2/bench"; D6="/workspace/flp_rerun/ablation_v2/du62_600"
def load(p):
    d={}
    for f in glob.glob(p+"/*_s*.json"):
        r=json.load(open(f)); d[(r["method"],r["instance"],r["seed"])]=r
    return d
win=load(W); abl=load(A); D=dict(win); 
dup=[k for k in abl if k in win]; D.update(abl); d6=load(D6)
BUDGET={"O7":20,"vC10a":20,"AB20":60,"SC30":60,"Du62":150}
rng=np.random.default_rng(0)
def cost(r): return r['cost'] if r.get('feasible') and r.get('cost') is not None else np.nan
def po(r): return (r.get('meta') or {}).get('stage2')=='polish only'
def holm(ps):
    k=sorted([x for x in ps if ps[x] is not None],key=lambda x:ps[x]); m=len(k); adj={}; run=0
    for j,x in enumerate(k): run=max(run,min(1,(m-j)*ps[x])); adj[x]=run
    return adj
def compare(a,b):
    a=np.array(a);b=np.array(b); d={}
    d['n']=len(a); d['dmean']=100*(b.mean()-a.mean())/a.mean()
    bs=[];idx=np.arange(len(a))
    for _ in range(5000):
        k=rng.choice(idx,len(idx)); bs.append(100*(b[k].mean()-a[k].mean())/a[k].mean())
    d['ci']=tuple(np.percentile(bs,[2.5,97.5])); diff=b-a; tol=1e-6*np.abs(a)
    d['wins']=int((diff>tol).sum()); d['losses']=int((diff<-tol).sum())
    d['p']=None if np.all(np.abs(diff)<=tol) else wilcoxon(b,a,zero_method='zsplit').pvalue
    return d
methods=sorted({k[0] for k in D if k[0].startswith('ours_')}); insts=["O7","vC10a","AB20","SC30","Du62"]
res={}; flags=[]
for (m,i,s),r in sorted(D.items()):
    if po(r) and m.startswith('ours'): flags.append(f"{m} {i} s{s} cost={cost(r):.2f}")
for i in insts:
    ps={}
    for m in methods:
        pairs=[(s,D[('ours',i,s)],D[(m,i,s)]) for (mm,ii,s) in D if mm==m and ii==i and ('ours',i,s) in D]
        if not pairs: continue
        a=[cost(x[1]) for x in pairs]; b=[cost(x[2]) for x in pairs]
        nf=sum(np.isfinite(b)); 
        ok=[k for k in range(len(a)) if np.isfinite(a[k]) and np.isfinite(b[k])]
        if len(ok)<len(a)//2:
            res[(m,i)]=dict(n=len(pairs),nf=nf,infeasible=True); continue
        pairs=[pairs[k] for k in ok]; a=[a[k] for k in ok]; b=[b[k] for k in ok]
        d=compare(a,b); d['nf']=nf; d['ntot']=len(ok) if False else None; d['nall']=nf+0; d['seeds']=f"{min(x[0] for x in pairs)}-{max(x[0] for x in pairs)}"
        d['po_var']=sum(po(x[2]) for x in pairs); d['po_ours']=sum(po(x[1]) for x in pairs)
        d['mean_v']=float(np.mean(b)); d['mean_o']=float(np.mean(a))
        res[(m,i)]=d; ps[m]=d['p']
    h=holm(ps)
    for m in ps: res[(m,i)]['holm']=h.get(m)
def fp(p): return 'tie' if p is None else (f'{p:.1e}' if p<1e-3 else f'{p:.3f}')
L=['| 变体 | 算例 | 配对数 (seed) | 可行 | Δ均值% vs ours [95% CI] | 变体差/好 | Wilcoxon p | Holm p | polish-only (变体/ours) |','|---|---|---|---|---|---|---|---|---|']
for i in insts:
    for m in methods:
        d=res.get((m,i))
        if not d: continue
        if d.get('infeasible'): L.append(f"| {m} | {i} | {d['n']} | {d['nf']}/{d['n']} | 不可比（有不可行） | — | — | — | — |"); continue
        L.append(f"| {m} | {i} | {d['n']} ({d['seeds']}) | {d['nf']}/{len([1 for (mm,ii,ss) in D if mm==m and ii==i])} | {d['dmean']:+.2f} [{d['ci'][0]:+.2f}, {d['ci'][1]:+.2f}] | {d['wins']}/{d['losses']} | {fp(d['p'])} | {fp(d.get('holm'))} | {d['po_var']}/{d['po_ours']} |")
open('tab_v2_stats.md','w').write('\n'.join(L)+'\n')
# Du62 600 s: force vs s1 paired; plus Du62 150 s force vs s1
L2=['| 比较 | 配对数 | 均值 A | 均值 B | Δ% (B vs A) [95% CI] | B差/好 | Wilcoxon p |','|---|---|---|---|---|---|---|']
def row(name,A_,B_):
    ks=sorted(set(s for (m,i,s) in A_)&set(s for (m,i,s) in B_))
    a=[cost(A_[(None,s)]) if False else cost([v for k,v in A_.items() if k[2]==s][0]) for s in ks]
    b=[cost([v for k,v in B_.items() if k[2]==s][0]) for s in ks]
    ok=[k for k in range(len(a)) if np.isfinite(a[k]) and np.isfinite(b[k])]; nbad=len(a)-len(ok)
    a=[a[k] for k in ok]; b=[b[k] for k in ok]; ks=[ks[k] for k in ok]
    if nbad: name+=f'（剔除 {nbad} 个崩溃 seed）'
    d=compare(a,b); L2.append(f"| {name} | {len(ks)} | {np.mean(a):,.0f} | {np.mean(b):,.0f} | {d['dmean']:+.3f} [{d['ci'][0]:+.3f}, {d['ci'][1]:+.3f}] | {d['wins']}/{d['losses']} | {fp(d['p'])} |")
sel=lambda S,m,i:{k:v for k,v in S.items() if k[0]==m and k[1]==i}
row('Du62 600 s：A=ours_force，B=ours_s1',sel(d6,'ours_force','Du62'),sel(d6,'ours_s1','Du62'))
row('Du62 150 s：A=ours_force，B=ours_s1',sel(D,'ours_force','Du62'),sel(D,'ours_s1','Du62'))
row('Du62 150 s：A=ours（polish-only），B=ours_force',sel(D,'ours','Du62'),sel(D,'ours_force','Du62'))
f600=sel(d6,'ours_force','Du62'); 
L2.append(''); L2.append('Du62 600 s ours_force 各 seed 是否 polish-only：'+', '.join(f"s{k[2]}={'是' if po(v) else '否'}" for k,v in sorted(f600.items())))
L2.append('Du62 600 s 墙钟（force / s1）：'+', '.join(f"{v['wall']:.0f}" for k,v in sorted(f600.items()))+' / '+', '.join(f"{v['wall']:.0f}" for k,v in sorted(sel(d6,'ours_s1','Du62').items())))
open('tab_v2_du62.md','w').write('\n'.join(L2)+'\n')
# nos1_cons start info
L3=[]
for (m,i,s),r in sorted(D.items()):
    if m=='ours_nos1_cons' and s==0: L3.append(f"{i}: meta keys={list((r.get('meta') or {}).keys())[:12]} start={(r.get('meta') or {}).get('start')}")
open('extra_v2.txt','w').write('dup keys overriding win_results: %d\n'%len(dup)+'polish-only runs:\n'+'\n'.join(flags)+'\n'+'\n'.join(L3)+'\n')
print(open('tab_v2_stats.md').read()); print(open('tab_v2_du62.md').read()); print(open('extra_v2.txt').read())
