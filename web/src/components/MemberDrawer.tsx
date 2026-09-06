import {useEffect,useRef,useState} from 'react';
import type {MemberView} from '../contracts';
import {watts} from '../format';
import LoadPath from './LoadPath';
export default function MemberDrawer({member,onClose}:{member:MemberView;onClose:()=>void}){
 const dialog=useRef<HTMLDialogElement>(null);const [selected,setSelected]=useState(member.devices[0]?.id);
 useEffect(()=>{dialog.current?.showModal();return()=>dialog.current?.close();},[]);
 const device=member.devices.find(d=>d.id===selected);
 return <dialog ref={dialog} className="drawer" onCancel={onClose}><button className="close" onClick={onClose} aria-label="Close household inspector">×</button><div className="section-label">HOUSEHOLD INSPECTOR / DEMO OBSERVER</div><h2>{member.id}</h2><p className="muted">Private device detail is visible to this fictional demo observer. It is not an input to the coordinator.</p><div className="device-list">{member.devices.map(d=><button key={d.id} onClick={()=>setSelected(d.id)} className={d.id===selected?'selected':''}><span>{d.label}<small>{d.control_policy}</small></span><strong>{watts(d.w)}</strong></button>)}</div>{device&&<LoadPath member={member} device={device}/>}</dialog>;
}
