import type {CSSProperties} from 'react';
import './clouds.css';

/** The same stack exits from back to front and rebuilds from the opposite side. */
export default function CloudLayers({hidden=false,variant='home'}:{hidden?:boolean;variant?:'home'|'example'|'footer'}){
 if(variant==='example')return <div className={`cloud-stack cloud-stack--example${hidden?' clouds-away':''}`} aria-hidden="true">
  <div className="cloud-layer cloud-layer--robot" style={{'--layer':0} as CSSProperties}>
   <img src="/clouds/cloud-robot.png" alt="" width={1560} height={688} draggable="false"/>
  </div>
 </div>;
 return <div className={`cloud-stack cloud-stack--${variant}${hidden?' clouds-away':''}`} aria-hidden="true">
  {Array.from({length:6},(_,i)=><div className={`cloud-layer cloud-layer--${i}`} key={i} style={{'--layer':i} as CSSProperties}>
   <img src="/clouds/cloud.png" alt="" width={626} height={276} draggable="false"/>
  </div>)}
 </div>;
}
