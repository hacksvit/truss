import {getState} from './api';
import {isSnapshot,type Snapshot,type Source} from './contracts';
export type Connection='connecting'|'connected'|'polling'|'stale';
export function acceptRevision(previous:Snapshot|null,next:Snapshot,source:Source):boolean {
 return next.source===source && (!previous || next.stream_id!==previous.stream_id || (next.run_id===previous.run_id && next.revision>previous.revision));
}
export function connect(source:Source,onSnapshot:(s:Snapshot)=>void,onStatus:(s:Connection)=>void):()=>void {
 let disposed=false, ws:WebSocket|null=null, previous:Snapshot|null=null,last=0,lastWS=0,attempt=0,polling=false;
 let retry:ReturnType<typeof setTimeout>|undefined;
 const receive=(value:unknown)=>{if(isSnapshot(value)&&acceptRevision(previous,value,source)){previous=value;last=Date.now();onSnapshot(value);return true;}return false;};
 const open=()=>{
  if(disposed)return;
  onStatus('connecting');
  ws=new WebSocket(`${location.protocol==='https:'?'wss:':'ws:'}//${location.host}/ws/v1/state?source=${source}`,'truss.ui.v1');
  ws.onmessage=e=>{try {const f=JSON.parse(e.data);if(f.type==='ping')ws?.send(JSON.stringify({type:'pong',id:f.id}));if(f.type==='snapshot'&&receive(f.data)){lastWS=Date.now();attempt=0;onStatus('connected');}}catch{onStatus('stale');}};
  ws.onclose=()=>{if(disposed)return;onStatus('stale');retry=setTimeout(open,Math.min(5000,500*2**attempt++)*(.8+Math.random()*.4));};
  ws.onerror=()=>ws?.close();
 };
 const timer=setInterval(async()=>{
  if(Date.now()-last>1500)onStatus('stale');
  if(Date.now()-lastWS>2000&&!polling){polling=true;const started=Date.now();try {const s=await getState(source);if(!disposed&&lastWS<started&&receive(s))onStatus('polling');}catch{if(!disposed)onStatus('stale');}finally{polling=false;}}
 },1000);
 open();
 return()=>{disposed=true;clearInterval(timer);clearTimeout(retry);ws?.close();};
}
