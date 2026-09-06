import {useEffect,useState} from 'react';
import TrussMark from './TrussMark';
import {IconHome,IconInfo,IconExample,IconConsole,IconLab,IconCredits,IconCog} from './icons';

export const NAV=[{href:'/',label:'HOME',Icon:IconHome},{href:'/info',label:'INFO',Icon:IconInfo},{href:'/example',label:'EXAMPLE',Icon:IconExample},{href:'/console',label:'CONSOLE',Icon:IconConsole},{href:'/lab',label:'LAB',Icon:IconLab},{href:'/credits',label:'CREDITS',Icon:IconCredits}];

function stored(){try{const v=localStorage.getItem('truss-theme');if(v==='light'||v==='dark')return v;}catch{}return null;}
function initialTheme(){return stored()??(matchMedia('(prefers-color-scheme: light)').matches?'light':'dark');}

export default function Chrome({route}:{route:string}){
 const [theme,setTheme]=useState(initialTheme);
 const [spin,setSpin]=useState(0);
 useEffect(()=>{document.documentElement.dataset.theme=theme;try{localStorage.setItem('truss-theme',theme);}catch{}},[theme]);
 const next=theme==='dark'?'light':'dark';
 return <div className="truss-chrome">
  <div className="truss-chrome__slot"><a className="truss-lockup" href="/" aria-label="Truss home"><TrussMark size={32}/><span className="truss-wordmark">TRUSS</span></a></div>
  <nav className="dash pixel-dash" aria-label="Main navigation">
   {NAV.map(({href,label,Icon})=><a key={href} className="dash-item pixel-item" href={href} aria-current={route===href?'page':undefined}><Icon/><span className="dash-item__label">{label}</span></a>)}
  </nav>
  <div className="truss-chrome__slot truss-chrome__slot--right">
   <button className="cog pixel-item" onClick={()=>{setTheme(next);setSpin(spin+180);}} aria-label={'Switch to '+next+' theme'}><span className="cog__spin" style={{transform:'rotate('+spin+'deg)'}}><IconCog/></span></button>
  </div>
 </div>;
}
