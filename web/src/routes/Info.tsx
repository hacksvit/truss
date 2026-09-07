import {memo,useEffect,useId,useRef,useState} from 'react';
import TrussMark from '../components/TrussMark';
import './info.css';

const CHAPTERS=[
 {id:'supply',title:'Shared Supply',copy:'Several homes share one power supply. When everyone needs more at once, something has to wait.',scene:'One supply. Five virtual homes.',group:'THE BUILDING'},
 {id:'agent',title:'Room Agent',copy:'A small program looks after each home’s appliances. A room could be managed the same way.',scene:'Open a home. Meet its local agent.',group:'THE BUILDING'},
 {id:'choice',title:'Local Choice',copy:'The agent chooses what can run within its allowance. Appliance details stay out of the coordinator’s view.',scene:'The choices stay inside the home.',group:'THE BUILDING'},
 {id:'request',title:'Small Request',copy:'The home sends how much power it could use. The coordinator receives a total, rather than an appliance list.',scene:'Only the total makes this journey.',group:'THE CONVERSATION'},
 {id:'essentials',title:'Essentials First',copy:'Each home has an agreed basic allowance. We reserve those allowances before sharing extra power.',scene:'Make room for the basics first.',group:'THE CONVERSATION'},
 {id:'sharing',title:'Fair Shares',copy:'Spare power is shared fairly until each home’s request is filled. A smaller request leaves more for the others.',scene:'Fill together. Stop when a request is met.',group:'THE CONVERSATION'},
 {id:'promises',title:'Kept Promises',copy:'Earlier permissions may still be in use. We count them before giving out more power.',scene:'Earlier promises still take up space.',group:'THE CONVERSATION'},
 {id:'expiry',title:'Short Permission',copy:'Extra power comes with an expiry. If renewal stops, the virtual home returns to its basic allowance.',scene:'Extra permission ends. The basics remain.',group:'WHEN THINGS CHANGE'},
 {id:'readings',title:'Missing Readings',copy:'No reading means “unknown.” We keep counting earlier promises until they expire.',scene:'Silence never means zero.',group:'WHEN THINGS CHANGE'},
 {id:'scale',title:'More Rooms',copy:'More rooms would mean more agents and messages. We need to test the whole system as it grows.',scene:'Proposed expansion · an illustration',group:'THE BIGGER PICTURE'},
 {id:'today',title:'Tested Today',copy:'The live demo runs five virtual homes. The Lab tests allocation for larger groups, not the whole network.',scene:'Five live virtual homes. A separate allocation Lab.',group:'THE BIGGER PICTURE'},
 {id:'limits',title:'Real Limits',copy:'Software cannot create missing power. Real installations need suitable hardware and further testing.',scene:'A software prototype, with real questions to test.',group:'THE BIGGER PICTURE'},
];
const clamp=(n:number)=>Math.max(0,Math.min(1,n));
const ease=(n:number)=>{const t=clamp(n);return t*t*(3-2*t);};
const ROOMS=[[110,145],[300,145],[490,145],[205,315],[395,315]];

