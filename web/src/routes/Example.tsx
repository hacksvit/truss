import {useState} from 'react';
import SiteScene from '../components/SiteScene';

const FLOOR=[160,170,180];
const NAMES=['A','B','C'];

export default function Example(){
 const [cap,setCap]=useState(1800);
 const [mode,setMode]=useState<'overview'|'explore'>('overview');
 const useful=[900,700,1100];
 const reserve=100;
 const floors=FLOOR.reduce((a,b)=>a+b,0);
 const spare=cap-reserve-floors;
 const feasible=spare>=0;

 let budgets=FLOOR.slice();
 if(feasible){
  let pool=spare;
  const head=useful.map((u,i)=>Math.max(0,u-FLOOR[i]));
  const active=head.map((h,i)=>({i,h})).filter(x=>x.h>0).sort((a,b)=>a.h-b.h);
  let level=0,n=active.length;
  for(const {h} of active){
   const cost=(h-level)*n;
   if(cost>pool){ level+=pool/n; pool=0; break; }
   pool-=cost; level=h; n--;
  }
  budgets=FLOOR.map((f,i)=>f+Math.floor(Math.min(head[i],level)));
 }

 return <main className="example">
  <SiteScene onMode={setMode}/>
  <div className={'stage-controls'+(mode==='explore'?' walking':'')}>
   <span className="stage-mode">{mode==='explore'
     ? 'WASD move · V first person + mouse look · F exit'
     : 'F or hold the generator to walk the site'}</span>
   <label className="cap">
    <span>supply</span>
    <input type="range" min={400} max={3200} step={50} value={cap}
      onChange={e=>setCap(+e.target.value)}/>
    <b>{cap} W</b>
   </label>
   <div className={'grants'+(feasible?'':' infeasible')}>
    {feasible
     ? NAMES.map((n,i)=><span key={n}><i>{n}</i>{budgets[i]} W</span>)
     : <span className="short">infeasible · short {-spare} W</span>}
   </div>
  </div>
 </main>;
}
