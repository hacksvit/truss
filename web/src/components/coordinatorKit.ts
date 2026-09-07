import * as THREE from 'three';
import {SITE_MEMBERS,WANTS,RESERVE_W,assign,allocate,usefulFor} from './trussModel';

/** Real scene geometry. All labels are textures on the boards or curved glass,
 * so the camera, lighting, depth and website theme belong to one scene. */
export function buildCoordinatorInternals(enclosure:THREE.MeshStandardMaterial){
 const root=new THREE.Group();root.name='coordinator-internals';root.visible=true;
 const solid:THREE.MeshStandardMaterial[]=[];
 const wires:{curve:THREE.CatmullRomCurve3;dot:THREE.Mesh;down:boolean;phase:number}[]=[];
 const textures:THREE.CanvasTexture[]=[];
 const projections:THREE.Object3D[]=[];
 const surfaces:{canvas:HTMLCanvasElement;texture:THREE.CanvasTexture;draw:()=>void}[]=[];
 let cap=1800,disposed=false;
 const token=(name:string,fallback:string)=>getComputedStyle(document.documentElement).getPropertyValue(name).trim()||fallback;
 const colors=()=>({fg:token('--text-primary','#E3EDF5'),muted:token('--text-muted','#8A97AB'),accent:token('--accent','#698F93'),line:token('--border-strong','#2B3648'),bg:token('--bg-dash','#0B1120')});
 function mat(role:'metal'|'board'|'accent'){
  const m=new THREE.MeshStandardMaterial({roughness:role==='metal'?.38:.64,metalness:role==='metal'?.62:.18});m.userData.role=role;solid.push(m);return m;
 }
 const metal=mat('metal'),board=mat('board'),accent=mat('accent');
 function box(w:number,h:number,d:number,x:number,y:number,z:number,m=metal){
  const mesh=new THREE.Mesh(new THREE.BoxGeometry(w,h,d),m);mesh.position.set(x,y,z);root.add(mesh);return mesh;
 }
 // Same 1.15 × 1.25 × .75 enclosure in both states. The front is a
 // hinged lid, not a second case substituted during the camera animation.
 box(1.15,1.25,.03,0,0,-.36,enclosure);
 for(const x of [-.56,.56])box(.03,1.25,.75,x,0,0,enclosure);
 for(const y of [-.61,.61])box(1.15,.03,.75,0,y,0,enclosure);
 const lid=new THREE.Group();lid.position.set(-.545,0,.375);root.add(lid);
 const cover=new THREE.Mesh(new THREE.BoxGeometry(1.09,1.19,.03),enclosure);cover.position.x=.545;lid.add(cover);
 for(const x of [-.55,.55])for(const y of [-.59,.59]){
  const screw=new THREE.Mesh(new THREE.CylinderGeometry(.017,.017,.03,12),accent);screw.rotation.x=Math.PI/2;screw.position.set(x,y,.17);root.add(screw);
 }
 // Standoffs lift the PCB off the backplate; all connectors have actual depth.
 box(1.03,.99,.025,0,.055,.06,board);
 const chips=[{name:'ALLOCATOR',sub:'weighted surplus',x:-.265,y:.36,w:.43},
  {name:'VALIDATOR',sub:'independent check',x:.265,y:.36,w:.43},
  {name:'RESERVATION GATE',sub:'outstanding authority + reserve ≤ cap',x:0,y:.04,w:.89},
  {name:'MQTT / MOSQUITTO',sub:'v5 · :18883 · QoS 1',x:0,y:-.30,w:.89}];
 function textSurface(width:number,height:number,painter:(c:CanvasRenderingContext2D,p:ReturnType<typeof colors>)=>void){
  const canvas=document.createElement('canvas');canvas.width=width;canvas.height=height;
  const texture=new THREE.CanvasTexture(canvas);texture.colorSpace=THREE.SRGBColorSpace;texture.anisotropy=4;textures.push(texture);
  const draw=()=>{const c=canvas.getContext('2d');if(c){c.clearRect(0,0,width,height);painter(c,colors());texture.needsUpdate=true;}};
  surfaces.push({canvas,texture,draw});draw();return texture;
 }
 chips.forEach(chip=>{
  box(chip.w,.21,.055,chip.x,chip.y,.115,metal);
  for(const side of [-1,1])for(let i=0;i<8;i++)box(.018,.032,.012,chip.x+(i-3.5)*chip.w/9,chip.y+side*.12,.11,accent);
  const labelWidth=chip.w<.5?550:950;
  const map=textSurface(labelWidth,220,(c,p)=>{
   c.fillStyle=p.fg;c.textAlign='center';c.font='500 60px "Plex Mono",monospace';c.fillText(chip.name,labelWidth/2,84);
   c.fillStyle=p.muted;c.font='42px "Space Grotesk",sans-serif';c.fillText(chip.sub,labelWidth/2,151);
  });
  const label=new THREE.Mesh(new THREE.PlaneGeometry(chip.w-.025,.18),new THREE.MeshBasicMaterial({map,transparent:true,depthWrite:false}));label.position.set(chip.x,chip.y,.146);root.add(label);
 });
 function wire(points:number[][],down=false,phase=0){
  const curve=new THREE.CatmullRomCurve3(points.map(p=>new THREE.Vector3(...p as [number,number,number])));
  const cable=new THREE.Mesh(new THREE.TubeGeometry(curve,24,.009,6,false),accent);root.add(cable);
  const dot=new THREE.Mesh(new THREE.SphereGeometry(.017,8,8),accent);root.add(dot);wires.push({curve,dot,down,phase});return {cable,dot};
 }
 wire([[-.27,.24,.13],[-.27,.17,.20],[.27,.17,.20],[.27,.24,.13]],false,.1);
 wire([[.42,.25,.13],[.49,.22,.22],[.49,.045,.22],[.45,.045,.13]],false,.5);
 wire([[.16,-.08,.13],[.16,-.16,.24],[.16,-.19,.13]],true,.3);
 wire([[-.16,-.19,.13],[-.16,-.13,.26],[-.46,-.13,.26],[-.5,.35,.25],[-.47,.35,.13]],false,.7);
 for(let i=0;i<3;i++){
  const x=(i-1)*.35;
  box(.20,.10,.13,x,-.58,.18,board);
  for(const dx of [-.045,.045])box(.025,.045,.025,x+dx,-.575,.26,accent);
  wire([[x,-.4,.13],[x,-.47,.25],[x,-.54,.25]],false,i*.25);
  const map=textSurface(256,100,(c,p)=>{c.fillStyle=p.fg;c.font='36px "Plex Mono",monospace';c.textAlign='center';c.fillText('HOME '+'ABC'[i],128,64);});
  const label=new THREE.Mesh(new THREE.PlaneGeometry(.23,.08),new THREE.MeshBasicMaterial({map,transparent:true}));label.position.set(x,-.74,.15);root.add(label);projections.push(label);
 }
 const panelWidth=1.18,panelHeight=1.88;
 function curvedGeometry(){
  const pos:number[]=[],uv:number[]=[],indices:number[]=[];const segments=40,r=1.65;
  for(let row=0;row<2;row++)for(let i=0;i<=segments;i++){
   const u=i/segments,t=(u-.5)*panelWidth/r;
   pos.push(Math.sin(t)*r,(.5-row)*panelHeight,(Math.cos(t)-1)*r);uv.push(u,1-row);
  }
  for(let i=0;i<segments;i++){const j=i+segments+1;indices.push(i,j,i+1,i+1,j,j+1);}
  const g=new THREE.BufferGeometry();g.setAttribute('position',new THREE.Float32BufferAttribute(pos,3));g.setAttribute('uv',new THREE.Float32BufferAttribute(uv,2));g.setIndex(indices);g.computeVertexNormals();return g;
 }
 function panel(side:number){
  const map=textSurface(800,1280,(c,p)=>{
   c.fillStyle=p.bg;c.globalAlpha=.9;c.beginPath();c.roundRect(3,3,794,1274,25);c.fill();c.globalAlpha=1;
   c.strokeStyle=p.accent;c.lineWidth=2;c.stroke();
   const offers=SITE_MEMBERS.map(m=>({id:m.id,floor:m.floor,useful:usefulFor(m,WANTS[m.id])}));
   const plan=allocate(offers,cap,RESERVE_W);
   const rows=SITE_MEMBERS.map(m=>{const budget=plan.budgets[m.id]??m.floor;const draw=Object.values(assign(m,budget,WANTS[m.id])).reduce((s,v)=>s+v,0);return {m,budget,draw,offer:offers.find(o=>o.id===m.id)!};});
   const proposed=plan.feasible?rows.reduce((s,r)=>s+r.budget,0):0;
   const draw=plan.feasible?rows.reduce((s,r)=>s+r.draw,0):0;
   function label(text:string,y:number){c.fillStyle=p.accent;c.font='26px "Plex Mono",monospace';c.textAlign='left';c.fillText(text,46,y);}
   function line(y:number){c.strokeStyle=p.line;c.lineWidth=2;c.beginPath();c.moveTo(46,y);c.lineTo(754,y);c.stroke();}
   function row(name:string,value:string,y:number){c.font='30px "Space Grotesk",sans-serif';c.fillStyle=p.muted;c.textAlign='left';c.fillText(name,46,y);c.fillStyle=p.fg;c.textAlign='right';c.font='30px "Plex Mono",monospace';c.fillText(value,754,y);}
   function paragraph(text:string,y:number){c.font='30px "Space Grotesk",sans-serif';c.fillStyle=p.muted;c.textAlign='left';let current='';for(const word of text.split(' ')){const next=current?current+' '+word:word;if(c.measureText(next).width>702){c.fillText(current,46,y);current=word;y+=44;}else current=next;}c.fillText(current,46,y);}
   if(side<0){
    label('01 / SUPPLY & OFFERS',65);c.fillStyle=p.fg;c.textAlign='left';c.font='72px "Space Grotesk",sans-serif';c.fillText(cap.toLocaleString()+' W',46,166);
    row('Measurement reserve','100 W',245);row('Protected floors · A–C','510 W',302);line(336);
    row(plan.feasible?'Surplus to share':'Floor shortfall',(plan.feasible?cap-610:plan.deficit)+' W',390);
    label('02 / WHAT HOMES ASK FOR',493);row('HOME / FLOOR','USEFUL',558);
    rows.forEach((r,i)=>row(`${r.m.name} / ${r.m.floor} W`,`${r.offer.useful} W`,624+i*62));
    line(793);label('03 / SURPLUS WATER-FILL',855);
    rows.forEach((r,i)=>{const y=921+i*66;row(r.m.name,plan.feasible?'+'+(r.budget-r.m.floor)+' W':'—',y);c.fillStyle=p.line;c.fillRect(120,y-20,370,8);if(plan.feasible){c.fillStyle=p.accent;c.fillRect(120,y-20,370*(r.budget-r.m.floor)/(r.offer.useful-r.m.floor||1),8);}});
    paragraph('Equal weights. Floors first, then share until useful demand is met.',1140);
   }else{
    label('04 / WHERE THE WATTS GO',65);
    c.fillStyle=p.fg;c.font='46px "Space Grotesk",sans-serif';c.textAlign='left';c.fillText(plan.feasible?'Permission ≠ draw':'INFEASIBLE',46,145);
    if(plan.feasible){row('Projected local draw',draw+' W',231);row('Unused permission',(proposed-draw)+' W',291);row('Unassigned capacity',(cap-RESERVE_W-proposed)+' W',351);row('Measurement reserve','100 W',411);line(444);row('Total supply',cap+' W',501);}else paragraph(`Floors + reserve exceed supply by ${plan.deficit} W. No new plan.`,225);
    label('05 / LOCAL OUTCOME PREVIEW',597);row('HOME / PROPOSED','DRAW',662);
    rows.forEach((r,i)=>row(`${r.m.name} / ${plan.feasible?r.budget+' W':'—'}`,plan.feasible?r.draw+' W':'—',729+i*61));
    paragraph(plan.feasible&&proposed>draw?`A leaves ${proposed-draw} W unused. Its 650 W binary heater cannot take a partial step.`:'Local profiles predict these draws. The coordinator receives aggregate offers only.',949);
    line(1060);label('06 / AUTHORITY',1114);row('Lease TTL · from request','6 s',1174);row('Reservation / recovery hold','6.4 s',1233);
   }
  });
  const mesh=new THREE.Mesh(curvedGeometry(),new THREE.MeshBasicMaterial({map,transparent:true,side:THREE.DoubleSide,depthWrite:false}));
  mesh.name=side<0?'coordinator-input-hologram':'coordinator-output-hologram';mesh.position.set(side*1.37,.02,.14);mesh.rotation.y=-side*.16;root.add(mesh);
  // A physical emitter and thin projection lines tie each hologram to the case.
  const emitter=box(.085,.06,.12,side*.62,-.57,.2,accent);
  const beam=wire([[side*.64,-.56,.21],[side*.9,-.62,.20],[side*1.14,-.94,.14]],false,side<0?.2:.6);
  projections.push(emitter,beam.cable,beam.dot);
  return mesh;
 }
 const left=panel(-1),right=panel(1);
 const titleMap=textSurface(1600,160,(c,p)=>{c.textAlign='center';c.fillStyle=p.fg;c.font='42px "Space Grotesk",sans-serif';c.fillText('Inside the coordinator',800,65);c.fillStyle=p.muted;c.font='25px "Plex Mono",monospace';c.fillText('A–C EXAMPLE · MESSAGE WIRING · NO LIVE LEASES',800,119);});
 const title=new THREE.Mesh(new THREE.PlaneGeometry(2.25,.225),new THREE.MeshBasicMaterial({map:titleMap,transparent:true}));title.position.set(0,1.89,.1);root.add(title);
 const noteMap=textSurface(1600,220,(c,p)=>{c.textAlign='center';c.fillStyle=p.muted;c.font='31px "Space Grotesk",sans-serif';c.fillText('A proposal is not a lease. The gate checks existing authority before admission.',800,66);c.fillText('MQTT carries messages. Power feeds homes separately.',800,114);c.font='25px "Plex Mono",monospace';c.fillText('E / ESC TO STEP OUT · SCROLL TO LOOK CLOSER',800,173);});
 const note=new THREE.Mesh(new THREE.PlaneGeometry(2.8,.385),new THREE.MeshBasicMaterial({map:noteMap,transparent:true}));note.position.set(0,-1.23,.12);root.add(note);
 function paint(){if(disposed)return;const p=colors(),light=document.documentElement.dataset.theme==='light';for(const m of solid){const role=m.userData.role;m.color.set(role==='accent'?p.accent:role==='board'?(light?'#c4d8dc':'#14292f'):(light?'#a9b8c4':'#27313e'));m.emissive.set(role==='accent'?p.accent:'#000000');m.emissiveIntensity=role==='accent'?.12:0;}surfaces.forEach(s=>s.draw());}
 paint();document.fonts?.ready.then(()=>{if(!disposed)paint();});
 return {root,left,right,paint,update(value:number){if(cap!==value){cap=value;surfaces.forEach(s=>s.draw());}},
  animate(now:number,open:number,reduced:boolean){lid.rotation.y=-open*Math.PI*1.5;left.visible=right.visible=title.visible=note.visible=open>.03;left.scale.setScalar(.85+.15*open);right.scale.copy(left.scale);for(const node of projections)node.visible=open>.03;for(const w of wires){w.dot.visible=open>.9&&(!w.down||cap>=610);w.dot.position.copy(w.curve.getPointAt(reduced?.5:(now*.00025+w.phase)%1));}},
  dispose(){disposed=true;textures.forEach(t=>t.dispose());root.traverse(o=>{if(o instanceof THREE.Mesh){o.geometry.dispose();const ms=Array.isArray(o.material)?o.material:[o.material];ms.forEach(m=>{if(m!==enclosure)m.dispose();});}});}
 };
}