function Room({index,step,phase}:{index:number;step:number;phase:number}){
 const open=step>=1,focused=index===0&&step>=1&&step<=3;
 const essentials=step>=4;
 const expired=step===7;
 const extra=step>=5&&step!==11?expired?1-phase:1:0;
 const unknown=step===8&&index===2;
 const arrival=step===0?ease(phase*1.65-index*.13):1;
 const unfold=step===1?ease(phase*1.5-index*.1):open?1:0;
 const lift=focused?(step===1?unfold:1):0;
 return <g className={'info-room'+(focused?' is-focused':'')} style={{opacity:.2+.8*arrival,transform:`translate(${-12*lift}px,${(1-arrival)*44-8*lift}px) scale(${1+.04*lift})`}}>
  <path className="room-depth" d="M0 0 14 -12H170V114L156 128H0Z"/>
  <rect className="room-interior" x="0" y="0" width="156" height="128" rx="5"/>
  <path className="room-floor" d="M0 105 35 82H156V128H0Z"/>
  <g className="room-appliances" style={{opacity:unfold,transform:`translateY(${(1-unfold)*15}px)`}}>
   <rect className="room-device" x="102" y="30" width="29" height="63" rx="3"/>
   {step===2&&index===0?<rect className="device-choice-ring" x="98" y="26" width="37" height="71" rx="6" pathLength="1" strokeDasharray="1" strokeDashoffset={1-phase}/>:null}
   <path className="room-detail" d="M103 55h27m-21-15v7m0 17v12"/>
   <path className="room-detail" d="M33 52v40m-13 1h26"/>
   <path className="room-lamp" d="m22 32-8 22h37l-8-22Z"/>
   <ellipse className="room-light" cx="34" cy="79" rx="21" ry="6" style={{opacity:step===2&&index!==0?.25:1}}/>
   <g className="room-agent" transform={`translate(61 ${65-(step===1?Math.sin(unfold*Math.PI)*10:0)})`}>
    {focused?<circle className="agent-signal" cx="3" cy="17" r={20+phase*12} style={{opacity:(1-phase)*.7}}/>:null}
    <path d="M5 7V0m-2 0h4M-9 15l-5 8m27-8 5 8M-4 29v6m14-6v6"/>
    <rect x="-8" y="6" width="22" height="23" rx="6"/>
    <path className="agent-eyes" d="M-2 14h1m7 0h1"/>
   </g>
  </g>
  <g className="room-facade" style={{opacity:1-unfold,transform:`translate(${-55*unfold}px,${20*unfold}px) skewY(${-22*unfold}deg)`}}>
   <rect x="0" y="0" width="156" height="128" rx="5"/>
   <path d="M17 26h37v42H17zm80 0h37v42H97zM66 69h25v59H66Z"/>
   <path d="M35 26v42m-18-21h37m62-21v42m-19-21h37"/>
  </g>
  <rect className="allowance-track" x="12" y="112" width="132" height="5" rx="2"/>
  <rect className="allowance-basic" x="12" y="112" width={essentials?38*(step===4?ease(phase*1.5-index*.1):1):0} height="5" rx="2"/>
  <rect className="allowance-extra" x="50" y="112" width={extra*Math.min([68,42,80,56,72][index],step===5?phase*80:80)} height="5" rx="2"/>
  {step===6||unknown?<rect className="allowance-promise" x="50" y="109" width={68} height="11" rx="3" pathLength="1" strokeDasharray=".04 .03" strokeDashoffset={-phase*.4}/>:null}
  <text className="room-name" x="0" y="149">HOME {String.fromCharCode(65+index)}</text>
  {unknown?<g transform={`translate(128 13) scale(${.75+.25*phase})`}><circle className="unknown-disc" r="18"/><text className="unknown-mark" textAnchor="middle" y="6">?</text></g>:null}
 </g>;
}

