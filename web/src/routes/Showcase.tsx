import {useEffect,useRef,useState,type CSSProperties} from 'react';
import TrussMark from '../components/TrussMark';
import CloudLayers from '../components/CloudLayers';
import './showcase.css';

const TOPICS=[
 {t:'Power Limits',p:'Too many appliances at once can overload one shared power supply.'},
 {t:'Essentials First',p:'We keep power for each home’s essentials before sharing the rest.'},
 {t:'Your Privacy',p:'Homes share how much power they need, not their appliance lists.'},
 {t:'Fair Shares',p:'We share spare power fairly until each home’s request is filled.'},
 {t:'Local Choice',p:'Each home picks the appliances that fit within its power allowance.'},
 {t:'Short Permissions',p:'When permission runs out, each home returns to its agreed basic power.'},
 {t:'Missing Readings',p:'Missing readings stay unknown, and earlier power promises still count.'},
 {t:'Try Truss',p:'Explore three homes, or watch five virtual homes in the live console.'}
];
const clamp=(n:number)=>Math.max(0,Math.min(1,n));
const smooth=(n:number)=>{const t=clamp(n);return t*t*(3-2*t);};
// The eight visible joints in the original 730 × 730 Truss artwork.
// Each card is the same DOM element as one joint: position, size and corner
// radius interpolate continuously from that point into its finished card.
const JOINTS=[[232,48],[498,48],[683,227],[682,506],[498,680],[232,680],[48,506],[48,227]];
const LAST=TOPICS.length-1;
// Reuse the original photography, including alternate crops for the two new topics.
const PICTURES=[1,5,2,3,2,4,6,1];

