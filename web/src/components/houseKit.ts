import * as THREE from 'three';
import {GLTFLoader} from 'three/examples/jsm/loaders/GLTFLoader.js';

/** Asset loading and interior construction for the site scene.
 *  Shells and the character are downloaded CC0 models; interiors are authored
 *  because they have to open up and hold placed appliances and wiring. */

export type DeviceId='protected-load'|'router'|'charger'|'heater';

export interface DeviceSpec{
 id:DeviceId; label:string; baseline:number; max:number;
 policy:'protected'|'flexible'; priority:number;
}

/** Verbatim from config/member-*.json — the devices the backend actually runs. */
export const DEVICES:DeviceSpec[]=[
 {id:'protected-load',label:'Protected load',baseline:120,max:120,policy:'protected',priority:100},
 {id:'router',label:'Router + lighting',baseline:40,max:40,policy:'protected',priority:90},
 {id:'charger',label:'Charger',baseline:0,max:180,policy:'flexible',priority:60},
 {id:'heater',label:'Heater',baseline:0,max:650,policy:'flexible',priority:20}
];

/** Mirror of src/truss/local_policy.py assign(): baselines first, then the
 *  surplus down the flexible devices by descending priority. */
export function assign(budget:number):Record<DeviceId,number>{
 const out={} as Record<DeviceId,number>;
 let remaining=budget;
 for(const d of DEVICES){ out[d.id]=d.baseline; remaining-=d.baseline; }
 for(const d of [...DEVICES].sort((a,b)=>b.priority-a.priority)){
  if(d.policy!=='flexible') continue;
  const extra=Math.max(0,Math.min(remaining,d.max-d.baseline));
  out[d.id]+=extra; remaining-=extra;
 }
 return out;
}

const loader=new GLTFLoader();
const load=(url:string)=>new Promise<THREE.Group>((res,rej)=>
 loader.load(url,g=>res(g.scene),undefined,rej));

export interface Kit{
 shells:THREE.Group[];
 robot:THREE.Group|null;
 clips:THREE.AnimationClip[];
 appliances:Partial<Record<DeviceId,THREE.Group>>[];
}

/** Per-home model sets. Every home runs the SAME four device roles — that is
 *  what config/member-*.json says — but each gets its own models so the three
 *  interiors read as different households rather than copies. */
export const APPLIANCE_SETS:Record<DeviceId,{url:string;height:number}>[]=[
 {
  'protected-load':{url:'/models/fridge_A.gltf',height:.62},
  'router':{url:'/models/lamp_standing.gltf',height:.58},
  'charger':{url:'/models/car_hatchback.gltf',height:.34},
  'heater':{url:'/models/oven.gltf',height:.52}
 },
 {
  'protected-load':{url:'/models/fridge_B.gltf',height:.60},
  'router':{url:'/models/lamp_table.gltf',height:.30},
  'charger':{url:'/models/car_hatchback.gltf',height:.34},
  'heater':{url:'/models/stove_single.gltf',height:.48}
 },
 {
  'protected-load':{url:'/models/fridge_A_decorated.gltf',height:.62},
  'router':{url:'/models/lamp_standing.gltf',height:.58},
  'charger':{url:'/models/car_hatchback.gltf',height:.34},
  'heater':{url:'/models/stove_multi.gltf',height:.50}
 }
];

/** Fetches the CC0 shells and the rigged character. Resolves with whatever
 *  arrived; a failed fetch yields nulls so the caller can fall back. */
export async function loadKit():Promise<Kit>{
 const shellUrls=['/models/building_A.gltf','/models/building_B.gltf','/models/building_F.gltf'];
 const results=await Promise.allSettled([
  ...shellUrls.map(load),
  new Promise<{scene:THREE.Group;animations:THREE.AnimationClip[]}>((res,rej)=>
   loader.load('/models/robot.glb',g=>res({scene:g.scene as THREE.Group,animations:g.animations}),undefined,rej))
 ]);
 const shells:THREE.Group[]=[];
 for(let i=0;i<shellUrls.length;i++){
  const r=results[i];
  if(r.status==='fulfilled') shells.push(r.value as THREE.Group);
 }
 const robotRes=results[shellUrls.length];
 let robot:THREE.Group|null=null, clips:THREE.AnimationClip[]=[];
 if(robotRes.status==='fulfilled'){
  const v=robotRes.value as {scene:THREE.Group;animations:THREE.AnimationClip[]};
  robot=v.scene; clips=v.animations;
 }
 const cache=new Map<string,THREE.Group>();
 const appliances:Partial<Record<DeviceId,THREE.Group>>[]=[];
 for(const set of APPLIANCE_SETS){
  const out:Partial<Record<DeviceId,THREE.Group>>={};
  for(const id of Object.keys(set) as DeviceId[]){
   const url=set[id].url;
   try{
    if(!cache.has(url)) cache.set(url,await load(url));
    out[id]=cache.get(url);
   }catch{ /* box fallback */ }
  }
  appliances.push(out);
 }
 return {shells,robot,clips,appliances};
}

