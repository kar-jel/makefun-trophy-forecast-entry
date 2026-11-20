"""Robust, count-smoothed launch-week trophy forecast."""
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
    # Work in logit space; binomial pseudo-count smoothing stabilizes small rates.
    times=[]; values=[[] for _ in range(n)]
    for row in hist:
        times.append(row['slot'])
        N=max(1,row.get('players_tracked') or 1)
        for i,r in enumerate(row['rates']):
            if r is None: values[i].append(None); continue
            k=min(N,max(0,math.floor(r*N/100+0.5)))
            values[i].append(_logit_pct(100*(k+0.5)/(N+1)))
    # slots are ISO timestamps in real cases; numeric in synthetic tests.
    def hours(v):
        if isinstance(v,(int,float)): return float(v)
        from datetime import datetime
        return datetime.fromisoformat(v.replace('Z','+00:00')).timestamp()/3600
    th=[hours(x) for x in times]
    end=th[-1]; cutoff=end-24
    slopes=[]; current=[]; residual=[]; flat=[]
    for i,arr in enumerate(values):
        good=[(t,y) for t,y in zip(th,arr) if y is not None]
        recent=[(t,y) for t,y in good if t>=cutoff]
        if not recent: recent=good[-12:]
        current.append(recent[-1][1])
        flat.append(len(recent)<2 or max(y for _,y in recent)-min(y for _,y in recent)<1e-9)
        # Theil-Sen robust slope, in logit/day; cap the pair count for speed.
        pairs=[]
        sampled=recent[-24:]
        for a in range(len(sampled)):
            for b in range(a+1,len(sampled)):
                dt=(sampled[b][0]-sampled[a][0])/24
                if dt>0: pairs.append((sampled[b][1]-sampled[a][1])/dt)
        slopes.append(_median(pairs) if pairs else 0.0)
        residual.append(_median([abs(y-_median([z for _,z in recent])) for _,y in recent]) if len(recent)>1 else 0.0)
    # Tier-level EB pooling, with greater shrinkage for rare/common low-count observations.
    groups={}
    for i,t in enumerate(case['trophies']): groups.setdefault(t.get('tier','unknown'),[]).append(i)
    mu=current[:]; slope=slopes[:]
    for indices in groups.values():
        center=_median([current[i] for i in indices]); sc=_median([slopes[i] for i in indices])
        for i in indices:
            rate=100/(1+math.exp(-max(-30,min(30,current[i]))))
            # Rare achievements borrow more; the prior is deliberately modest.
            w=min(.92,max(.18,rate/3.0))
            mu[i]=w*current[i]+(1-w)*center
            slope[i]=.45*slopes[i]+.55*sc
    # Truly flat history is a special case: no extrapolation, narrow uncertainty.
    rows=[]
    for i,t in enumerate(case['trophies']):
        if flat[i]:
            m=mu[i]; sigma=.025
        else:
            tau=2.8
            gain=slope[i]*tau*(1-math.exp(-H/tau))
            # Growth cannot plausibly continue at an unbounded historical rate.
            gain=max(-0.75,min(1.25,gain))
            m=mu[i]+gain
            sigma=min(1.15,max(.09, .12 + .35*math.sqrt(H) + min(.35, residual[i]*1.8)))
        qs=[]
        for z in Z: qs.append(min(100,max(0,100/(1+math.exp(-max(-35,min(35,m+z*sigma)))))))
        # Ensure rounded values remain ordered and finite.
        q=[round(x+1e-12,4) for x in qs]
        for j in range(1,5): q[j]=max(q[j],q[j-1])
        rows.append({'id':t['id'],'q':q})
    return {'trophies':rows}
