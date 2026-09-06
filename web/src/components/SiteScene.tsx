import {useEffect,useRef} from 'react';
import * as THREE from 'three';

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
export default function SiteScene({onMode}:{onMode?:(m:'overview'|'explore')=>void}){
 const host=useRef<HTMLDivElement>(null);
 const modeCb=useRef(onMode); modeCb.current=onMode;

 useEffect(()=>{
  const el=host.current!;
  const scene=new THREE.Scene();
  const camera=new THREE.PerspectiveCamera(38,1,0.1,100);
  const renderer=new THREE.WebGLRenderer({antialias:true,alpha:true});
  renderer.setPixelRatio(Math.min(devicePixelRatio,2));
  el.appendChild(renderer.domElement);

  const rig=new THREE.Group(); scene.add(rig);

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
  pad.position.y=-.03; rig.add(pad);

  const grid=new THREE.GridHelper(9,18,0x6f8f95,0x44585e);
  const gridMat=grid.material as THREE.Material;
  gridMat.transparent=true; gridMat.opacity=0; grid.position.y=.005; rig.add(grid);

  const gen=new THREE.Group();
  const genBody=new THREE.Mesh(new THREE.BoxGeometry(1.15,1.25,.75),mats.gen);
  gen.add(genBody);
  const fin=new THREE.Mesh(new THREE.BoxGeometry(1.3,.1,.9),mats.gen);
  fin.position.y=.72; gen.add(fin);
  gen.position.y=.62; rig.add(gen);

  const R=2.9;
  const houses:THREE.Vector3[]=[];
  for(let i=0;i<3;i++){
   const a=(i/3)*Math.PI*2 - Math.PI/2;
   const h=new THREE.Group();
   const body=new THREE.Mesh(new THREE.BoxGeometry(1.05,.85,1.05),mats.wall);
   body.position.y=.42; h.add(body);
   const roof=new THREE.Mesh(new THREE.ConeGeometry(.86,.62,4),mats.roof);
   roof.position.y=1.16; roof.rotation.y=Math.PI/4; h.add(roof);
   h.position.set(Math.cos(a)*R,0,Math.sin(a)*R);
   h.rotation.y=-a+Math.PI/2;
   rig.add(h); houses.push(h.position.clone());

   const from=new THREE.Vector3(Math.cos(a)*R,.34,Math.sin(a)*R);
   const to=new THREE.Vector3(0,.55,0);
   const mid=from.clone().lerp(to,.5); mid.y+=.85;
   const tube=new THREE.Mesh(new THREE.TubeGeometry(new THREE.QuadraticBezierCurve3(from,mid,to),28,.045,8,false),mats.link);
   rig.add(tube);
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

  let mode:'overview'|'explore'='overview';
  let firstPerson=false;
  let blend=0, blendRaw=0;
  // The camera has its OWN yaw. Input is transformed through it, so W is always
  // "away from the camera". Deriving heading from raw input instead made W mean
  // world -Z, which reads as walking backwards once the view had swung round.
  let camYaw=Math.PI, camPitch=-0.12;
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
   if(m==='explore'){
    doll.position.set(0,0,1.9); doll.rotation.y=Math.PI; heading=Math.PI; vel.set(0,0,0);
    camYaw=Math.PI; camPitch=-0.12; firstPerson=false;
   }
   modeCb.current?.(m);
  };

  const isTyping=(t:EventTarget|null)=>{
   const n=t as HTMLElement|null;
   return !!n && (n.tagName==='INPUT'||n.tagName==='TEXTAREA'||n.isContentEditable);
  };
  const onKeyDown=(e:KeyboardEvent)=>{
   if(isTyping(e.target)) return;
   const k=e.key.toLowerCase();
   if(k==='f'){ e.preventDefault(); setMode(mode==='explore'?'overview':'explore'); return; }
   if(k==='escape'&&mode==='explore'){ setMode('overview'); return; }
   if(k==='v'&&mode==='explore'){
    e.preventDefault();
    firstPerson=!firstPerson;
    // keydown counts as a user gesture, so the lock request is allowed here
    if(firstPerson) renderer.domElement.requestPointerLock?.();
    else if(document.pointerLockElement) document.exitPointerLock?.();
    modeCb.current?.(mode);
    return;
   }
   if('wasd'.includes(k)||k.startsWith('arrow')){ if(mode==='explore') e.preventDefault(); keys.add(k); }
  };
  const onKeyUp=(e:KeyboardEvent)=>{ keys.delete(e.key.toLowerCase()); };

  const ray=new THREE.Raycaster(); const ptr=new THREE.Vector2();
  let holdTimer=0;
  const onDown=(e:PointerEvent)=>{
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

  const onLockChange=()=>{
   locked=document.pointerLockElement===renderer.domElement;
   // if the user escapes the lock, drop back out of first person so the
   // controls on screen still match what the mouse actually does
   if(!locked&&firstPerson){ firstPerson=false; modeCb.current?.(mode); }
  };
  const onRawMove=(e:MouseEvent)=>{
   if(!locked) return;
   camYaw-=e.movementX*0.0022;
   camPitch=Math.max(-0.55,Math.min(0.45,camPitch-e.movementY*0.0018));
  };
  document.addEventListener('pointerlockchange',onLockChange);
  document.addEventListener('mousemove',onRawMove);

  renderer.domElement.style.cursor='grab';
  renderer.domElement.addEventListener('pointerdown',onDown);
  addEventListener('pointermove',onPointerMove);
  addEventListener('pointerup',onUp);
  addEventListener('keydown',onKeyDown);
  addEventListener('keyup',onKeyUp);

  const oPos=new THREE.Vector3(0,4.6,11.6), oLook=new THREE.Vector3(0,.4,0);
  const ePos=new THREE.Vector3(), eLook=new THREE.Vector3();
  const camPos=new THREE.Vector3(), camLook=new THREE.Vector3();
  let raf=0, last=performance.now();

  const tick=(now:number)=>{
   raf=requestAnimationFrame(tick);
   const dt=Math.min(.064,(now-last)/1000); last=now;

   // time-based progress so the transition can be properly eased and arced,
   // rather than an exponential lerp that only ever approaches its target
   const want=mode==='explore'?1:0;
   blendRaw=Math.max(0,Math.min(1,blendRaw+(want?1:-1)*dt/0.95));
   blend=blendRaw*blendRaw*blendRaw*(blendRaw*(blendRaw*6-15)+10);   // smootherstep
   const swoop=Math.sin(blend*Math.PI);                              // 0 -> 1 -> 0

   if(mode==='explore'){
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

    const rr=Math.hypot(doll.position.x,doll.position.z);
    if(rr>3.9){ doll.position.x*=3.9/rr; doll.position.z*=3.9/rr; }
    for(const hp of houses){
     const dx=doll.position.x-hp.x, dz=doll.position.z-hp.z;
     const d=Math.hypot(dx,dz);
     if(d<.95&&d>1e-4){ doll.position.x=hp.x+dx/d*.95; doll.position.z=hp.z+dz/d*.95; }
    }
    const gd=Math.hypot(doll.position.x,doll.position.z);
    if(gd<.95&&gd>1e-4){ doll.position.x*=.95/gd; doll.position.z*=.95/gd; }

    const speed=Math.hypot(vel.x,vel.z);
    walkPhase+=dt*(6+speed*2.4);
    const amt=Math.min(1,speed/2);
    const bob=Math.abs(Math.sin(walkPhase*2))*0.045*amt;
    const sq=1+Math.sin(walkPhase*2+Math.PI/2)*0.07*amt;
    squash.scale.set(1/Math.sqrt(sq),sq,1/Math.sqrt(sq));
    doll.position.y=bob;
    armL.position.z=Math.sin(walkPhase)*0.13*Math.min(1,speed/1.6);
    armR.position.z=-armL.position.z;
    legL.position.z=-armL.position.z*0.8;
    legR.position.z=armL.position.z*0.8;
    let hd=heading-doll.rotation.y;
    hd=Math.atan2(Math.sin(hd),Math.cos(hd));
    doll.rotation.y+=hd*Math.min(1,dt*10);

    const cf=Math.cos(camPitch);
    if(firstPerson){
     ePos.set(doll.position.x,doll.position.y+.68,doll.position.z);
     eLook.set(
      ePos.x+Math.sin(camYaw)*cf,
      ePos.y+Math.sin(camPitch),
      ePos.z+Math.cos(camYaw)*cf
     );
    } else {
     ePos.set(
      doll.position.x-Math.sin(camYaw)*3.1*cf,
      doll.position.y+1.55-Math.sin(camPitch)*2.2,
      doll.position.z-Math.cos(camYaw)*3.1*cf
     );
     eLook.set(doll.position.x,doll.position.y+.55,doll.position.z);
    }
   } else {
    if(!dragging){
     velY*=0.94; velX*=0.94;
     targetY+=velY; targetX+=velX;
     if(!reduced) targetY+=0.0016;
    }
    ePos.copy(oPos); eLook.copy(oLook);
   }

   curY+=(targetY-curY)*0.08;
   curX+=(targetX-curX)*0.08;
   rig.rotation.y=curY*(1-blend);
   rig.rotation.x=curX*(1-blend);

   camPos.copy(oPos).lerp(ePos,blend);
   camLook.copy(oLook).lerp(eLook,blend);
   // arc the flight path and punch the lens mid-move, so it swoops in rather
   // than sliding along a straight line
   camPos.y+=swoop*2.3;
   camPos.x+=Math.sin(blend*Math.PI*2)*0.5;
   const fov=38+swoop*16;
   if(Math.abs(camera.fov-fov)>0.01){ camera.fov=fov; camera.updateProjectionMatrix(); }
   camera.position.copy(camPos);
   camera.lookAt(camLook);
   camera.rotateZ(Math.sin(blend*Math.PI)*0.05);

   gridMat.opacity=blend*0.34;
   grid.visible=blend>0.01;
   doll.visible=blend>0.02&&!(firstPerson&&blend>0.85);
   doll.scale.setScalar(0.55+blend*0.45);

   renderer.render(scene,camera);
  };
  tick(performance.now());

  const resize=()=>{
   const w=Math.max(1,el.clientWidth||420), h=Math.max(1,el.clientHeight||420);
   renderer.setSize(w,h);
   camera.aspect=w/h; camera.updateProjectionMatrix();
  };
  resize();
  const ro=new ResizeObserver(resize); ro.observe(el);
  const themeWatch=new MutationObserver(paint);
  themeWatch.observe(document.documentElement,{attributes:true,attributeFilter:['data-theme']});

  return ()=>{
   cancelAnimationFrame(raf); ro.disconnect(); themeWatch.disconnect();
   window.clearTimeout(holdTimer);
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
   aria-label="Three homes connected to one shared generator. Press F to walk the site."/>;
}