/** Scale a model to a target HEIGHT and sit it on the floor. */
export function fitToHeight(obj:THREE.Object3D,target:number){
 const box=new THREE.Box3().setFromObject(obj);
 const size=new THREE.Vector3(); box.getSize(size);
 const s=target/(size.y||1);
 obj.scale.setScalar(s);
 const b2=new THREE.Box3().setFromObject(obj);
 obj.position.y-=b2.min.y;
 return s;
}

/** Scale a loaded model so its longest horizontal edge matches `target`,
 *  and sit it on y=0. KayKit pieces arrive at wildly different sizes. */
export function fitToGround(obj:THREE.Object3D,target:number){
 const box=new THREE.Box3().setFromObject(obj);
 const size=new THREE.Vector3(); box.getSize(size);
 const span=Math.max(size.x,size.z)||1;
 const s=target/span;
 obj.scale.setScalar(s);
 const box2=new THREE.Box3().setFromObject(obj);
 obj.position.y-=box2.min.y;
 return s;
}

export interface Appliance{
 spec:DeviceSpec;
 group:THREE.Group;
 body:THREE.Mesh;
 lamp:THREE.Mesh;
 wire:THREE.Mesh;
 wireMat:THREE.MeshBasicMaterial;
 lampMat:THREE.MeshStandardMaterial;
 watts:number;
 pulseTex:THREE.Texture;
 pulseMat:THREE.MeshBasicMaterial;
}

/** One home's interior: a floor, a meter post, and the four appliances with a
 *  wire running from each back to the meter. */
export function buildInterior(colours:{floor:THREE.Color;wall:THREE.Color;accent:THREE.Color;muted:THREE.Color},
                              agentName='HOME'){
 const root=new THREE.Group();
 root.name='interior';

 const floorMat=new THREE.MeshStandardMaterial({color:colours.floor,roughness:.95,metalness:0});
 const floor=new THREE.Mesh(new THREE.BoxGeometry(1.9,.05,1.9),floorMat);
 floor.position.y=.03; root.add(floor);

 const postMat=new THREE.MeshStandardMaterial({color:colours.accent,roughness:.4,metalness:.3,
   emissive:colours.accent.clone().multiplyScalar(.3)});
 const meter=new THREE.Mesh(new THREE.BoxGeometry(.2,.44,.14),postMat);
 meter.position.set(0,.28,-.76); root.add(meter);

 // the household agent: the thing that actually holds the lease for this home
 const agent=makeLabel(agentName,['—','—']);
 agent.sprite.scale.set(1.35,.68,1);
 agent.sprite.position.set(0,.95,-.72);
 root.add(agent.sprite);

 const spots:[number,number][]=[[-.56,-.34],[.56,-.34],[-.56,.52],[.56,.52]];
 const appliances:Appliance[]=[];

 DEVICES.forEach((spec,i)=>{
  const [x,z]=spots[i];
  const g=new THREE.Group(); g.position.set(x,0,z);

  const h=spec.id==='heater'?.5:spec.id==='charger'?.3:.36;
  const bodyMat=new THREE.MeshStandardMaterial({color:colours.wall,roughness:.7,metalness:.08});
  const body=new THREE.Mesh(new THREE.BoxGeometry(.42,h,.3),bodyMat);
  body.position.y=h/2; g.add(body);

  const lampMat=new THREE.MeshStandardMaterial({color:colours.muted,roughness:.3,
    emissive:new THREE.Color(0x000000)});
  const lamp=new THREE.Mesh(new THREE.SphereGeometry(.045,14,12),lampMat);
  lamp.position.set(.13,h-.07,.16); g.add(lamp);

  // wire from the device back to the meter post
  const from=new THREE.Vector3(x,.07,z);
  const to=new THREE.Vector3(0,.14,-.76);
  const mid=from.clone().lerp(to,.5); mid.y+=.02;
  const wireMat=new THREE.MeshBasicMaterial({color:colours.muted,transparent:true,opacity:.5});
  const wire=new THREE.Mesh(
   new THREE.TubeGeometry(new THREE.QuadraticBezierCurve3(from,mid,to),24,.016,6,false),wireMat);
  root.add(wire);

  // a second, additive tube over the same path carries the travelling pulse
  const pulseTex=pulseTexture();
  const pulseMat=new THREE.MeshBasicMaterial({map:pulseTex,color:colours.accent,
    transparent:true,opacity:0,blending:THREE.AdditiveBlending,depthWrite:false});
  const pulse=new THREE.Mesh(
   new THREE.TubeGeometry(new THREE.QuadraticBezierCurve3(from,mid,to),24,.026,6,false),pulseMat);
  root.add(pulse);

  root.add(g);
  appliances.push({spec,group:g,body,lamp,wire,wireMat,lampMat,watts:spec.baseline,pulseTex,pulseMat});
 });

 /** Replace each placeholder box with its CC0 model once the kit lands. */
 function useModels(models:Partial<Record<DeviceId,THREE.Group>>,setIndex=0){
  const set=APPLIANCE_SETS[setIndex%APPLIANCE_SETS.length];
  for(const a of appliances){
   const src=models[a.spec.id];
   if(!src) continue;
   const inst=src.clone(true);
   const h=set[a.spec.id].height;
   fitToHeight(inst,h);
   inst.rotation.y=(setIndex*0.7)+(a.spec.id==='charger'?Math.PI/2:0);
   a.body.visible=false;
   a.group.add(inst);
   a.lamp.position.set(.17,h+.07,0);
  }
 }
 return {root,appliances,agent,useModels};
}

