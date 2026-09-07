import {useEffect,useRef,useState} from 'react';
import Showcase from './routes/Showcase';
import Console from './routes/Console';
import Lab from './routes/Lab';
import Example from './routes/Example';
import Credits from './routes/Credits';
import Info from './routes/Info';
import Chrome from './components/Chrome';

const OUT_MS=780;   // includes the 540ms cloud exit + 5 × 45ms stagger

export default function App(){
 const [route,setRoute]=useState(location.pathname);
 const [leaving,setLeaving]=useState(false);
 const timer=useRef(0);

 useEffect(()=>{
  const reduced=()=>typeof matchMedia==='function'&&matchMedia('(prefers-reduced-motion: reduce)').matches;
  const swap=(href:string,push:boolean)=>{
   if(push) history.pushState({},'',href);
   setLeaving(false); setRoute(href); scrollTo({top:0});
  };

  const pop=()=>{
   clearTimeout(timer.current);const path=location.pathname;
   if(reduced()){swap(path,false);return;}
   setLeaving(true);timer.current=window.setTimeout(()=>swap(path,false),OUT_MS);
  };
  addEventListener('popstate',pop);

  const click=(e:MouseEvent)=>{
   if(e.defaultPrevented||e.button!==0||e.metaKey||e.ctrlKey||e.shiftKey||e.altKey)return;
   const a=(e.target as HTMLElement)?.closest?.('a');
   if(!a)return;
   const href=a.getAttribute('href');
   if(!href||!href.startsWith('/')||a.getAttribute('target'))return;
   e.preventDefault();
   if(href===location.pathname)return;

   if(reduced()){ swap(href,true); return; }
   // cascade the current page out, then mount the next one — which runs its own
   // staggered entrance because .route-view is keyed on the route and remounts
   setLeaving(true);
   clearTimeout(timer.current);
   timer.current=window.setTimeout(()=>swap(href,true),OUT_MS);
  };
  document.addEventListener('click',click);

  return ()=>{
   removeEventListener('popstate',pop);
   document.removeEventListener('click',click);
   clearTimeout(timer.current);
  };
 },[]);

 const page=route==='/console'?<Console/>
  :route==='/lab'?<Lab/>
  :route==='/info'?<Info/>
  :route==='/example'?<Example/>
  :route==='/credits'?<Credits/>
  :<Showcase/>;

 return <>
  <Chrome route={route}/>
  <div className="chrome-spacer"/>
  <div className={'route-view'+(leaving?' is-leaving':'')} key={route}>{page}</div>
 </>;
}
