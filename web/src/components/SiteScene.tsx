import {useEffect,useRef,useState} from 'react';
import * as THREE from 'three';
import {loadKit,fitToGround,buildInterior,applyAllocation,buildCreditsBoard,makeLabel,pulseTexture} from './houseKit';
import {CoordinatorVisit} from './coordinatorVisit';
import {buildCoordinatorInternals} from './coordinatorKit';
import {SITE_MEMBERS,WANTS} from './trussModel';

function cssColor(name:string,fallback:string){
 const v=getComputedStyle(document.documentElement).getPropertyValue(name).trim();
 return new THREE.Color(v||fallback);
}

/** Three homes feeding one generator, with two camera modes.
 *  OVERVIEW — the orbiting site model; cursor gyro + drag to rotate.
 *  EXPLORE  — press F, or hold-click the generator: the camera drops to ground
 *             level and you walk a small grey doll around the courtyard with
 *             WASD. F (or Esc) returns. The doll is built from primitives and
 *             squashes as it moves, rather than being a downloaded rig. */
export default function SiteScene({onMode,onHouse,onPanel,budgets,cap=1800,panelOpen:panelVisible=false}:{
 onMode?:(m:'overview'|'explore')=>void;
 onHouse?:(h:{index:number;name:string;prompt?:boolean}|null)=>void;
 onPanel?:(open:boolean)=>void;
 budgets?:number[];
 cap?:number;
 panelOpen?:boolean;
}){
 const [loading,setLoading]=useState<'loading'|'ready'|'fallback'>('loading');
 const capRef=useRef(cap); capRef.current=cap;
 const host=useRef<HTMLDivElement>(null);
 const modeCb=useRef(onMode); modeCb.current=onMode;
 const houseCb=useRef(onHouse); houseCb.current=onHouse;
 const panelCb=useRef(onPanel); panelCb.current=onPanel;
 const budgetRef=useRef(budgets); budgetRef.current=budgets;

 useEffect(()=>{
  const el=host.current!;
  const scene=new THREE.Scene();
  const camera=new THREE.PerspectiveCamera(38,1,0.1,100);
  const renderer=new THREE.WebGLRenderer({antialias:true,alpha:true});
  renderer.setPixelRatio(Math.min(devicePixelRatio,2));
  el.appendChild(renderer.domElement);

  // Commit one complete scene only. A timeout keeps a stable fallback instead
  // of exposing temporary geometry and swapping it later on a slow connection.
  let disposed=false,settled=false;
  setLoading('loading');
  const cv=renderer.domElement;
  cv.style.opacity='0';
  cv.style.transition='opacity 300ms ease';
  const reveal=(fallback=false)=>{
   if(disposed) return;
   renderer.render(scene,camera);
   cv.style.opacity='1';
   setLoading(fallback?'fallback':'ready');
  };
  const revealTimer=window.setTimeout(()=>{
   if(disposed||settled)return;
   settled=true; reveal(true);
  },12000);

  const rig=new THREE.Group(); scene.add(rig);
  // everything except the character lives in `world`, so dropping into
  // character mode can scale the site up around you without scaling the rig
  const world=new THREE.Group(); rig.add(world);

  const mats={
   wall:new THREE.MeshStandardMaterial({roughness:.75,metalness:.05}),
   roof:new THREE.MeshStandardMaterial({roughness:.6,metalness:.1}),
   gen:new THREE.MeshStandardMaterial({roughness:.35,metalness:.4}),
   link:new THREE.MeshBasicMaterial({transparent:true,opacity:.9}),
   pad:new THREE.MeshStandardMaterial({roughness:1,metalness:0,transparent:true,opacity:.16,depthWrite:false}),
   doll:new THREE.MeshStandardMaterial({roughness:.42,metalness:.05,color:0xb9c0c6}),
   dollDark:new THREE.MeshStandardMaterial({roughness:.5,metalness:.05,color:0x8d959c})
  };
  function paint(){
   const structure=cssColor('--truss-logo-structure','#343B45');
   const web=cssColor('--truss-logo-web','#698F93');
   const accent=cssColor('--accent','#3E7C84');
   mats.wall.color.copy(structure);
   mats.roof.color.copy(web).multiplyScalar(.85);
   mats.gen.color.copy(accent);
   mats.gen.emissive.copy(accent).multiplyScalar(.25);
   mats.link.color.copy(web);
   mats.pad.color.copy(structure).multiplyScalar(.35);
  }
  paint();

  scene.add(new THREE.AmbientLight(0xffffff,.85));
  const key=new THREE.DirectionalLight(0xffffff,1.5); key.position.set(4,7,5); scene.add(key);
  const rim=new THREE.DirectionalLight(0x9fc6cc,.7); rim.position.set(-5,3,-4); scene.add(rim);

  const pad=new THREE.Mesh(new THREE.CylinderGeometry(4.3,4.3,.06,64),mats.pad);
  pad.position.y=-.03; world.add(pad);

  const grid=new THREE.GridHelper(160,160,0x6f8f95,0x44585e);
  const gridMat=grid.material as THREE.Material;
  gridMat.transparent=true; gridMat.opacity=0; grid.position.y=.005; world.add(grid);

  const gen=new THREE.Group();
  const genBody=new THREE.Mesh(new THREE.BoxGeometry(1.15,1.25,.75),mats.gen);
  gen.add(genBody);
  const fin=new THREE.Mesh(new THREE.BoxGeometry(1.3,.1,.9),mats.gen);
  fin.position.y=.72; gen.add(fin);
  gen.position.y=.62; world.add(gen);
  // The old solid body remains only as the existing raycast target. The
  // matching hollow shell and hinged door render in both open/closed states.
  genBody.visible=false;
  const coordinator=buildCoordinatorInternals(mats.gen);
  gen.add(coordinator.root);
  const coordinatorTheme=new MutationObserver(()=>coordinator.paint());
  coordinatorTheme.observe(document.documentElement,{attributes:true,attributeFilter:['data-theme']});
  const genLabel=makeLabel('coordinator',[capRef.current+' W example supply']);
  genLabel.sprite.scale.set(1.9,.95,1);
  genLabel.sprite.position.set(0,2.15,0);
  genLabel.sprite.visible=false;
  world.add(genLabel.sprite);

  const R=2.9;
  const houses:THREE.Vector3[]=[];
  const houseGroups:THREE.Group[]=[];
  const shellHolders:THREE.Group[]=[];
  const placeholders:THREE.Object3D[]=[];
  const siteLinks:THREE.Mesh[]=[];
  const sitePulses:{tex:THREE.Texture;mat:THREE.MeshBasicMaterial}[]=[];
  for(let i=0;i<3;i++){
   const a=(i/3)*Math.PI*2 - Math.PI/2;
   const h=new THREE.Group();
   const body=new THREE.Mesh(new THREE.BoxGeometry(1.05,.85,1.05),mats.wall);
   body.position.y=.42; h.add(body);
   const roof=new THREE.Mesh(new THREE.ConeGeometry(.86,.62,4),mats.roof);
   roof.position.y=1.16; roof.rotation.y=Math.PI/4; h.add(roof);
   h.position.set(Math.cos(a)*R,0,Math.sin(a)*R);
   h.rotation.y=-a+Math.PI/2;
   world.add(h); houses.push(h.position.clone());
   houseGroups.push(h);
   placeholders.push(body,roof);
   const holder=new THREE.Group(); h.add(holder); shellHolders.push(holder);

   const from=new THREE.Vector3(Math.cos(a)*R,.34,Math.sin(a)*R);
   const to=new THREE.Vector3(0,.55,0);
   const mid=from.clone().lerp(to,.5); mid.y+=.85;
   const curve=new THREE.QuadraticBezierCurve3(from,mid,to);
   const tube=new THREE.Mesh(new THREE.TubeGeometry(curve,28,.045,8,false),mats.link);
   world.add(tube);siteLinks.push(tube);
   const ptex=pulseTexture();
   const pmat=new THREE.MeshBasicMaterial({map:ptex,transparent:true,opacity:.5,
     blending:THREE.AdditiveBlending,depthWrite:false});
   const ptube=new THREE.Mesh(new THREE.TubeGeometry(curve,28,.062,8,false),pmat);
   world.add(ptube);siteLinks.push(ptube);
   sitePulses.push({tex:ptex,mat:pmat});
  }

  // ---- the doll: primitives with squash/stretch, no external rig ----
  const doll=new THREE.Group();
  const squash=new THREE.Group(); doll.add(squash);
  const torso=new THREE.Mesh(new THREE.CapsuleGeometry(.16,.2,6,14),mats.doll);
  torso.position.y=.30; squash.add(torso);
  const head=new THREE.Mesh(new THREE.SphereGeometry(.155,20,16),mats.doll);
  head.position.y=.60; squash.add(head);
  const armL=new THREE.Mesh(new THREE.SphereGeometry(.075,12,10),mats.dollDark);
  const armR=armL.clone();
  armL.position.set(-.20,.34,0); armR.position.set(.20,.34,0);
  squash.add(armL,armR);
  const legL=new THREE.Mesh(new THREE.SphereGeometry(.085,12,10),mats.dollDark);
  const legR=legL.clone();
  legL.position.set(-.09,.09,0); legR.position.set(.09,.09,0);
  squash.add(legL,legR);
  doll.position.set(0,0,1.9); doll.visible=false; rig.add(doll);

  // populated once the CC0 kit arrives; the primitive doll above is the fallback
  let mixer:THREE.AnimationMixer|null=null;
  let robotRoot:THREE.Group|null=null;
  let actIdle:THREE.AnimationAction|null=null;
  let actWalk:THREE.AnimationAction|null=null;
  let actRun:THREE.AnimationAction|null=null;
  let current:THREE.AnimationAction|null=null;
  const interiors:ReturnType<typeof buildInterior>[]=[];
  const shellMats:THREE.Material[]=[];
  let nearHouse=-1, inside=-1, insideBlend=0;
  let lastBudgets='';
  let nearCoord=false, panelOpen=false, panelBlend=0, panelZoom=1;
  const visit=new CoordinatorVisit();
  const panelCamera=new THREE.Vector3(),panelAim=new THREE.Vector3(),landing=new THREE.Vector3();
  const savedFollow=new THREE.Vector3(),savedAim=new THREE.Vector3();
  let savedFollowInit=false,savedFirstPerson=false;
  const panelLook={x:0,y:0};

  // credits board, out in the open ground beyond the site
  const credits=buildCreditsBoard(['Pranav','Logesh','Prashanth','Kevin','Kalyan']);
  credits.root.position.set(0,0,6.6);
  credits.root.rotation.y=Math.PI;
  credits.root.visible=false;
  world.add(credits.root);

  let mode:'overview'|'explore'='overview';
  let firstPerson=false;
  let blend=0, blendRaw=0;
  // The camera has its OWN yaw. Input is transformed through it, so W is always
  // "away from the camera". Deriving heading from raw input instead made W mean
  // world -Z, which reads as walking backwards once the view had swung round.
  let camYaw=Math.PI, camPitch=-0.12;
  let camDist=2.5;                      // scroll wheel adjusts this
  const camFollow=new THREE.Vector3(), camAim=new THREE.Vector3();
  let followInit=false;
  let locked=false;   // pointer lock, engaged alongside first person
  let targetX=0,targetY=0, curX=0,curY=0;
  let dragging=false, lastX=0,lastY=0, velY=0,velX=0;
  let heading=Math.PI, walkPhase=0;
  const vel=new THREE.Vector3();
  const keys=new Set<string>();
  const reduced=typeof matchMedia==='function'&&matchMedia('(prefers-reduced-motion: reduce)').matches;

  const setMode=(m:'overview'|'explore')=>{
   if(mode===m) return;
   mode=m;
   if(m==='overview'&&document.pointerLockElement) document.exitPointerLock?.();
   if(m==='overview'){ inside=-1; nearHouse=-1; nearCoord=false;
    if(panelOpen){ panelOpen=false; panelCb.current?.(false); }
    houseCb.current?.(null); }
   if(m==='explore'){
    doll.position.set(0,0,1.9); doll.rotation.y=Math.PI; heading=Math.PI; vel.set(0,0,0);
    camYaw=Math.PI; camPitch=-0.12; firstPerson=false; camDist=2.5; followInit=false;
   }
   modeCb.current?.(m);
  };

  loadKit().then(kit=>{
   if(disposed||settled) return;
   settled=true; window.clearTimeout(revealTimer);
   const structure=cssColor('--truss-logo-structure','#343B45');
   const web=cssColor('--truss-logo-web','#698F93');
   const accent=cssColor('--accent','#3E7C84');

   // ---- swap the box-and-cone placeholders for the CC0 shells ----
   kit.shells.forEach((shell,i)=>{
    if(!shell) return;
    const holder=shellHolders[i];
    if(!holder) return;
    const inst=shell.clone(true);
    fitToGround(inst,1.55);
    holder.add(inst);
    inst.traverse((o:THREE.Object3D)=>{
     const m=o as THREE.Mesh;
     if(!m.isMesh) return;
     const mat=(m.material as THREE.Material).clone();
     (mat as THREE.MeshStandardMaterial).transparent=true;
     m.material=mat; shellMats.push(mat);
    });
   });
   kit.shells.forEach((shell,i)=>{if(shell){placeholders[i*2].visible=false;placeholders[i*2+1].visible=false;}});

   // ---- interiors, one per home ----
   houseGroups.forEach((h,i)=>{
    const profile=SITE_MEMBERS[i];
    const built=buildInterior({floor:new THREE.Color(0x1b2430),wall:new THREE.Color(0x39424f),accent,muted:web},
                              'agent '+profile.name,profile);
    built.root.visible=false;
    built.root.scale.setScalar(0.78);
    h.add(built.root);
    built.useModels(kit.appliances[i]||{},i);
    interiors.push(built);
    applyAllocation(built.appliances,profile,budgetRef.current?.[i]??profile.floor,
                    WANTS[profile.id],accent,web);
   });

   // ---- the rigged character replaces the primitive doll ----
   if(kit.robot){
    robotRoot=kit.robot;
    fitToGround(robotRoot,0.46);
    // no yaw offset here: the parent `doll` group is already rotated to the
    // travel heading, so an extra PI turns the model to face where it came from
    doll.add(robotRoot);
    for(const c of [...squash.children]) c.visible=false;
    mixer=new THREE.AnimationMixer(robotRoot);
    const byName=(n:string)=>kit.clips.find(c=>c.name===n)||null;
    const mk=(n:string)=>{ const c=byName(n); return c?mixer!.clipAction(c):null; };
    actIdle=mk('Idle'); actWalk=mk('Walking'); actRun=mk('Running');
    if(actIdle){ actIdle.play(); current=actIdle; }
   }
   reveal(kit.shells.some(shell=>!shell));
  }).catch(()=>{ if(disposed)return; settled=true; window.clearTimeout(revealTimer); reveal(true); });

  const isTyping=(t:EventTarget|null)=>{
   const n=t as HTMLElement|null;
   return !!n && (n.tagName==='INPUT'||n.tagName==='TEXTAREA'||n.isContentEditable);
  };
  const onKeyDown=(e:KeyboardEvent)=>{
   const k=e.key.toLowerCase();
   if(e.repeat&&['e','f','v','escape'].includes(k))return;
   if(visit.active){
    if(k==='e'||k==='escape'){e.preventDefault();visit.leave(camera);panelCb.current?.(false);}
    return;
   }
   if(isTyping(e.target)) return;
   if(k==='f'){ e.preventDefault(); setMode(mode==='explore'?'overview':'explore'); return; }
   if(k==='escape'&&mode==='explore'){ setMode('overview'); return; }
   if(k==='v'&&mode==='explore'){
    e.preventDefault();
    firstPerson=!firstPerson;
    // keydown counts as a user gesture, so the lock request is allowed here
    if(firstPerson){
     const rq=renderer.domElement.requestPointerLock?.() as unknown;
     if(rq&&typeof (rq as Promise<void>).catch==='function') (rq as Promise<void>).catch(()=>{});
    }
    else if(document.pointerLockElement) document.exitPointerLock?.();
    modeCb.current?.(mode);
    return;
   }
   if(k==='e'&&mode==='explore'){
    e.preventDefault();
    if(panelOpen){ panelOpen=false; panelCb.current?.(false); return; }
    if(inside>=0){ inside=-1; houseCb.current?.(null); return; }
    if(nearCoord){
     visit.enter(camera,doll);
     savedFollow.copy(camFollow);savedAim.copy(camAim);savedFollowInit=followInit;savedFirstPerson=firstPerson;
     panelOpen=true;panelZoom=1;panelLook.x=panelLook.y=0;keys.clear();
     if(actIdle&&current!==actIdle){current?.fadeOut(.15);actIdle.reset().fadeIn(.15).play();current=actIdle;}
     if(document.pointerLockElement)document.exitPointerLock?.();
     panelCb.current?.(true);return;
    }
    if(nearHouse>=0){ inside=nearHouse; houseCb.current?.({index:inside,name:'ABC'[inside]}); }
    return;
   }
   if('wasd'.includes(k)||k.startsWith('arrow')){ if(mode==='explore') e.preventDefault(); keys.add(k); }
  };
  const onKeyUp=(e:KeyboardEvent)=>{ keys.delete(e.key.toLowerCase()); };

  const ray=new THREE.Raycaster(); const ptr=new THREE.Vector2();
  let holdTimer=0;
  const onDown=(e:PointerEvent)=>{
   if(visit.active)return;
   const r=renderer.domElement.getBoundingClientRect();
   ptr.x=((e.clientX-r.left)/r.width)*2-1;
   ptr.y=-((e.clientY-r.top)/r.height)*2+1;
   ray.setFromCamera(ptr,camera);
   if(mode==='overview'&&ray.intersectObjects([genBody,fin],false).length>0){
    holdTimer=window.setTimeout(()=>setMode('explore'),380);
   }
   dragging=true; lastX=e.clientX; lastY=e.clientY;
   renderer.domElement.setPointerCapture(e.pointerId);
   renderer.domElement.style.cursor='grabbing';
  };
  const onUp=(e:PointerEvent)=>{
   window.clearTimeout(holdTimer);
   dragging=false;
   try{renderer.domElement.releasePointerCapture(e.pointerId);}catch{}
   renderer.domElement.style.cursor=mode==='explore'?'default':'grab';
  };
  const onPointerMove=(e:PointerEvent)=>{
   if(visit.active){
    const r=el.getBoundingClientRect();
    panelLook.x=(e.clientX-r.left)/r.width*2-1;
    panelLook.y=-((e.clientY-r.top)/r.height*2-1);
    return;
   }
   if(mode==='explore'){
    if(!dragging) return;
    const dx=e.clientX-lastX, dy=e.clientY-lastY;
    lastX=e.clientX; lastY=e.clientY;
    camYaw-=dx*0.005;
    camPitch=Math.max(-0.55,Math.min(0.45,camPitch-dy*0.003));
    return;
   }
   if(dragging){
    window.clearTimeout(holdTimer);
    const dx=e.clientX-lastX, dy=e.clientY-lastY;
    lastX=e.clientX; lastY=e.clientY;
    velY=dx*0.006; velX=dy*0.004;
    targetY+=velY; targetX=Math.max(-.5,Math.min(.7,targetX+velX));
    return;
   }
   const r=el.getBoundingClientRect();
   const nx=(e.clientX-(r.left+r.width/2))/r.width;
   const ny=(e.clientY-(r.top+r.height/2))/r.height;
   targetY=nx*0.22; targetX=Math.max(-.28,Math.min(.42,0.14+ny*0.15));
  };

  let wasLocked=false;
  const onLockChange=()=>{
   locked=document.pointerLockElement===renderer.domElement;
   // only when a lock we actually held is released — a refused request also
   // reports a null element, and that must not kick us out of first person
   if(wasLocked&&!locked&&firstPerson){ firstPerson=false; modeCb.current?.(mode); }
   wasLocked=locked;
  };
  const onRawMove=(e:MouseEvent)=>{
   if(!locked||visit.active) return;
   camYaw-=e.movementX*0.0022;
   camPitch=Math.max(-0.55,Math.min(0.45,camPitch-e.movementY*0.0018));
  };
  document.addEventListener('pointerlockchange',onLockChange);
  document.addEventListener('mousemove',onRawMove);

  renderer.domElement.style.cursor='grab';
  const onWheel=(e:WheelEvent)=>{
   if(visit.active){e.preventDefault();panelZoom=Math.max(.52,Math.min(1.1,panelZoom+Math.sign(e.deltaY)*.06));return;}
   if(mode!=='explore') return;
   e.preventDefault();
   camDist=Math.max(1.6,Math.min(8,camDist+Math.sign(e.deltaY)*0.42));
  };
  renderer.domElement.addEventListener('wheel',onWheel,{passive:false});
  renderer.domElement.addEventListener('pointerdown',onDown);
  addEventListener('pointermove',onPointerMove);
  addEventListener('pointerup',onUp);
  addEventListener('keydown',onKeyDown);
  addEventListener('keyup',onKeyUp);

  const oPos=new THREE.Vector3(0,4.6,11.6), oLook=new THREE.Vector3(0,.4,0);
  const ePos=new THREE.Vector3(), eLook=new THREE.Vector3();
  const camPos=new THREE.Vector3(), camLook=new THREE.Vector3();
  let raf=0, last=performance.now(),lastCap=-1;

  const tick=(now:number)=>{
   raf=requestAnimationFrame(tick);
   const dt=Math.min(.064,(now-last)/1000); last=now;

   // time-based progress so the transition can be properly eased and arced,
   // rather than an exponential lerp that only ever approaches its target
   const want=mode==='explore'?1:0;
   if(!visit.active)blendRaw=Math.max(0,Math.min(1,blendRaw+(want?1:-1)*dt/1.35));
   blend=blendRaw*blendRaw*blendRaw*(blendRaw*(blendRaw*6-15)+10);   // smootherstep
   const swoop=Math.sin(blend*Math.PI);                              // 0 -> 1 -> 0

   const wsNow=1+blend*0.55;
   const wasInspecting=visit.active;
   visit.advance(dt,reduced);
   const inspecting=wasInspecting||visit.active;
   panelOpen=visit.active;panelBlend=visit.openness;
   coordinator.update(capRef.current);coordinator.animate(now,panelBlend,reduced);
   siteLinks.forEach(link=>{link.visible=panelBlend<.15;});
   if(inspecting){keys.clear();vel.set(0,0,0);}
   if(mode==='explore'&&!inspecting){
    let f=0,r=0;
    if(keys.has('w')||keys.has('arrowup')) f+=1;
    if(keys.has('s')||keys.has('arrowdown')) f-=1;
    if(keys.has('d')||keys.has('arrowright')) r+=1;
    if(keys.has('a')||keys.has('arrowleft')) r-=1;
    // rotate the input into world space through the CAMERA's yaw
    const fx=Math.sin(camYaw), fz=Math.cos(camYaw);    // forward
    const rx=-Math.cos(camYaw), rz=Math.sin(camYaw);   // right = forward x up
    let mx=fx*f+rx*r, mz=fz*f+rz*r;
    const len=Math.hypot(mx,mz);
    if(len>0){
     mx/=len; mz/=len;
     vel.x+=(mx*3.1-vel.x)*Math.min(1,dt*9);
     vel.z+=(mz*3.1-vel.z)*Math.min(1,dt*9);
     heading=Math.atan2(mx,mz);
     if(!dragging) camYaw+=Math.atan2(Math.sin(heading-camYaw),Math.cos(heading-camYaw))*Math.min(1,dt*1.4);
    } else {
     vel.x+=(0-vel.x)*Math.min(1,dt*8);
     vel.z+=(0-vel.z)*Math.min(1,dt*8);
    }
    doll.position.x+=vel.x*dt; doll.position.z+=vel.z*dt;

    // no outer clamp — the ground reads as endless and you can walk off-site
    for(const hp of houses){
     const dx=doll.position.x-hp.x*wsNow, dz=doll.position.z-hp.z*wsNow;
     const d=Math.hypot(dx,dz);
     if(d<1.02*wsNow&&d>1e-4){ doll.position.x=hp.x*wsNow+dx/d*1.02*wsNow; doll.position.z=hp.z*wsNow+dz/d*1.02*wsNow; }
    }
    const gd=Math.hypot(doll.position.x,doll.position.z);
    if(gd<.95*wsNow&&gd>1e-4){ doll.position.x*=.95*wsNow/gd; doll.position.z*=.95*wsNow/gd; }

    const speed=Math.hypot(vel.x,vel.z);
    walkPhase+=dt*(6+speed*2.4);
    const amt=Math.min(1,speed/2);
    const bob=Math.abs(Math.sin(walkPhase*2))*0.03*amt;
    const sq=1+Math.sin(walkPhase*2+Math.PI/2)*0.07*amt;
    squash.scale.set(1/Math.sqrt(sq),sq,1/Math.sqrt(sq));
    doll.position.y=bob;
    armL.position.z=Math.sin(walkPhase)*0.13*Math.min(1,speed/1.6);
    armR.position.z=-armL.position.z;
    legL.position.z=-armL.position.z*0.8;
    legR.position.z=armL.position.z*0.8;
    // drive the rig's clips from actual ground speed
    if(mixer){
     const want=speed>2.1?actRun:speed>0.25?actWalk:actIdle;
     if(want&&want!==current){
      want.reset().fadeIn(0.22).play();
      if(current) current.fadeOut(0.22);
      current=want;
     }
    }

    // nearest house, and the prompt that goes with it
    let best=-1,bestD=1e9;
    for(let i=0;i<houses.length;i++){
     const d=Math.hypot(doll.position.x-houses[i].x*wsNow,doll.position.z-houses[i].z*wsNow);
     if(d<bestD){ bestD=d; best=i; }
    }
    const dCoord=Math.hypot(doll.position.x,doll.position.z);
    const coordNow=dCoord<1.45*wsNow;
    if(coordNow!==nearCoord&&inside<0&&!panelOpen){
     nearCoord=coordNow;
     houseCb.current?.(coordNow?{index:-1,name:'the coordinator',prompt:true}:null);
    }
    const near=(!coordNow&&bestD<2.05*wsNow)?best:-1;
    if(near!==nearHouse&&inside<0){ nearHouse=near; if(!coordNow)houseCb.current?.(near>=0?{index:near,name:'ABC'[near],prompt:true}:null); }

    let hd=heading-doll.rotation.y;
    hd=Math.atan2(Math.sin(hd),Math.cos(hd));
    doll.rotation.y+=hd*Math.min(1,dt*10);

   } else if(mode==='overview'&&!inspecting){
    if(!dragging){
     velY*=0.94; velX*=0.94;
     targetY+=velY; targetX+=velX;
     if(!reduced) targetY+=0.0016;
    }
   }

   // The explore pose is computed whenever the blend still has ANY weight, not
   // only while mode==='explore'. Recomputing it only in explore mode made the
   // target snap to the overview the instant F was pressed, so the exit had
   // nothing to fly out from — it read as a cut, then a zoom.
   if(blend>0.0001&&!inspecting){
    const cf=Math.cos(camPitch);
    if(firstPerson&&mode==='explore'){
     ePos.set(doll.position.x,.52+doll.position.y*0.35,doll.position.z);
     eLook.set(
      ePos.x+Math.sin(camYaw)*cf,
      ePos.y+Math.sin(camPitch),
      ePos.z+Math.cos(camYaw)*cf
     );
    } else {
     // anchor to the GROUND, not to doll.position.y — that carries the walk-cycle
     // bob, and feeding it into the camera every step reads as the screen shaking
     ePos.set(
      doll.position.x-Math.sin(camYaw)*camDist*cf,
      1.18-Math.sin(camPitch)*(camDist*0.71),
      doll.position.z-Math.cos(camYaw)*camDist*cf
     );
     eLook.set(doll.position.x,.42,doll.position.z);
    }

    // and smooth what is left, frame-rate independently, so foot-plant jitter
    // and collision push-out never reach the view directly
    if(!followInit){ camFollow.copy(ePos); camAim.copy(eLook); followInit=true; }
    const kf=1-Math.pow(0.0009,dt);
    camFollow.lerp(ePos,kf); camAim.lerp(eLook,kf);
    ePos.copy(camFollow); eLook.copy(camAim);
   } else {
    ePos.copy(oPos); eLook.copy(oLook);
   }

   // ghost the shell you are inside and reveal its interior
   insideBlend+=((inside>=0?1:0)-insideBlend)*Math.min(1,dt*5);
   if(Math.abs((inside>=0?1:0)-insideBlend)<0.004) insideBlend=(inside>=0?1:0);
   interiors.forEach((it,i)=>{
    const on=i===inside;
    it.root.visible=on&&insideBlend>0.02;
    it.root.scale.setScalar(0.78*(0.92+insideBlend*0.08));
   });
   for(const m of shellMats){
    const sm=m as THREE.MeshStandardMaterial;
    sm.opacity=1-insideBlend*0.93;
    sm.depthWrite=insideBlend<0.5;
   }
   if(inside>=0){
    // sit outside and above the shell looking down into the floor plan; sitting
    // at the house origin puts the camera inside the building's own geometry
    const hp=houses[inside];
    const len=Math.hypot(hp.x,hp.z)||1;
    const hx=hp.x*wsNow, hz=hp.z*wsNow;
    ePos.set(hx+(hp.x/len)*1.9*wsNow,2.05*wsNow,hz+(hp.z/len)*1.9*wsNow);
    eLook.set(hx,0.38*wsNow,hz);
   }

   curY+=(targetY-curY)*0.08;
   curX+=(targetX-curX)*0.08;
   rig.rotation.y=curY*(1-blend)*(1-panelBlend);
   rig.rotation.x=curX*(1-blend)*(1-panelBlend);

   camPos.copy(oPos).lerp(ePos,blend);
   camLook.copy(oLook).lerp(eLook,blend);
   // arc the flight path and punch the lens mid-move, so it swoops in rather
   // than sliding along a straight line
   camPos.y+=swoop*3.6;
   camPos.x+=Math.sin(blend*Math.PI*2)*0.9;
   camPos.z+=Math.sin(blend*Math.PI)*0.6;
   const fov=38+swoop*26;                       // lens punch through the middle
   if(Math.abs(camera.fov-fov)>0.01){ camera.fov=fov; camera.updateProjectionMatrix(); }
   camera.position.copy(camPos);
   camera.lookAt(camLook);
   camera.rotateZ(Math.sin(blend*Math.PI)*0.11);
   if(inspecting){
    const tan=Math.tan(THREE.MathUtils.degToRad(fov/2));
    const distance=Math.max(1.8/tan,2.07/(tan*camera.aspect))*wsNow*panelZoom;
    const pan=(1-panelZoom)*2.2;
    panelAim.set(panelLook.x*pan*wsNow,(.94+panelLook.y*pan*.45)*wsNow,.18*wsNow);
    panelCamera.set(panelAim.x*.94,panelAim.y+.15*wsNow,distance);
    landing.set(0,(gen.position.y+fin.position.y+.05)*wsNow,0);
    visit.apply(camera,doll,panelCamera,panelAim,landing,reduced);
    if(!visit.active){
     camFollow.copy(savedFollow);camAim.copy(savedAim);followInit=savedFollowInit;firstPerson=savedFirstPerson;
     houseCb.current?.({index:-1,name:'the coordinator',prompt:true});
    }
   }

   // snap the grid to whole cells under the player so it never appears to end
   grid.position.x=Math.round(doll.position.x);
   grid.position.z=Math.round(doll.position.z);
   gridMat.opacity=blend*0.30*(1-panelBlend*.92);
   const ws=1+blend*0.55;               // the site swells as you drop into it
   world.scale.setScalar(ws);
   grid.visible=blend>0.01;
   credits.root.visible=blend>0.05;
   credits.root.scale.setScalar(0.8+blend*0.2);
   doll.visible=blend>0.02&&(inspecting||!(firstPerson&&blend>0.85));
   doll.scale.setScalar(0.55+blend*0.45);

   // current travelling along the wires: scroll the stripe toward the load
   const flow=now*0.00042;
   for(const p of sitePulses){ p.tex.offset.x=-flow; p.mat.opacity=0.22+0.20*Math.sin(now*0.002); }
   for(const it of interiors)
    for(const a of it.appliances) a.pulseTex.offset.x=-flow*1.6;

   // push live allocations into the agent labels when they actually change
   const bs=(budgetRef.current||[]).join(',');
   if(bs!==lastBudgets&&interiors.length){
    lastBudgets=bs;
    const accentNow=cssColor('--accent','#3E7C84');
    const webNow=cssColor('--truss-logo-web','#698F93');
    interiors.forEach((it,i)=>{
     const profile=SITE_MEMBERS[i];
     const b=budgetRef.current?.[i]??profile.floor;
     const got=applyAllocation(it.appliances,profile,b,WANTS[profile.id],accentNow,webNow);
     const drawn=Object.values(got).reduce((x,y)=>x+y,0);
     // stranded watts are real: a binary load whose whole step will not fit is
     // skipped, so the home is allowed more than it can reach
     it.agent.set('agent '+profile.name,
      [b+' W proposed', drawn<b ? drawn+' W projected · '+(b-drawn)+' W stranded'
                               : profile.floor+' W floor']);
    });
   }

   if(capRef.current!==lastCap){lastCap=capRef.current;genLabel.set('coordinator',[lastCap+' W example supply']);}
   genLabel.sprite.visible=blend>0.06&&panelBlend<.1;
   (genLabel.sprite.material as THREE.SpriteMaterial).opacity=Math.min(1,blend*1.4);

   if(mixer) mixer.update(dt);
   renderer.render(scene,camera);
  };
  const resize=()=>{
   const w=Math.max(1,el.clientWidth||420), h=Math.max(1,el.clientHeight||420);
   renderer.setSize(w,h);
   camera.aspect=w/h; camera.updateProjectionMatrix();
  };
  resize();
  tick(performance.now());
  const ro=new ResizeObserver(resize); ro.observe(el);
  const themeWatch=new MutationObserver(paint);
  themeWatch.observe(document.documentElement,{attributes:true,attributeFilter:['data-theme']});

  return ()=>{
   disposed=true;coordinatorTheme.disconnect();coordinator.dispose();genLabel.dispose();
   cancelAnimationFrame(raf); ro.disconnect(); themeWatch.disconnect();
   window.clearTimeout(holdTimer); window.clearTimeout(revealTimer);
   renderer.domElement.removeEventListener('wheel',onWheel);
   renderer.domElement.removeEventListener('pointerdown',onDown);
   removeEventListener('pointermove',onPointerMove);
   removeEventListener('pointerup',onUp);
   removeEventListener('keydown',onKeyDown);
   removeEventListener('keyup',onKeyUp);
   document.removeEventListener('pointerlockchange',onLockChange);
   document.removeEventListener('mousemove',onRawMove);
   if(document.pointerLockElement) document.exitPointerLock?.();
   renderer.dispose();
   scene.traverse((o:THREE.Object3D)=>{const m=o as THREE.Mesh; if(m.geometry) m.geometry.dispose();});
   Object.values(mats).forEach(m=>m.dispose());
   if(renderer.domElement.parentNode) renderer.domElement.parentNode.removeChild(renderer.domElement);
  };
 },[]);

 return <div className="site-scene" ref={host} role="img"
   aria-label={panelVisible?'Inside the coordinator: 3D allocator, validator, reservation gate, MQTT broker, wiring and curved information panels. E or Escape to step out.':'Three homes connected to one shared generator. Press F to walk the site, then E near the coordinator.'}>
   {panelVisible&&<span className="sr-only">Three-home example; no live leases. Supply {cap} W. Proposed budgets: {SITE_MEMBERS.map((m,i)=>`${m.name} ${budgets?.[i]??m.floor} W`).join(', ')}. The reservation gate admits each request against outstanding authority. Lease TTL 6 seconds; recovery hold 6.4 seconds.</span>}
   {loading==='loading'&&<span className="site-scene-status" role="status">Loading the site model…</span>}
   {loading==='fallback'&&<span className="site-scene-fallback" role="status">Some models unavailable · simplified view</span>}
  </div>;
}