/** Push an allocation into an interior: lamps light, wires brighten, shed
 *  flexible loads dim and go translucent. */
export function applyAllocation(appliances:Appliance[],budget:number,accent:THREE.Color,muted:THREE.Color){
 const assigned=assign(budget);
 for(const a of appliances){
  const w=assigned[a.spec.id];
  a.watts=w;
  const on=w>0;
  const full=a.spec.max>0?w/a.spec.max:0;
  a.lampMat.emissive.copy(on?accent:new THREE.Color(0x000000)).multiplyScalar(on?.4+full*.6:0);
  a.lampMat.color.copy(on?accent:muted);
  a.wireMat.color.copy(on?accent:muted);
  a.wireMat.opacity=on?.55+full*.45:.18;
  a.pulseMat.opacity=on?0.30+full*0.55:0;      // no current, no pulse
  const lift=a.spec.policy==='flexible'&&!on?-.02:0;
  a.group.position.y=lift;
 }
 return assigned;
}


/** A free-standing credits board for the outer ground. The face is drawn to a
 *  canvas because three has no text primitive, and redrawn on theme change. */
export function buildCreditsBoard(names:string[]){
 const root=new THREE.Group();
 const canvas=document.createElement('canvas');
 canvas.width=1024; canvas.height=576;
 const tex=new THREE.CanvasTexture(canvas);
 tex.colorSpace=THREE.SRGBColorSpace;
 tex.anisotropy=4;

 function draw(bg:string,fg:string,accent:string,muted:string){
  const c=canvas.getContext('2d');
  if(!c) return;
  c.fillStyle=bg; c.fillRect(0,0,canvas.width,canvas.height);

  c.strokeStyle=accent; c.lineWidth=6;
  c.strokeRect(20,20,canvas.width-40,canvas.height-40);

  c.textAlign='center';
  c.fillStyle=accent;
  c.font='500 34px "IBM Plex Mono", ui-monospace, monospace';
  c.fillText('C R E D I T S',canvas.width/2,110);

  c.strokeStyle=muted; c.lineWidth=2;
  c.beginPath(); c.moveTo(300,146); c.lineTo(724,146); c.stroke();

  c.fillStyle=fg;
  c.font='700 54px "Space Grotesk", system-ui, sans-serif';
  names.forEach((n,i)=>c.fillText(n,canvas.width/2,232+i*68));
  tex.needsUpdate=true;
 }
 const repaint=()=>{
  const light=document.documentElement.dataset.theme==='light';
  draw(light?'#F4F8FB':'#0B1120', light?'#131A24':'#E3EDF5',
       light?'#3E7C84':'#698F93', light?'#8A97AB':'#4A5568');
 };
 repaint();
 const mo=new MutationObserver(repaint);
 mo.observe(document.documentElement,{attributes:true,attributeFilter:['data-theme']});
 const mo2=new MutationObserver(()=>frameTint());
 // the canvas is painted before the self-hosted faces finish loading, so the
 // first draw falls back to a system font (or nothing) — repaint once they land
 const f=(document as Document&{fonts?:{ready:Promise<unknown>}}).fonts;
 if(f&&f.ready) f.ready.then(repaint,()=>{});

 // Two front-facing planes rather than one DoubleSide plane: a back face shows
 // the texture mirrored, so walking round the board read "S T I D E R C".
 const faceMat=new THREE.MeshBasicMaterial({map:tex,transparent:true});
 const geo=new THREE.PlaneGeometry(4.4,2.5);
 const front=new THREE.Mesh(geo,faceMat);
 front.position.set(0,2.35,0); root.add(front);
 const rear=new THREE.Mesh(geo,faceMat);
 rear.position.set(0,2.35,-.34); rear.rotation.y=Math.PI; root.add(rear);

 const frameMat=new THREE.MeshStandardMaterial({roughness:.6,metalness:.2});
 const back=new THREE.Mesh(new THREE.BoxGeometry(4.1,2.2,.08),frameMat);
 back.position.set(0,2.35,-.17); root.add(back);
 for(const x of [-1.8,1.8]){
  const post=new THREE.Mesh(new THREE.CylinderGeometry(.09,.09,2.4,10),frameMat);
  post.position.set(x,1.2,-.17); root.add(post);
 }
 const frameTint=()=>frameMat.color.set(
  document.documentElement.dataset.theme==='light'?0xB9C7D6:0x2b3648);
 frameTint();
 mo2.observe(document.documentElement,{attributes:true,attributeFilter:['data-theme']});
 return {root,draw};
}


