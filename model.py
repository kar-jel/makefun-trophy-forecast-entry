"""Two-series launch-week trophy forecast."""
import math

Z = [-1.6448536269514722, -0.6744897501960817, 0.0, 0.6744897501960817, 1.6448536269514722]

def _logit_pct(p):
    p = min(99.99, max(0.01, p)) / 100.0
    return math.log(p / (1.0-p))

def _inv(x):
    if x >= 0:
        e = math.exp(-min(x, 700)); return 100/(1+e)
    e = math.exp(max(x, -700)); return 100*e/(1+e)

def _median(xs):
    a=sorted(xs); n=len(a)
    return a[n//2] if n%2 else (a[n//2-1]+a[n//2])/2

def forecast(case):
 hist=case['history']; n=len(case['trophies']); H=max(0,case['horizon_minutes']/1440)
 def hours(v):
  if isinstance(v,(int,float)): return float(v)
  from datetime import datetime
  return datetime.fromisoformat(v.replace('Z','+00:00')).timestamp()/3600
 th=[hours(r['slot']) for r in hist]; end=th[-1]; cutoff=end-24
 Ns=[max(1,int(r.get('players_tracked') or 1)) for r in hist]
 recentN=[(th[j],math.log(Ns[j])) for j in range(len(th)) if th[j]>=cutoff]
 gs=[(recentN[b][1]-recentN[a][1])/(recentN[b][0]-recentN[a][0]) for a in range(len(recentN)) for b in range(a+1,len(recentN)) if recentN[b][0]>recentN[a][0]]
 g=max(0,_median(gs) if gs else 0); tau=max(1,min(336,max(1,(end-th[0])*2)))
 tracked=Ns[-1]*math.exp(min(.35,g)*tau*(1-math.exp(-H*24/tau)))
 noise=max(.005,min(.25,_median([abs(recentN[j][1]-recentN[j-1][1]) for j in range(1,len(recentN))]) if len(recentN)>1 else .08))
 counts=[[] for _ in range(n)]; logs=[[] for _ in range(n)]
 for row,N in zip(hist,Ns):
  for i,r in enumerate(row['rates']):
   if r is None: counts[i].append(None); logs[i].append(None)
   else:
    k=min(N,max(0,math.floor(r*N/100+.5))); counts[i].append(k); logs[i].append(_logit_pct(100*(k+.5)/(N+1)))
 groups={}
 for i,t in enumerate(case['trophies']): groups.setdefault(t.get('tier','unknown'),[]).append(i)
 current=[]; slopes=[]; residual=[]; flats=[]
 for i,arr in enumerate(logs):
  good=[(tt,y) for tt,y in zip(th,arr) if y is not None]; r=[x for x in good if x[0]>=cutoff] or good[-12:]
  current.append(r[-1][1]); flats.append(len(r)<2 or max(y for _,y in r)-min(y for _,y in r)<1e-9)
  ps=[(r[b][1]-r[a][1])/((r[b][0]-r[a][0])/24) for a in range(len(r)) for b in range(a+1,len(r)) if r[b][0]>r[a][0]]
  slopes.append(_median(ps) if ps else 0); med=_median([y for _,y in r]); residual.append(_median([abs(y-med) for _,y in r]) if len(r)>1 else 0)
 pooled=slopes[:]
 for inds in groups.values():
  s=_median([slopes[i] for i in inds])
  for i in inds: pooled[i]=.45*slopes[i]+.55*s
 priors={}
 for inds in groups.values():
  r=[1000*k/N for i in inds for k,N in zip(counts[i],Ns) if k is not None]
  for i in inds: priors[i]=_median(r) if r else .1
 rows=[]
 for i,t in enumerate(case['trophies']):
  last=counts[i][-1]; N=Ns[-1]
  if last==N and hist[-1]['rates'][i] is not None and hist[-1]['rates'][i]>=99.995: qs=[100.]*5
  else:
   if flats[i]: m=_logit_pct(hist[-1]['rates'][i] if hist[-1]['rates'][i] is not None else .01); sig=.025
   else:
    w=last/(last+8); shrunk=w*last+(1-w)*priors[i]*N/1000
    m=_logit_pct(100*(shrunk+.5)/(N+1)); d=pooled[i]*2.8*(1-math.exp(-H/2.8)); m+=max(-.75,min(1.25,d))
    sig=min(1.15,max(.09,.12+.35*math.sqrt(H)+min(.35,residual[i]*1.8)))
   sig=math.sqrt(sig*sig+(.12*noise*min(H,5))**2)
   qs=[_inv(m+z*sig) for z in Z]
   if last==0: qs[2]=max(qs[2],min(.1,priors[i]/10)); qs[3]=max(qs[3],qs[2]); qs[4]=max(qs[4],qs[3])
  q=[round(x+1e-12,4) for x in qs]
  for j in range(1,5): q[j]=max(q[j],q[j-1])
  rows.append({'id':t['id'],'q':q})
 return {'trophies':rows}
