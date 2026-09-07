import {useEffect,useId,useRef,useState,type CSSProperties} from 'react';
import TrussMark from '../components/TrussMark';
import {TEAM} from './creditsTeam';
import './credits.css';

const clamp=(v:number)=>Math.max(0,Math.min(1,v));
const ease=(v:number)=>{const t=clamp(v);return t*t*(3-2*t);};
const mix=(a:number,b:number,t:number)=>a+(b-a)*t;
const START=.06,SPAN=.145;

export default function Credits(){
 const section=useRef<HTMLElement>(null),stage=useRef<HTMLDivElement>(null),assembly=useRef<HTMLDivElement>(null);
 const [active,setActive]=useState(-1);
 const glow=useId();
 useEffect(()=>{
  const el=section.current,st=stage.current,scene=assembly.current;if(!el||!st||!scene)return;
  const cards=Array.from(scene.querySelectorAll<HTMLElement>('.connection-card'));
  const anchors=Array.from(scene.querySelectorAll<HTMLElement>('.connection-anchor'));
  const paths=Array.from(scene.querySelectorAll<SVGPathElement>('.connection-line'));
  const heads=Array.from(scene.querySelectorAll<SVGCircleElement>('.connection-traveller'));
  const media=matchMedia('(prefers-reduced-motion: reduce)');
  let raf=0,lastActive=-2;
  const render=()=>{
   raf=0;
   const mobile=innerWidth<=760||innerHeight<=650,reduced=media.matches;
   const bounds=el.getBoundingClientRect(),top=parseFloat(getComputedStyle(st).top)||90;
   const p=clamp((top-bounds.top)/Math.max(1,el.offsetHeight-st.offsetHeight));
   const group=reduced?1:ease((p-.82)/.14);
   st.style.setProperty('--group',String(group));st.style.setProperty('--intro',String(1-ease(p/.08)));
   const invitation=scene.querySelector<HTMLElement>('.connections-invitation')!;
   invitation.inert=p>.08||mobile||reduced;
   st.querySelector<HTMLElement>('.connections-signoff')!.inert=!mobile&&!reduced&&group<.8;
   const w=scene.clientWidth,h=scene.clientHeight;
   const cardH=Math.min(292,Math.max(194,(h-30)/2)),cardW=cardH*.77,gap=cardW+30;
   const points=[[-gap,h*.245],[0,h*.245],[gap,h*.245],[gap*.5,h*.755],[-gap*.5,h*.755]];
   paths.forEach((path,i)=>{
    const from=points[(i+4)%5],to=points[i];
    const x1=w/2+from[0],y1=from[1],x2=w/2+to[0],y2=to[1];
    const bend=i===0?-90:i<3?-80:80;
    path.setAttribute('d',`M${x1} ${y1} C${x1} ${y1+bend},${x2} ${y2+bend},${x2} ${y2}`);
    const drawn=reduced?1:ease((p-(START+i*SPAN-.05))/.10);
    path.style.strokeDashoffset=String(1-drawn);
    if(!mobile&&!reduced){
     const cursor=path.getPointAtLength(path.getTotalLength()*drawn);
     heads[i].setAttribute('cx',String(cursor.x));heads[i].setAttribute('cy',String(cursor.y));
    }
    heads[i].style.opacity=String(drawn>0&&drawn<1?1:0);
   });
   cards.forEach((card,i)=>{
    const local=(p-START-i*SPAN)/SPAN;
    const arrive=ease(local/.23),reveal=ease((local-.16)/.38),settle=ease((local-.65)/.35);
    const mobileReveal=reduced||!mobile?1:ease((innerHeight*.88-card.getBoundingClientRect().top)/(innerHeight*.42));
    const show=mobile?mobileReveal:reduced?1:reveal;
    card.style.setProperty('--reveal',String(show));
    card.style.setProperty('--caption',String(ease((show-.38)/.62)));
    card.style.setProperty('--scan',String(Math.sin(show*Math.PI)));
    card.style.setProperty('--focus-light',String(reduced||mobile?1:mix(1,.62,settle)*(1-group)+group));
    card.inert=show<.1;
    if(!mobile&&!reduced){
     const [endX,endY]=points[i];
     const x=mix(mix((i%2?-1:1)*w*.42,0,arrive),endX,settle);
     const y=mix(mix(h*.65,h*.5,arrive),endY,settle);
     const z=mix(mix(-650,65,arrive),-100*(1-group),settle);
     const rotateY=mix((i%2?-1:1)*72,0,arrive)+(endX/gap)*-7*settle*(1-group);
     card.style.width=`${cardW}px`;card.style.height=`${cardH}px`;
     card.style.transform=`translate3d(${x}px,${y}px,${z}px) translate(-50%,-50%) rotateY(${rotateY}deg) rotateX(${mix(14,0,arrive)}deg) rotateZ(${mix((i-2)*5,0,arrive)}deg) scale(${mix(1.48,1,settle)})`;
     card.style.opacity=String(ease(local/.12));card.style.zIndex=String(local>=0&&local<1?20:5);
    }else{
     for(const prop of ['width','height','transform','opacity','z-index'])card.style.removeProperty(prop);
    }
    anchors[i].style.left=`${w/2+points[i][0]}px`;anchors[i].style.top=`${points[i][1]}px`;
    anchors[i].style.setProperty('--lit',String(reduced?1:ease(local/.2)));
   });
   const selected=mobile?-1:p<START?-1:p>.84?5:Math.min(4,Math.floor((p-START)/SPAN));
   if(selected!==lastActive){lastActive=selected;setActive(selected);}
  };
  const schedule=()=>{if(!raf)raf=requestAnimationFrame(render);};
  const move=(e:PointerEvent)=>{
   if(media.matches||e.pointerType==='touch')return;
   const r=scene.getBoundingClientRect();
   st.style.setProperty('--look-x',`${(e.clientX-r.left-r.width/2)/r.width*3}deg`);
   st.style.setProperty('--look-y',`${-(e.clientY-r.top-r.height/2)/r.height*3}deg`);
  };
  const reset=()=>{st.style.setProperty('--look-x','0deg');st.style.setProperty('--look-y','0deg');};
  render();addEventListener('scroll',schedule,{passive:true});addEventListener('resize',schedule);media.addEventListener('change',schedule);
  scene.addEventListener('pointermove',move);scene.addEventListener('pointerleave',reset);
  return()=>{cancelAnimationFrame(raf);removeEventListener('scroll',schedule);removeEventListener('resize',schedule);media.removeEventListener('change',schedule);scene.removeEventListener('pointermove',move);scene.removeEventListener('pointerleave',reset);};
 },[]);
 const go=(i:number)=>{
  const el=section.current,st=stage.current;if(!el||!st)return;
  const reduced=matchMedia('(prefers-reduced-motion: reduce)').matches;
  if(innerWidth<=760||innerHeight<=650||reduced){document.getElementById(`connection-${Math.min(4,i)}`)?.scrollIntoView({block:'center',behavior:reduced?'instant':'smooth'});return;}
  const p=i===5?.99:START+i*SPAN+SPAN*.55;
  scrollTo({top:scrollY+el.getBoundingClientRect().top-(parseFloat(getComputedStyle(st).top)||90)+(el.offsetHeight-st.offsetHeight)*p,behavior:'smooth'});
 };
 return <main className="credits-page">
  <section className="connections-journey" ref={section} aria-label="The five people behind Truss">
   <div className="connections-stage" ref={stage}>
    <div className="connections-aura" aria-hidden="true"/>
    <header className="connections-heading"><p>THE PEOPLE BEHIND TRUSS</p><h1>Five people.<br className="connections-mobile-break"/> <span>One shared idea.</span></h1></header>
    <div className="connections-scene" ref={assembly}>
     <div className="connections-orbit" aria-hidden="true"><span/><span/><span/></div>
     <svg className="connections-lines" aria-hidden="true"><defs><filter id={glow}><feGaussianBlur stdDeviation="3"/></filter></defs>{TEAM.map((_,i)=><g key={i}><path className={`connection-line connection-line--${i}`} pathLength="1"/><circle className="connection-traveller" r="5" filter={`url(#${glow})`}/></g>)}</svg>
     {TEAM.map((_,i)=><div key={i} className="connection-anchor" aria-hidden="true"><span/>{String(i+1).padStart(2,'0')}</div>)}
     <div className="connections-invitation"><TrussMark size={60}/><p>Different paths.<br/>Something shared.</p><button onClick={()=>go(0)}>Follow the connection <span aria-hidden="true">↓</span></button></div>
     {TEAM.map((person,i)=><article className="connection-card" id={`connection-${i}`} key={person.id} tabIndex={0} aria-label={person.name||`Team member ${i+1}, details pending`} style={{'--member':i} as CSSProperties}>
      <div className="connection-card-depth" aria-hidden="true"/>
      <div className="connection-card-face">
       <div className="connection-portrait">
        <div className="connection-placeholder" aria-hidden="true"><span className="placeholder-orbit"/><svg viewBox="0 0 120 150"><circle cx="60" cy="48" r="24"/><path d="M15 144v-18a45 45 0 0 1 90 0v18"/></svg></div>
        <span className="connection-number">{String(i+1).padStart(2,'0')}</span><span className="connection-scan" aria-hidden="true"/>
       </div>
       <div className="connection-caption"><h2>{person.name||`Team member ${i+1}`}</h2><p>{person.contribution||'Name and contribution to be added.'}</p></div>
       <span className="connection-shine" aria-hidden="true"/>
      </div>
     </article>)}
    </div>
    <div className="connections-signoff"><p>Different strengths. <span>Built together.</span></p><a href="https://github.com/hacksvit/truss" target="_blank" rel="noreferrer">See what we built ↗</a></div>
    <nav className="connections-controls" aria-label="Meet the team"><span className="connections-progress-label">{active===5?'ALL TOGETHER':active<0?'SCROLL TO CONNECT':`CONNECTION ${String(active+1).padStart(2,'0')} / 05`}</span><div>{TEAM.map((p,i)=><button key={p.id} onClick={()=>go(i)} aria-label={p.name?`Meet ${p.name}`:`Meet team member ${i+1}`} aria-current={active===i?'step':undefined}><span/></button>)}</div><button className="connections-skip" onClick={()=>go(5)}>All five <span aria-hidden="true">↗</span></button></nav>
   </div>
  </section>
 </main>;
}