const BuildingScene=memo(function BuildingScene({step,phase}:{step:number;phase:number}){
 const gridId=useId();
 const showingRequest=step===3,showingReply=step===5;
 const wide=step===9;
 const network=step>=3;
 // A small request follows a cubic curve; the room's appliance icons stay put.
 const t=showingReply?1-phase:phase,x=(1-t)**3*188+3*(1-t)**2*t*130+3*(1-t)*t*t*620+t**3*654;
 const y=(1-t)**3*280+3*(1-t)**2*t*515+3*(1-t)*t*t*270+t**3*478;
 return <svg className="info-building" viewBox="0 0 800 660" role="img" aria-label={CHAPTERS[step].scene}>
  <defs><pattern id={gridId} width="32" height="32" patternUnits="userSpaceOnUse"><path d="M32 0H0V32" fill="none" stroke="currentColor" strokeWidth=".5"/></pattern></defs>
  <rect className="scene-grid" width="800" height="660" fill={`url(#${gridId})`}/>
  <ellipse className="building-shadow" cx="390" cy="529" rx="287" ry="36"/>
  <g className="expansion" style={{opacity:wide?1:0}}>
   {[0,1,2].map(row=>[0,1,2,3,4,5].map(col=>{const grow=ease(phase*2-(row+col)*.12);return <g key={`${row}-${col}`} opacity={grow} transform={`translate(${70+col*116} ${130+row*132+(1-grow)*35})`}><rect width="91" height="88" rx="4"/><path d="M18 23h16v22H18zm38 0h16v22H56zM40 60h15v28"/></g>;}))}
  </g>
  <g className="building-world" style={{transform:wide?'translate(176px,153px) scale(.55)':'translate(0px,0px) scale(1)'}}>
   <path className="supply-line" d="M65 98H730M94 98v414h94m-1-414v36m190-36v36m190-36v36"/>
   <path className="supply-trace" d="M65 98H730" pathLength="1" strokeDasharray="1" strokeDashoffset={step===0?1-phase:0}/>
   <g transform="translate(345 69)"><rect className="supply-label" x="-90" y="-20" width="180" height="34" rx="17"/><text className="scene-label" textAnchor="middle" y="2">SHARED SUPPLY</text></g>
   <path className="building-roof" d="m91 135 299-35 299 35-19 12H108Z" style={{opacity:step===0?1:.25,transform:step===0?'translateY(0)':'translateY(-15px)'}}/>
   {ROOMS.map(([rx,ry],i)=><g key={i} transform={`translate(${rx} ${ry})`}><Room index={i} step={step} phase={phase}/></g>)}
   <path className="message-route" d="M188 280C130 515 620 270 654 478" style={{opacity:network?1:0,strokeDashoffset:-phase*60}}/>
   <g className="coordinator-box" transform="translate(588 481)" style={{opacity:network?1:.4}}>
    <rect x="0" y="0" width="147" height="73" rx="9"/><path d="M18 19h21v18H18zm33 0h21v18H51zm33 0h21v18H84z"/><text x="73" y="60" textAnchor="middle">COORDINATOR</text>
   </g>
   {showingRequest||showingReply?<g className={'request-capsule'+(showingReply?' is-reply':'')} transform={`translate(${x} ${y})`}><rect x="-60" y="-17" width="120" height="34" rx="17"/><text textAnchor="middle" y="5">{showingReply?'PERMISSION':'POWER REQUEST'}</text></g>:null}
   {step===7?<g className="expiry-clock" transform="translate(110 422)"><circle r="31"/><circle className="expiry-remaining" r="31" strokeDasharray={`${(1-phase)*195} 195`} transform="rotate(-90)"/><text textAnchor="middle" y="5">{Math.ceil((1-phase)*6)}s</text></g>:null}
   {step===10?<g className="lab-outline" transform="translate(70 542)"><path d="M0 42h200"/>{[15,25,33,45,55].map((height,i)=><path key={i} d={`M${20+i*35} 35v${-height*ease(phase*1.8-i*.17)}`}/>)}<text x="0" y="67">LAB · ALLOCATION ONLY</text></g>:null}
  </g>
  {step>=4&&step<=8?<g className="scene-key" transform="translate(205 610)"><circle className="key-basic" r="4"/><text x="13" y="4">Basic allowance</text><circle className="key-extra" cx="191" r="4"/><text x="204" y="4">Extra permission</text></g>:null}
  {wide?<text className="expansion-label" x="400" y="603" textAnchor="middle">PROPOSED EXPANSION</text>:null}
 </svg>;
});

