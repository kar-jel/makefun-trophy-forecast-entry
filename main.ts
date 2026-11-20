// GTA VI trophy rarity forecast, Node 22 standard-library entrypoint.
// This is a TypeScript port of the Python model in model.py.
import { mkdirSync, readdirSync, readFileSync, writeFileSync } from 'node:fs';
import { join } from 'node:path';
type Row = Record<string, any>;
const INPUT_DIR = process.env.MAKEFUN_INPUT_DIR ?? '/input';
const OUTPUT_DIR = process.env.MAKEFUN_OUTPUT_DIR ?? '/output';
const LEVELS = [0.05, 0.25, 0.5, 0.75, 0.95];
const Z = [-1.6448536269514722, -0.6744897501960817, 0, 0.6744897501960817, 1.6448536269514722];
const median = (xs: number[]): number => { const a = [...xs].sort((x,y)=>x-y), n=a.length; return n ? (n%2 ? a[n>>1] : (a[n/2-1]+a[n/2])/2) : 0; };
function logit(p: number): number { p=Math.min(99.99,Math.max(.01,p))/100; return Math.log(p/(1-p)); }
function inv(x: number): number { if(x>=0){const e=Math.exp(-Math.min(x,700));return 100/(1+e);} const e=Math.exp(Math.max(x,-700));return 100*e/(1+e); }
function order(text: unknown): number|null { const d=typeof text==='string'?text.toLowerCase():''; let m=d.match(/complete chapter (\d+)/); if(m)return 100+Number(m[1]); if(d.includes('complete gone fishing'))return 1; if(d.includes('complete the final mission.'))return 200; m=d.match(/complete (\d+) mission strands/); if(m)return 300+Number(m[1]); m=d.match(/complete (\d+) challenges/); if(m)return 400+Number(m[1]); m=d.match(/complete (\d+) collectible/); if(m)return 400+Number(m[1]); return null; }
function forecast(c: Row): Row {
 const trophies:Array<Row>=Array.isArray(c.trophies)?c.trophies:[],n=trophies.length,H=Math.max(0,(typeof c.horizon_minutes==='number'&&Number.isFinite(c.horizon_minutes)?c.horizon_minutes:0)/1440);
 const hist0:Array<Row>=Array.isArray(c.history)?c.history:[],hist:Row[]=(hist0.length?hist0:[{slot:0,players_tracked:1,rates:Array(n).fill(null)}]).map(r=>{const rates=Array.isArray(r?.rates)?r.rates:[];return {...(r&&typeof r==='object'?r:{}),rates:Array.from({length:n},(_,i)=>{const x=rates[i];return typeof x==='number'&&Number.isFinite(x)?x:null;}),players_tracked:typeof r?.players_tracked==='number'&&r.players_tracked>0?r.players_tracked:1,slot:r?.slot??0};});
 const hours=(v:any)=>typeof v==='number'?v:Date.parse(v)/3600000;
 const th=hist.map(r=>hours(r.slot)),end=th[th.length-1],cut=end-24,Ns=hist.map(r=>Math.max(1,Math.trunc(r.players_tracked||1)));
 const recent=th.map((t,i)=>[t,Math.log(Ns[i])] as [number,number]).filter(x=>x[0]>=cut),gs:number[]=[];
 for(let a=0;a<recent.length;a++)for(let b=a+1;b<recent.length;b++)if(recent[b][0]>recent[a][0])gs.push((recent[b][1]-recent[a][1])/(recent[b][0]-recent[a][0]));
 const g=Math.max(0,gs.length?median(gs):0),tau=Math.max(1,Math.min(336,Math.max(1,(end-th[0])*2)));
 const tracked=Ns[Ns.length-1]*Math.exp(Math.min(.35,g)*tau*(1-Math.exp(-H*24/tau)));
 const noise=Math.max(.005,Math.min(.25,recent.length>1?median(recent.slice(1).map((x,j)=>Math.abs(x[1]-recent[j][1]))):.08));
 const counts:Array<Array<number|null>>=Array.from({length:n},()=>[]),logs:Array<Array<number|null>>=Array.from({length:n},()=>[]);
 hist.forEach((row,j)=>row.rates.forEach((rate:number|null,i:number)=>{if(rate===null){counts[i].push(null);logs[i].push(null);}else{const k=Math.min(Ns[j],Math.max(0,Math.floor(rate*Ns[j]/100+.5)));counts[i].push(k);logs[i].push(logit(100*(k+.5)/(Ns[j]+1)));}}));
 const groups=new Map<any,number[]>(); trophies.forEach((t:Row,i:number)=>{t=t&&typeof t==='object'?t:{};const k=t.tier??'unknown';if(!groups.has(k))groups.set(k,[]);groups.get(k)!.push(i);});
 const slopes:number[]=[],resid:number[]=[],flats:boolean[]=[];
 logs.forEach((arr,i)=>{const good=th.map((t,j)=>[t,arr[j]] as [number,number|null]).filter((x):x is [number,number]=>x[1]!==null),r=good.filter(x=>x[0]>=cut);if(!r.length)r.push(...good.slice(-12));flats.push(r.length<2||Math.max(...r.map(x=>x[1]))-Math.min(...r.map(x=>x[1]))<1e-9);const p:number[]=[];for(let a=0;a<r.length;a++)for(let b=a+1;b<r.length;b++)if(r[b][0]>r[a][0])p.push((r[b][1]-r[a][1])/((r[b][0]-r[a][0])/24));slopes.push(p.length?median(p):0);const m=median(r.map(x=>x[1]));resid.push(r.length>1?median(r.map(x=>Math.abs(x[1]-m))):0);});
 const pooled=[...slopes],priors:number[]=[];for(const ids of groups.values()){const s=median(ids.map(i=>slopes[i]));for(const i of ids)pooled[i]=.45*slopes[i]+.55*s;const vals=ids.flatMap(i=>counts[i].flatMap((k,j)=>k===null?[]:[1000*k/Ns[j]]));for(const i of ids)priors[i]=vals.length?median(vals):.1;}
 const orders=trophies.map((t:Row)=>order(t&&typeof t==='object'?t.description:null)),prog=orders.map((o:number|null,i:number)=>o===null?null:[o,i] as [number,number]).filter((x):x is [number,number]=>x!==null).sort((a,b)=>a[0]-b[0]);
 const observed=prog.map(([o,i])=>[o,hist[hist.length-1].rates[i]||0] as [number,number]);
 const frontO=Math.max(...observed.filter(x=>x[1]>=5).map(x=>x[0]),prog.length?Math.min(...prog.map(x=>x[0])):0),frontRate=Math.max(...observed.filter(x=>x[0]<=frontO).map(x=>x[1]),.01);
 const front=Math.max(0,logit(frontRate)-logit(.01)),step=Math.max(.08,Math.min(.6,front/Math.max(1,frontO-(prog.length?Math.min(...prog.map(x=>x[0])):frontO))));
 const rows=trophies.map((raw:Row,i:number)=>{const t=raw&&typeof raw==='object'?raw:{id:i};const last=counts[i][counts[i].length-1]??0,N=Ns[Ns.length-1];let qs:number[];
 if(last===N&&hist[hist.length-1].rates[i]!==null&&hist[hist.length-1].rates[i]>=99.995)qs=[100,100,100,100,100];else{let m:number,sig:number;if(flats[i]){m=logit(hist[hist.length-1].rates[i]??.01);sig=.025;}else{const w=last/(last+8),shrunk=w*last+(1-w)*priors[i]*N/1000;m=logit(100*(shrunk+.5)/(N+1));const d=pooled[i]*2.8*(1-Math.exp(-H/2.8));m+=Math.max(-.75,Math.min(1.25,d));sig=Math.min(.5,Math.max(.35,.35+Math.min(.15,resid[i]*.5)));}
 const o=orders[i],waiting=o!==null&&o>frontO&&(hist[hist.length-1].rates[i]||0)<=.02;if(waiting){const arrival=(o!-frontO)*step;sig=Math.sqrt(sig*sig+Math.min(2,arrival*.45)**2);qs=Z.map(z=>inv(m+z*sig));qs[2]=inv(m);qs[3]=Math.max(qs[3],inv(m+Math.max(0,(H-arrival)*.8)));qs[4]=Math.max(qs[4],inv(m+Math.max(0,(H-arrival)*.8)+sig));}else{sig=Math.sqrt(sig*sig+(.12*noise*Math.min(H,5))**2);qs=Z.map(z=>inv(m+z*sig));}if(last===0&&!waiting){qs[2]=Math.max(qs[2],Math.min(.1,priors[i]/10));qs[3]=Math.max(qs[3],qs[2]);qs[4]=Math.max(qs[4],qs[3]);}}
 const q=qs.map(x=>Math.floor((x+1e-12)*10000+.5)/10000);for(let j=1;j<5;j++)q[j]=Math.max(q[j],q[j-1]);return{id:t.id??i,q};});
 return{trophies:rows};
}
mkdirSync(OUTPUT_DIR,{recursive:true});
for(const file of readdirSync(INPUT_DIR).filter(f=>f.endsWith('.in')).sort()){const c=JSON.parse(readFileSync(join(INPUT_DIR,file),'utf8')) as Row;if(JSON.stringify(c.levels)!==JSON.stringify(LEVELS))throw Error(`${file}: wrong levels`);writeFileSync(join(OUTPUT_DIR,`${file.slice(0,-3)}.out`),JSON.stringify(forecast(c))+'\n');}