export default function Showcase(){
 const journey=useRef<HTMLElement>(null),stage=useRef<HTMLDivElement>(null);
 const [active,setActive]=useState(0);
 const [showStory,setShowStory]=useState(false);
 const reduced=useRef(false);
 useEffect(()=>{
  const section=journey.current,el=stage.current;if(!section||!el)return;
  const media=matchMedia('(prefers-reduced-motion: reduce)');
  const emblem=el.querySelector<HTMLElement>('.hero-emblem')!;
  const cards=Array.from(el.querySelectorAll<HTMLElement>('.story-card'));
  const clouds=Array.from(el.querySelectorAll<HTMLElement>('.home-atmosphere .cloud-layer'));
  let raf=0,lastActive=-1,lastStory=false;
  const render=()=>{
   raf=0;reduced.current=media.matches;
   if(media.matches){lastStory=true;setShowStory(true);document.documentElement.style.setProperty('--story-focus','0');clouds.forEach(cloud=>cloud.style.removeProperty('translate'));el.style.setProperty('--cloud-mist-opacity','1');return;}
   const stickyTop=parseFloat(getComputedStyle(el).top)||90;
   const p=clamp((stickyTop-section.getBoundingClientRect().top)/Math.max(1,section.offsetHeight-el.offsetHeight));
   const dissolve=smooth((p-.025)/.13),release=smooth((p-.035)/.13),reveal=smooth((p-.29)/.065);
   const cursor=clamp((p-.37)/.60)*LAST;
   const inStory=p>.29;if(inStory!==lastStory){lastStory=inStory;setShowStory(inStory);}
   el.style.setProperty('--intro-opacity',String(1-dissolve));
   el.style.setProperty('--intro-rise',`${-dissolve*60}px`);
   el.style.setProperty('--cloud-rise',`${-p*70}px`);
   // Independent translate composes with the existing route entrance/exit
   // transform. Each bank leaves toward its own side, back layers first.
   clouds.forEach((cloud,i)=>{
    const depart=smooth((p-.055-Math.floor(i/2)*.026)/.22);
    cloud.style.translate=`${(i%2===0?-1:1)*depart*innerWidth*.78}px ${-depart*el.offsetHeight*(.14+Math.floor(i/2)*.045)}px`;
   });
   el.style.setProperty('--cloud-opacity','1');
   el.style.setProperty('--cloud-mist-opacity',String(1-smooth((p-.06)/.15)));
   el.style.setProperty('--cards-opacity',String(reveal));
   document.documentElement.style.setProperty('--story-focus',String(reveal));
   el.style.setProperty('--mark-opacity',String(1-smooth((p-.035)/.10)));
   const mobile=innerWidth<=700;
   const width=mobile?innerWidth*.88:Math.max(440,Math.min(640,innerWidth*.49));
   const height=Math.min(600,el.offsetHeight*.76);
   const centerY=el.offsetHeight*.14+height/2;
   const spacing=width+36;
   const markWidth=emblem.offsetWidth,markTop=emblem.offsetTop,dot=markWidth*88/730;
   cards.forEach((card,i)=>{
    const grow=smooth((p-.14-i*.006)/.18);
    const [jx,jy]=JOINTS[i];
    const startX=(jx/730-.5)*markWidth,startY=markTop+jy/730*markWidth;
    const angle=Math.atan2(jy-365,jx-365);
    const separatedX=startX+Math.cos(angle)*release*90;
    const separatedY=startY+Math.sin(angle)*release*55+release*30;
    const d=i-cursor,far=Math.abs(d);
    const x=separatedX*(1-grow)+d*spacing*grow;
    const y=separatedY*(1-grow)+(centerY+far*far*12)*grow;
    const w=dot+(width-dot)*grow,h=dot+(height-dot)*grow;
    card.style.width=`${w}px`;card.style.height=`${h}px`;
    card.style.borderRadius=`${Math.min(w,h)/2*(1-grow)+12*grow}px`;
    card.style.transform=`translate3d(${x}px,${y}px,${-Math.min(far,3)*170*grow}px) translate(-50%,-50%) rotateY(${-Math.max(-2,Math.min(2,d))*27*grow}deg)`;
    card.style.setProperty('--growth',String(grow));
    card.style.setProperty('--content-opacity',String(smooth((grow-.65)/.35)));
    const titleFocus=smooth((1.5-far)/1.1),lineFocus=smooth((1.2-far)/1.05);
    card.style.setProperty('--title-opacity',String(.35+.65*titleFocus));
    card.style.setProperty('--line-opacity',String(.2+.8*lineFocus));
    card.style.setProperty('--title-shift',`${(1-titleFocus)*24}px`);
    card.style.setProperty('--line-shift',`${(1-lineFocus)*34}px`);
    card.style.opacity=String(smooth(p/.025)*(1-grow+grow*Math.max(0,1-Math.max(0,far-1)*.65)));
    card.style.zIndex=String(20-Math.round(far*2));
   });
   const selected=Math.round(cursor);if(selected!==lastActive){lastActive=selected;setActive(selected);}
  };
  const schedule=()=>{if(!raf)raf=requestAnimationFrame(render);};
  render();addEventListener('scroll',schedule,{passive:true});addEventListener('resize',schedule);media.addEventListener('change',schedule);
  return()=>{document.documentElement.style.removeProperty('--story-focus');cancelAnimationFrame(raf);removeEventListener('scroll',schedule);removeEventListener('resize',schedule);media.removeEventListener('change',schedule);};
 },[]);
 const go=(i:number)=>{
  const section=journey.current,el=stage.current;if(!section||!el)return;
  if(reduced.current){document.getElementById(`story-${i}`)?.scrollIntoView({block:'center'});return;}
  const top=section.getBoundingClientRect().top+scrollY-(parseFloat(getComputedStyle(el).top)||90);
  scrollTo({top:top+(section.offsetHeight-el.offsetHeight)*(.37+i/LAST*.60),behavior:'smooth'});
 };
 return <main className="home-page">
  <section className="home-journey" ref={journey} aria-label="The Truss story">
   <div className="home-stage" ref={stage}>
    <div className="home-atmosphere"><CloudLayers/></div>
    <div className="hero-emblem" aria-hidden="true">
     <div className="whole-mark"><TrussMark size={200}/></div>

    </div>
    <div className="home-intro" inert={showStory&&!reduced.current}>
     <p className="home-eyebrow">A LITTLE COORDINATION. A LOT MORE POSSIBILITY.</p>
     <h1>TRUSS</h1>
     <p className="home-problem">One shared supply. Too many things switched on.</p>
     <p className="home-solution">We share the spare power fairly, keeping the essentials first.</p>
     <div className="home-actions"><a href="/example">Explore the example <span aria-hidden="true">↗</span></a><button onClick={()=>go(0)}>How it works <span aria-hidden="true">↓</span></button></div>
    </div>
    <div className="scroll-invitation" aria-hidden="true"><span/>SCROLL TO UNBIND THE STORY</div>
    <div className="story-carousel" role="region" aria-label="How Truss works" aria-roledescription="carousel" onKeyDown={e=>{if(e.key==='ArrowRight'){e.preventDefault();go(Math.min(LAST,active+1));}if(e.key==='ArrowLeft'){e.preventDefault();go(Math.max(0,active-1));}}}>
     <div className="story-heading"><p>PIECE BY PIECE</p><h2>A simpler way to share.</h2></div>
     <div className="story-card-space">{TOPICS.map((t,i)=><article className="story-card" style={{'--dot-color':i===0||i===6||i===7?'var(--truss-logo-structure)':'var(--truss-logo-web)'} as CSSProperties} id={`story-${i}`} key={t.t} aria-label={`${i+1} of ${TOPICS.length}: ${t.t}`}>
      <div className="story-backdrop" aria-hidden="true"><img src={`/topics/t${PICTURES[i]}.jpg`} alt="" decoding="async" style={{objectPosition:i===4?'75% center':i===7?'25% center':'center'}}/></div>
      <div className="story-copy"><h3>{t.t}</h3><p>{t.p}</p></div>
     </article>)}</div>
     <div className="story-controls" inert={!showStory}><button aria-label="Previous story card" disabled={active===0} onClick={()=>go(active-1)}>←</button><div className="story-dots">{TOPICS.map((t,i)=><button key={t.t} aria-label={`Show card ${i+1}: ${t.t}`} aria-current={i===active?'step':undefined} onClick={()=>go(i)}><span/></button>)}</div><button aria-label="Next story card" disabled={active===LAST} onClick={()=>go(active+1)}>→</button><span className="story-count" aria-live="polite">0{active+1} / 08</span></div>
    </div>
   </div>
  </section>
  <footer className="home-footer">
   <CloudLayers variant="footer"/>
   <div className="footer-top"><a className="footer-lockup" href="/" aria-label="Truss home"><TrussMark size={36}/><span>TRUSS</span></a><div><p>EXPLORE</p><a href="/example">Walk the example ↗</a><a href="/console">Live console ↗</a><a href="/lab">Try the lab ↗</a></div><div><p>BUILD WITH US</p><a href="https://github.com/hacksvit/truss" target="_blank" rel="noreferrer">GitHub ↗</a><a href="https://github.com/hacksvit/truss#readme" target="_blank" rel="noreferrer">Read the project ↗</a></div></div>
   <div className="footer-message"><p>Less overload. More looking out for each other.</p><h2>Power is shared.<br/><span>So is the possibility.</span></h2><a href="/example">Step into the neighbourhood <span aria-hidden="true">↗</span></a></div>
   <div className="footer-wordmark" aria-label="Truss"><TrussMark size={180}/><span>TRUSS</span></div>
   <div className="footer-bottom"><span>BUILT TO SHARE. DESIGNED TO KEEP PROMISES.</span><span>Local coordination · Virtual appliances · Open source</span><a href="#" onClick={e=>{e.preventDefault();scrollTo({top:0,behavior:reduced.current?'instant':'smooth'});}}>Back to top ↑</a></div>
  </footer>
 </main>;
}
