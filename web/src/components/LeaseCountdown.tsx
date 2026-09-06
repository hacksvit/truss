import {useEffect,useState} from 'react';
import type {LeaseView} from '../contracts';
import {estimatedRemaining} from '../format';
export default function LeaseCountdown({lease}:{lease:LeaseView}){
 const [elapsed,setElapsed]=useState(0);
 useEffect(()=>{setElapsed(0);const start=performance.now();const id=setInterval(()=>setElapsed(performance.now()-start),100);return()=>clearInterval(id);},[lease]);
 const remaining=estimatedRemaining(lease.remaining_ms,elapsed);
 return <div className={`lease ${lease.quality!=='fresh'?'muted':''}`}><span>{remaining===null?'—':`~${(remaining/1000).toFixed(1)} s`}</span><small>lease estimate{lease.quality!=='fresh'?' · stale':''}</small><div className="lease-track"><div style={{width:`${(remaining??0)/60}%`}}/></div></div>;
}
