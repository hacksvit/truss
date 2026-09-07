import {useEffect,useRef} from 'react';
import PixelText from '../components/PixelText';
import {ArtSqueeze,ArtPrivacy,ArtFairShare,ArtLease,ArtFailSafe,ArtHonest} from '../components/TopicArt';

const TOPICS=[
 {n:'01',img:'/topics/t1.jpg',t:'The squeeze',Art:ArtSqueeze,p:'Five homes share one inverter. At 7pm everyone switches on at once and the total goes over the limit. Today that means a trip, a blunt whole-floor cut, or one unlucky room absorbing all of it.'},
 {n:'02',img:'/topics/t2.jpg',t:'Offers, not appliance lists',Art:ArtPrivacy,p:'Each home runs a small agent that knows its own devices and keeps that private. It publishes two numbers: the floor it must keep, and the most it could usefully use.'},
 {n:'03',img:'/topics/t3.jpg',t:'Fair share, by rule',Art:ArtFairShare,p:'A coordinator reserves every floor first, then fills the surplus like pouring water into glasses together — small askers get all they asked for, big askers share the rest equally.'},
 {n:'04',img:'/topics/t4.jpg',t:'A lease, not a command',Art:ArtLease,p:'What comes back is permission with an expiry: this many watts, for six seconds. The clock starts when the home asks, so a slow reply can never quietly extend it.'},
 {n:'05',img:'/topics/t5.jpg',t:'Fails quiet, not loud',Art:ArtFailSafe,p:'Kill the coordinator and nothing is sent, because nobody is left to send it. Every lease simply runs out and each home drops to its own safe floor.'},
 {n:'06',img:'/topics/t6.jpg',t:'Honest about limits',Art:ArtHonest,p:'A silent home is not a home drawing zero. Missing readings stay UNKNOWN, and a cap below the protected floors reports INFEASIBLE. Software cannot invent capacity.'}
];

const LOOP=[...TOPICS,...TOPICS,...TOPICS];   // three passes so the wrap is never on screen

export default function Showcase(){
 const track=useRef<HTMLDivElement>(null);
 const stage=useRef<HTMLDivElement>(null);

 useEffect(()=>{
  const tr=track.current, st=stage.current;
  if(!tr||!st) return;
  const reduced=typeof matchMedia==='function'&&matchMedia('(prefers-reduced-motion: reduce)').matches;

  const cards=[...tr.children] as HTMLElement[];
  const one=cards.length/3;                    // cards in one pass
  let span=0, offset=0, paused=false, raf=0, last=performance.now();
  const SPEED=44;                              // px per second

  const measure=()=>{
   const a=cards[0].getBoundingClientRect(), b=cards[one].getBoundingClientRect();
   span=(b.left-a.left)+offset;                // width of one pass, transform-independent
   if(span>0) offset=span;                     // start inside the middle copy
  };

  const frame=(now:number)=>{
   const dt=Math.min(64,now-last); last=now;
   if(!paused&&!reduced&&span>0) offset+=SPEED*dt/1000;
   if(span>0&&offset>=span*2) offset-=span;    // seamless wrap
   tr.style.transform='translateX('+(-offset)+'px)';

   // curve the row inward — cards away from centre turn to face the middle
   const mid=st.getBoundingClientRect().left+st.clientWidth/2;
   const half=st.clientWidth/2;
   for(const card of cards){
    const r=card.getBoundingClientRect();
    if(r.right<-500||r.left>innerWidth+500){ card.style.visibility='hidden'; continue; }
    card.style.visibility='visible';
    const d=(r.left+r.width/2-mid)/half;
    const k=Math.max(-1.8,Math.min(1.8,d));
    const far=Math.abs(k);
    card.style.transform='rotateY('+(-k*30)+'deg) translateZ('+(-far*far*200)+'px) scale('+(1-far*0.05)+')';
    card.style.opacity=String(Math.max(0.10,1-far*0.5));
    card.style.zIndex=String(100-Math.round(far*40));
   }
   raf=requestAnimationFrame(frame);
  };

  const onResize=()=>{ offset=0; measure(); };
  measure();
  raf=requestAnimationFrame(frame);

  const enter=()=>{paused=true;}, leave=()=>{paused=false;};
  st.addEventListener('pointerenter',enter);
  st.addEventListener('pointerleave',leave);
  addEventListener('resize',onResize);
  return ()=>{
   cancelAnimationFrame(raf);
   st.removeEventListener('pointerenter',enter);
   st.removeEventListener('pointerleave',leave);
   removeEventListener('resize',onResize);
  };
 },[]);

 return <main className="showcase">
  <section className="reel-head">
   <PixelText lines={['Share the capacity.','Keep the promises.']}/>
  </section>

  <div className="reel-stage" ref={stage}>
   <div className="reel-track" ref={track}>
    {LOOP.map(({n,t,img,Art,p},i)=>
     <article className="reel-card" key={i} aria-hidden={i>=TOPICS.length}>
      <div className="reel-art" style={{backgroundImage:'url('+img+')'}}><Art/></div>
      <div className="reel-body">
       <span className="reel-n">{n}</span>
       <h2>{t}</h2>
       <p>{p}</p>
      </div>
     </article>)}
   </div>
  </div>
 </main>;
}
