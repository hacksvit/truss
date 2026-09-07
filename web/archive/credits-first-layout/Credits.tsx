import {useEffect,useRef,type CSSProperties} from 'react';
import './credits.css';

// Replace these five empty slots with the team's confirmed names and portraits.
const TEAM:Array<{name:string;contribution:string;photo:string}> = Array.from({length:5},()=>({name:'',contribution:'',photo:''}));

export default function Credits(){
 const section=useRef<HTMLElement>(null);
 useEffect(()=>{
  const el=section.current;if(!el)return;
  const media=matchMedia('(prefers-reduced-motion: reduce)');
  const cards=Array.from(el.querySelectorAll<HTMLElement>('.team-card'));
  let raf=0;
  const render=()=>{
   raf=0;
   const stage=el.querySelector<HTMLElement>('.team-stage')!;
   const top=parseFloat(getComputedStyle(stage).top)||90;
   const progress=Math.max(0,Math.min(1,(top-el.getBoundingClientRect().top)/Math.max(1,el.offsetHeight-stage.offsetHeight)));
   cards.forEach((card,i)=>{
    const value=media.matches?1:Math.max(0,Math.min(1,(progress-i*.13)/.30));
    const eased=value*value*(3-2*value);
    card.style.setProperty('--arrival',String(eased));
   });
   stage.style.setProperty('--connected',String(media.matches?1:Math.max(0,Math.min(1,(progress-.76)/.16))));
  };
  const schedule=()=>{if(!raf)raf=requestAnimationFrame(render);};
  render();addEventListener('scroll',schedule,{passive:true});addEventListener('resize',schedule);media.addEventListener('change',schedule);
  return()=>{cancelAnimationFrame(raf);removeEventListener('scroll',schedule);removeEventListener('resize',schedule);media.removeEventListener('change',schedule);};
 },[]);
 return <main className="credits-page">
  <section className="team-journey" ref={section} aria-label="The five people behind Truss">
   <div className="team-stage">
    <header className="team-heading"><p>THE PEOPLE BEHIND TRUSS</p><h1>Built together.</h1><p>Five people. One shared idea.</p><span className="team-scroll-hint">Scroll to meet the team ↓</span></header>
    <div className="team-assembly">{TEAM.map((person,i)=><article className="team-card" key={i} style={{'--side':i%2===0?-1:1,'--tilt':`${(i-2)*8}deg`} as CSSProperties}>
     <div className="team-portrait">{person.photo?<img src={person.photo} alt=""/>:<div className="team-placeholder" aria-label="Portrait to be added"><svg viewBox="0 0 120 150" aria-hidden="true"><circle cx="60" cy="48" r="24"/><path d="M15 144v-18a45 45 0 0 1 90 0v18"/></svg><span>PORTRAIT TO BE ADDED</span></div>}</div>
     <div className="team-caption"><h2>{person.name||`Team member ${String(i+1).padStart(2,'0')}`}</h2><p>{person.contribution||'Name and contribution to be added.'}</p></div>
    </article>)}</div>
    <div className="team-signoff"><span className="team-thread" aria-hidden="true"/><p>Different strengths. Something shared.</p><a href="https://github.com/hacksvit/truss" target="_blank" rel="noreferrer">See what we built ↗</a></div>
   </div>
  </section>
 </main>;
}