export default function Info(){
 const page=useRef<HTMLElement>(null);
 const [frame,setFrame]=useState({step:0,phase:0});
 useEffect(()=>{
  const el=page.current;if(!el)return;
  const chapters=Array.from(el.querySelectorAll<HTMLElement>('.info-chapter'));
  const media=matchMedia('(prefers-reduced-motion: reduce)');
  let raf=0;
  const render=()=>{
   raf=0;const mobile=innerWidth<=800,anchor=innerHeight*(mobile?.78:.55);
   let step=0;
   for(let i=0;i<chapters.length;i++){if(chapters[i].getBoundingClientRect().top<=anchor)step=i;}
   const box=chapters[step].getBoundingClientRect();
   const phase=media.matches?1:ease((anchor-box.top)/Math.max(1,box.height*.6));
   setFrame(previous=>previous.step===step&&Math.abs(previous.phase-phase)<.003?previous:{step,phase});
  };
  const schedule=()=>{if(!raf)raf=requestAnimationFrame(render);};
  render();addEventListener('scroll',schedule,{passive:true});addEventListener('resize',schedule);media.addEventListener('change',schedule);
  return()=>{cancelAnimationFrame(raf);removeEventListener('scroll',schedule);removeEventListener('resize',schedule);media.removeEventListener('change',schedule);};
 },[]);
 const jump=(i:number)=>{
  const target=document.getElementById(`info-${CHAPTERS[i].id}`);if(!target)return;
  const mobile=innerWidth<=800;
  const reduced=matchMedia('(prefers-reduced-motion: reduce)').matches;
  const scene=page.current?.querySelector<HTMLElement>('.info-scene');
  const offset=mobile&&!reduced&&scene?parseFloat(getComputedStyle(scene).top)+scene.offsetHeight+12:mobile?152:110;
  scrollTo({top:scrollY+target.getBoundingClientRect().top-offset,behavior:reduced?'instant':'smooth'});
 };
 return <main className="info-page" ref={page}>
  <header className="info-intro"><p className="info-eyebrow">INSIDE TRUSS</p><h1>A little closer.<br/><span>A lot clearer.</span></h1><p>From one home’s choices to a building that shares.</p><button onClick={()=>jump(0)}>Open the building <span aria-hidden="true">↓</span></button></header>
  <nav className="info-chapter-nav" aria-label="Info chapters">{[0,3,7,9].map((i,g)=><button key={i} onClick={()=>jump(i)} aria-current={Math.min(3,frame.step<3?0:frame.step<7?1:frame.step<9?2:3)===g?'step':undefined}>{['The building','The conversation','When things change','The bigger picture'][g]}</button>)}</nav>
  <div className="info-journey">
   <aside className="info-scene" aria-label="Animated building explanation">
    <div className="info-scene-top"><TrussMark size={23}/><span>AN ILLUSTRATED WALKTHROUGH</span><span>{String(frame.step+1).padStart(2,'0')} / 12</span></div>
    <BuildingScene step={frame.step} phase={frame.phase}/>
    <p className="info-scene-caption" key={frame.step}>{CHAPTERS[frame.step].scene}</p>
    <div className="info-scene-progress" aria-hidden="true">{CHAPTERS.map((c,i)=><span key={c.id} className={i<=frame.step?'is-read':''}/>)}</div>
   </aside>
   <div className="info-chapters">{CHAPTERS.map((chapter,i)=><section key={chapter.id} id={`info-${chapter.id}`} className={'info-chapter'+(frame.step===i?' is-current':'')} aria-labelledby={`info-title-${chapter.id}`}>
    <div className="info-static-scene"><BuildingScene step={i} phase={1}/></div>
    <span className="info-chapter-index">{String(i+1).padStart(2,'0')} <span/> {chapter.group}</span>
    <h2 id={`info-title-${chapter.id}`}>{chapter.title}</h2><p>{chapter.copy}</p>
    {i===11?<div className="info-next"><a href="/example">Walk the example ↗</a><a href="/lab">Explore the Lab ↗</a></div>:null}
   </section>)}</div>
  </div>
  <div className="info-outro"><TrussMark size={52}/><p>Now you know what holds it together.</p><a href="/credits">Meet the people behind it ↗</a></div>
 </main>;
}