/** A billboarded label: a title with up to two value lines under it. Sprites
 *  always face the camera, so these stay readable from any angle. */
export function makeLabel(title:string,lines:string[]=[],w=512,h=256){
 const canvas=document.createElement('canvas');
 canvas.width=w; canvas.height=h;
 const tex=new THREE.CanvasTexture(canvas);
 tex.colorSpace=THREE.SRGBColorSpace;
 // depthTest MUST stay on: with it off the sprite draws over every wall and
 // roof, which reads as the card phasing through the buildings
 const mat=new THREE.SpriteMaterial({map:tex,transparent:true,depthTest:true,depthWrite:false});
 const sprite=new THREE.Sprite(mat);
 sprite.renderOrder=2;

 let cur={t:title,ls:lines};
 function paint(t:string,ls:string[]){
  cur={t,ls};
  const light=document.documentElement.dataset.theme==='light';
  const accent=light?'#2F6068':'#8FB4B8';
  const fg=light?'#0F1720':'#E3EDF5';
  const c=canvas.getContext('2d'); if(!c) return;
  c.clearRect(0,0,w,h);
  // a near-white panel vanished against the pale light-mode sky, so the light
  // card is tinted and given a heavier border instead
  c.fillStyle=light?'rgba(226,237,245,0.95)':'rgba(4,8,16,0.78)';
  const bw=w-24, bh=ls.length?h-40:96;
  c.beginPath(); c.roundRect(12,20,bw,bh,16); c.fill();
  c.strokeStyle=accent; c.lineWidth=light?5:3; c.stroke();

  c.textAlign='center';
  c.fillStyle=accent;
  c.font='500 30px "IBM Plex Mono", ui-monospace, monospace';
  c.fillText(t.toUpperCase(),w/2,72);
  c.fillStyle=fg;
  c.font='700 40px "Space Grotesk", system-ui, sans-serif';
  ls.forEach((l,i)=>c.fillText(l,w/2,132+i*52));
  tex.needsUpdate=true;
 }
 paint(title,lines);
 const f=(document as Document&{fonts?:{ready:Promise<unknown>}}).fonts;
 if(f&&f.ready) f.ready.then(()=>paint(title,lines),()=>{});

 // repaint when the site theme flips so the card is legible in both
 const mo=new MutationObserver(()=>paint(cur.t,cur.ls));
 mo.observe(document.documentElement,{attributes:true,attributeFilter:['data-theme']});

 return {sprite,set:(t:string,ls:string[])=>paint(t,ls),dispose:()=>mo.disconnect()};
}

/** Repeating stripe used to show current travelling along a wire. Scrolling the
 *  texture offset reads as a pulse without a custom shader. */
export function pulseTexture(){
 const c=document.createElement('canvas');
 c.width=128; c.height=4;
 const g=c.getContext('2d');
 if(g){
  const grad=g.createLinearGradient(0,0,128,0);
  // a bright crest with a trailing comet tail, twice per tile — reads as
  // discrete charge moving rather than a smear sliding along
  const crest=(at:number)=>{
   grad.addColorStop(Math.max(0,at-0.16),'rgba(255,255,255,0)');
   grad.addColorStop(Math.max(0,at-0.10),'rgba(255,255,255,0.18)');
   grad.addColorStop(Math.max(0,at-0.03),'rgba(255,255,255,0.72)');
   grad.addColorStop(at,'rgba(255,255,255,1)');
   grad.addColorStop(Math.min(1,at+0.025),'rgba(255,255,255,0.30)');
   grad.addColorStop(Math.min(1,at+0.07),'rgba(255,255,255,0)');
  };
  grad.addColorStop(0,'rgba(255,255,255,0)');
  crest(0.30); crest(0.78);
  grad.addColorStop(1,'rgba(255,255,255,0)');
  g.fillStyle=grad; g.fillRect(0,0,128,4);
 }
 const t=new THREE.CanvasTexture(c);
 t.wrapS=THREE.RepeatWrapping; t.wrapT=THREE.ClampToEdgeWrapping;
 t.repeat.set(2,1);
 return t;
}
