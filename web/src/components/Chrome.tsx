import {useEffect,useState} from 'react';
import {flushSync} from 'react-dom';
import TrussMark from './TrussMark';
import {IconHome,IconInfo,IconExample,IconConsole,IconLab,IconCredits,IconSun,IconMoon} from './icons';

export const NAV=[{href:'/',label:'HOME',Icon:IconHome},{href:'/info',label:'INFO',Icon:IconInfo},{href:'/example',label:'EXAMPLE',Icon:IconExample},{href:'/console',label:'CONSOLE',Icon:IconConsole},{href:'/lab',label:'LAB',Icon:IconLab},{href:'/credits',label:'CREDITS',Icon:IconCredits}];

function stored(){try{const v=localStorage.getItem('truss-theme');if(v==='light'||v==='dark')return v;}catch{}return null;}
function initialTheme(){
 if(typeof matchMedia!=='function') return stored()??'dark';
 return stored()??(matchMedia('(prefers-color-scheme: light)').matches?'light':'dark');
}

export default function Chrome({route}:{route:string}){
 const [theme,setTheme]=useState(initialTheme);
 useEffect(()=>{document.documentElement.dataset.theme=theme;try{localStorage.setItem('truss-theme',theme);}catch{}},[theme]);
 const next=theme==='dark'?'light':'dark';

 function toggle(e:React.MouseEvent<HTMLButtonElement>){
  const r=e.currentTarget.getBoundingClientRect();
  const x=r.left+r.width/2, y=r.top+r.height/2;
  const radius=Math.hypot(Math.max(x,innerWidth-x),Math.max(y,innerHeight-y));
  const root=document.documentElement;
  const doc=document as Document&{startViewTransition?:(cb:()=>void)=>{finished:Promise<void>}};
  const apply=()=>{flushSync(()=>setTheme(next));root.dataset.theme=next;};
  if(!doc.startViewTransition||(typeof matchMedia==='function'&&matchMedia('(prefers-reduced-motion: reduce)').matches)){apply();return;}
  // The reveal is a CSS keyframe, not a JS animation. A JS animation added after
  // t.ready races the transition: with no CSS animation declared the browser sees
  // zero animations and resolves finished immediately, tearing the pseudo-elements
  // down mid-sweep. Declaring it in CSS makes finished wait for it properly.
  root.style.setProperty('--sweep-x',x+'px');
  root.style.setProperty('--sweep-y',y+'px');
  root.style.setProperty('--sweep-r',radius+'px');
  root.classList.add('theme-sweep');
  const cleanup=()=>{
   root.classList.remove('theme-sweep');
   for(const k of ['--sweep-x','--sweep-y','--sweep-r']) root.style.removeProperty(k);
  };
  doc.startViewTransition(apply).finished.then(cleanup,cleanup);
 }

 return <div className="truss-chrome">
  <div className="truss-chrome__slot"><a className="truss-lockup" href="/" aria-label="Truss home"><TrussMark size={32}/><span className="truss-wordmark">TRUSS</span></a></div>
  <nav className="dash pixel-dash" aria-label="Main navigation">
   {NAV.map(({href,label,Icon})=><a key={href} className="dash-item pixel-item" href={href} aria-current={route===href?'page':undefined}><Icon/><span className="dash-item__label">{label}</span></a>)}
  </nav>
  <div className="truss-chrome__slot truss-chrome__slot--right">
   <button className="cog pixel-item" onClick={toggle} aria-label={'Switch to '+next+' theme'} title={'Switch to '+next+' theme'}>
    <span className="cog__glyph" key={theme}>{theme==='dark'?<IconSun/>:<IconMoon/>}</span>
   </button>
  </div>
 </div>;
}
