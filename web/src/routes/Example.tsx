import {useState} from 'react';
import SiteScene from '../components/SiteScene';
import {SITE_MEMBERS,WANTS,RESERVE_W,allocate,usefulFor} from '../components/trussModel';

export default function Example(){
 const [cap,setCap]=useState(1800);
 const [mode,setMode]=useState<'overview'|'explore'>('overview');
 const [house,setHouse]=useState<{index:number;name:string;prompt?:boolean}|null>(null);
 const [panel,setPanel]=useState(false);

 // exactly what a member publishes: its registered floor, and the floor plus
 // every flexible step it is currently asking to run
 const offers=SITE_MEMBERS.map(m=>
  ({id:m.id,floor:m.floor,useful:usefulFor(m,WANTS[m.id])}));

 // the same allocator the coordinator runs, on the same offers
 const plan=allocate(offers,cap,RESERVE_W);
 const budgets=SITE_MEMBERS.map(m=>plan.budgets[m.id]??m.floor);

 return <main className="example">
  <SiteScene onMode={setMode} onHouse={setHouse} onPanel={setPanel} budgets={budgets} cap={cap} panelOpen={panel}/>
  <div className={'stage-controls'+(mode==='explore'?' walking':'')+(panel?' coordinator-active':'')}>
   <span className="stage-mode">{
     panel ? 'Inside coordinator · E / Esc to step out · scroll to inspect'
     : house&&!house.prompt ? 'Inside home '+house.name+' · E to step out'
     : house?.prompt ? (house.index<0 ? 'E to open the coordinator' : 'E to enter home '+house.name)
     : mode==='explore' ? 'WASD move · V first person · F exit'
     : 'F or hold the generator to walk the site'}</span>
   <label className="cap">
    <span>supply</span>
    <input type="range" min={400} max={3200} step={50} value={cap}
      onChange={e=>setCap(+e.target.value)}/>
    <b>{cap} W</b>
   </label>
   <div className={'grants'+(plan.feasible?'':' infeasible')}>
    {plan.feasible
     ? SITE_MEMBERS.map((m,i)=><span key={m.id}><i>{m.name}</i>{budgets[i]} W proposed</span>)
     : <span className="short">infeasible · short {plan.deficit} W</span>}
   </div>
  </div>
 </main>;
}
