export interface ChampionInput {
  fixtureId:number; minute:number; scoreHome:number; scoreAway:number; status:string;
  homeTeam:string; awayTeam:string;
  forecast:{home:number|null;draw:number|null;away:number|null}|null;
  odds:{home:number|null;draw:number|null;away:number|null;over25:number|null;under25:number|null}|null;
  oddsUpdatedAt:string|null;
}
export interface ChampionCandidate {
  market:'MATCH_1X2'|'TOTAL_GOALS_2_5'; selection:string; label:string; odds:number;
  modelProbability:number; fairOdds:number; impliedProbability:number;
  devigProbability:number|null; edge:number; expectedValue:number; confidence:number; score:number;
}
export interface ChampionDecision {
  model:'CHAMPION'; version:string; action:'BET'|'NO_BET'; confidence:number|null;
  selection:string|null; label:string|null; market:'MATCH_1X2'|'TOTAL_GOALS_2_5'|null;
  odds:number|null; fairOdds:number|null; modelProbability:number|null;
  impliedProbability:number|null; devigProbability:number|null; edge:number|null;
  expectedValue:number|null; reason:string; checkedAt:string; candidates:ChampionCandidate[];
}
const MIN_P=.55, MIN_EV=.03, MIN_EDGE=.03, MAX_AGE=60;
const pmf=(l:number,n:number)=>{const a=new Array(n+1).fill(0);a[0]=Math.exp(-Math.max(0,l));for(let k=1;k<=n;k++)a[k]=a[k-1]*l/k;return a};
function fit(th:number,td:number,ta:number):[number,number]|null{
 let be=Infinity,bh=.1,ba=.1;
 for(let h=.05;h<=3.5;h+=.05){const ph=pmf(h,10);for(let a=.05;a<=3.5;a+=.05){const pa=pmf(a,10);let hw=0,d=0,aw=0;for(let i=0;i<=10;i++)for(let j=0;j<=10;j++){const p=ph[i]*pa[j];if(i>j)hw+=p;else if(i===j)d+=p;else aw+=p}const e=(hw-th)**2+(d-td)**2+(aw-ta)**2;if(e<be){be=e;bh=h;ba=a}}}return Number.isFinite(be)?[bh,ba]:null;
}
function live(lh:number,la:number,m:number,sh:number,sa:number){
 const f=Math.max(0,(90-Math.min(90,Math.max(0,m)))/90),ph=pmf(lh*f,12),pa=pmf(la*f,12);
 let hw=0,d=0,aw=0,ov=0;const ct=sh+sa;
 for(let i=0;i<=12;i++)for(let j=0;j<=12;j++){const p=ph[i]*pa[j],h=sh+i,a=sa+j;if(h>a)hw+=p;else if(h===a)d+=p;else aw+=p;if(ct+i+j>=3)ov+=p}
 const z=hw+d+aw||1;return{home:hw/z,draw:d/z,away:aw/z,over25:Math.min(1,Math.max(0,ov/z)),under25:1-Math.min(1,Math.max(0,ov/z))}
}
const devig=(o:number[])=>{if(o.some(x=>!Number.isFinite(x)||x<=1))return null;const p=o.map(x=>1/x),s=p.reduce((a,b)=>a+b,0);return s?p.map(x=>x/s):null};
const age=(t:string|null,n:number)=>{const x=t?Date.parse(t):NaN;return Number.isFinite(x)?Math.max(0,(n-x)/1000):Infinity};
export function computeChampionDecision(i:ChampionInput,now=Date.now()):ChampionDecision{
 const version='champion-live-v1.0',checkedAt=new Date(now).toISOString(),liveStatus=['1H','2H','HT','ET','LIVE','P'];
 const base=(reason:string,confidence:number|null=null):ChampionDecision=>({model:'CHAMPION',version,action:'NO_BET',confidence,selection:null,label:null,market:null,odds:null,fairOdds:null,modelProbability:null,impliedProbability:null,devigProbability:null,edge:null,expectedValue:null,reason,checkedAt,candidates:[]});
 if(!liveStatus.includes(i.status))return base('MATCH_NOT_LIVE');
 if(!i.odds)return base('ODDS_UNAVAILABLE');
 if(age(i.oddsUpdatedAt,now)>MAX_AGE)return base('ODDS_STALE');
 const f=i.forecast, fh=f?.home,fd=f?.draw,fa=f?.away;
 if([fh,fd,fa].some(x=>typeof x!=='number'||!Number.isFinite(x)||x<0||x>1))return base('MODEL_INPUT_UNAVAILABLE');
 const s=(fh!+fd!+fa!)||1,fitv=fit(fh!/s,fd!/s,fa!/s);if(!fitv)return base('MODEL_FIT_FAILED');
 const p=live(fitv[0],fitv[1],i.minute,i.scoreHome,i.scoreAway),c:ChampionCandidate[]=[];
 const o1=[i.odds.home,i.odds.draw,i.odds.away],f1=devig(o1.filter((x):x is number=>typeof x==='number'));
 if(o1.every(x=>typeof x==='number'&&x>1)&&f1){const ps=[p.home,p.draw,p.away],labs=[i.homeTeam,'Draw',i.awayTeam];o1.forEach((o,k)=>{if(typeof o!=='number')return;const q=ps[k],ev=q*o-1,e=q-f1[k];if(q>=MIN_P&&ev>=MIN_EV&&e>=MIN_EDGE)c.push({market:'MATCH_1X2',selection:['1','X','2'][k],label:labs[k],odds:o,modelProbability:q,fairOdds:1/q,impliedProbability:1/o,devigProbability:f1[k],edge:e,expectedValue:ev,confidence:q,score:ev*q})})}
 const o2=[i.odds.over25,i.odds.under25],f2=devig(o2.filter((x):x is number=>typeof x==='number'));
 if(o2.every(x=>typeof x==='number'&&x>1)&&f2){const ps=[p.over25,p.under25],labs=['Over 2.5 Goals','Under 2.5 Goals'];o2.forEach((o,k)=>{if(typeof o!=='number')return;const q=ps[k],ev=q*o-1,e=q-f2[k];if(q>=MIN_P&&ev>=MIN_EV&&e>=MIN_EDGE)c.push({market:'TOTAL_GOALS_2_5',selection:k?'UNDER':'OVER',label:labs[k],odds:o,modelProbability:q,fairOdds:1/q,impliedProbability:1/o,devigProbability:f2[k],edge:e,expectedValue:ev,confidence:q,score:ev*q})})}
 c.sort((a,b)=>b.score-a.score);const w=c[0];if(!w)return base('NO_MARKET_PASSES_CHAMPION_GATE',Math.max(p.home,p.draw,p.away,p.over25,p.under25));
 return{model:'CHAMPION',version,action:'BET',confidence:w.confidence,selection:w.selection,label:w.label,market:w.market,odds:w.odds,fairOdds:w.fairOdds,modelProbability:w.modelProbability,impliedProbability:w.impliedProbability,devigProbability:w.devigProbability,edge:w.edge,expectedValue:w.expectedValue,reason:'BEST_VALUE_MARKET',checkedAt,candidates:c};
}