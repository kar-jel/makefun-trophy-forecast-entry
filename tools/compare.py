import json, os, pathlib, subprocess, sys, tempfile, time
ROOT=pathlib.Path(__file__).resolve().parents[1]
CASES=[('p00', ROOT/'input/p00.in'),('p01',ROOT/'input/p01.in')]
def synth():
 c=json.loads((ROOT/'input/p01.in').read_text())
 c['id']='launchweek'; c['horizon_minutes']=60
 for j,row in enumerate(c['history']):
  row['slot']=f'2026-11-19T{(j//2):02d}:{(j%2)*30:02d}:00Z'
  row['players_tracked']=max(20,100+80*j)
 for i,t in enumerate(c['trophies']):
  t['tier']='gold' if i%3==0 else t.get('tier','bronze')
 for row in c['history']:
  row['rates']=[min(99.99, max(0, round((0.04+i*.09)*(1+j*.22),3))) for i in range(len(c['trophies']))]
  j=c['history'].index(row)
 return c
with tempfile.TemporaryDirectory() as td:
 td=pathlib.Path(td); inp=td/'in'; inp.mkdir(); cases=[]
 for name,path in CASES:
  c=json.loads(path.read_text()); (inp/f'{name}.in').write_text(json.dumps(c)); cases.append((name,c))
 c=synth(); (inp/'launchweek.in').write_text(json.dumps(c)); cases.append(('launchweek',c))
 outs={}
 for lang,cmd in [('Python',[sys.executable,str(ROOT/'main.py')]),('TypeScript',['node',str(ROOT/'main.ts')])]:
  out=td/lang; env=os.environ|{'MAKEFUN_INPUT_DIR':str(inp),'MAKEFUN_OUTPUT_DIR':str(out)}
  start=time.monotonic(); subprocess.run(cmd,cwd=ROOT,env=env,check=True,timeout=8); elapsed=time.monotonic()-start
  outs[lang]={};
  for name,case in cases:
   data=json.loads((out/f'{name}.out').read_text()); rows=data['trophies']; ids=[r['id'] for r in rows]; expected=[t['id'] for t in case['trophies']]
   assert len(rows)==len(expected) and len(ids)==len(set(ids)) and set(ids)==set(expected)
   assert all(len(r['q'])==5 and all(isinstance(x,(int,float)) and __import__('math').isfinite(x) and 0<=x<=100 for x in r['q']) and r['q']==sorted(r['q']) for r in rows)
   assert (out/f'{name}.out').stat().st_size<65536
   outs[lang][name]=(data,elapsed,(out/f'{name}.out').stat().st_size)
 print('Case | max abs difference (percentage points) | Python seconds | TypeScript seconds')
 for name,_ in cases:
  a=outs['Python'][name][0]['trophies']; b=outs['TypeScript'][name][0]['trophies']; bm={r['id']:r['q'] for r in b}
  diff=max(abs(x-y) for r in a for x,y in zip(r['q'],bm[r['id']]))
  assert diff<=0.0001+1e-12,(name,diff)
  print(f"{name} | {diff:.10f} | {outs['Python'][name][1]:.4f} | {outs['TypeScript'][name][1]:.4f}")
 print('Outputs (Python and TypeScript), first two trophies per practice case:')
 for name in ('p00','p01'):
  print(name)
  for lang in ('Python','TypeScript'):
   print(lang,json.dumps(outs[lang][name][0]['trophies'][:2],separators=(',',':')))
