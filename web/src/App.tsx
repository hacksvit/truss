import {useEffect,useRef,useState} from 'react';
import Showcase from './routes/Showcase';
import Console from './routes/Console';
import Lab from './routes/Lab';
import Example from './routes/Example';
import Chrome from './components/Chrome';

function Stub({title}:{title:string}){return <main className="empty"><h2>{title}</h2><p>Not built yet. The shell, navigation and theming are in place; this page's content is the next piece of work.</p><p className="muted"><a href="/console">Console</a> · <a href="/lab">Lab</a></p></main>;}

const OUT_MS=290;   // must stay in step with the tab-out stagger in chrome.css

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

  const pop=()=>{ clearTimeout(timer.current); setLeaving(false); setRoute(location.pathname); };
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
  :route==='/info'?<Stub title="Info"/>
  :route==='/example'?<Example/>
  :route==='/credits'?<Stub title="Credits"/>
  :<Showcase/>;

 return <>
  <Chrome route={route}/>
  <div className="chrome-spacer"/>
  <div className={'route-view'+(leaving?' is-leaving':'')} key={route}>{page}</div>
 </>;
}
