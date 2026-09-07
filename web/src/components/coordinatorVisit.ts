import {Object3D,PerspectiveCamera,Quaternion,Vector3} from 'three';

const ease=(t:number)=>t*t*t*(t*(t*6-15)+10);

/** One reversible visit, preserving the exact player and camera pose. The
 * enclosure never changes scale; this only moves the camera, lid and player. */
export class CoordinatorVisit {
 phase:'idle'|'entering'|'open'|'exiting'='idle';
 openness=0;
 private elapsed=0;
 private exitOpenness=0;
 private readonly startCamera=new Vector3();
 private readonly startCameraRotation=new Quaternion();
 private readonly startPlayer=new Vector3();
 private readonly startPlayerRotation=new Quaternion();
 private readonly exitCamera=new Vector3();
 private readonly exitCameraRotation=new Quaternion();
 private readonly targetCamera=new PerspectiveCamera();
 private readonly facingCamera=new Quaternion();
 get active(){return this.phase!=='idle';}
 enter(camera:PerspectiveCamera,player:Object3D){
  if(this.active)return;
  this.startCamera.copy(camera.position);this.startCameraRotation.copy(camera.quaternion);
  this.startPlayer.copy(player.position);this.startPlayerRotation.copy(player.quaternion);
  this.elapsed=0;this.openness=0;this.phase='entering';
 }
 leave(camera:PerspectiveCamera){
  if(this.phase==='idle'||this.phase==='exiting')return;
  this.exitCamera.copy(camera.position);this.exitCameraRotation.copy(camera.quaternion);
  this.exitOpenness=this.openness;this.elapsed=0;this.phase='exiting';
 }
 advance(dt:number,reduced=false){
  if(this.phase==='idle'||this.phase==='open')return;
  this.elapsed=Math.min(1,this.elapsed+dt/1.25);
  if(reduced)this.elapsed=1;
  if(this.phase==='entering'){
   this.openness=ease(this.elapsed);
   if(this.elapsed===1)this.phase='open';
  }else{
   this.openness=this.exitOpenness*(1-ease(this.elapsed));
   if(this.elapsed===1)this.phase='idle';
  }
 }
 apply(camera:PerspectiveCamera,player:Object3D,target:Vector3,look:Vector3,landing:Vector3,reduced=false){
  if(this.phase==='idle'){
   camera.position.copy(this.startCamera);camera.quaternion.copy(this.startCameraRotation);
   player.position.copy(this.startPlayer);player.quaternion.copy(this.startPlayerRotation);return;
  }
  this.targetCamera.position.copy(target);this.targetCamera.lookAt(look);
  if(this.phase==='exiting'){
   const t=ease(this.elapsed);
   camera.position.lerpVectors(this.exitCamera,this.startCamera,t);
   camera.quaternion.slerpQuaternions(this.exitCameraRotation,this.startCameraRotation,t);
  }else{
   camera.position.lerpVectors(this.startCamera,target,this.openness);
   camera.quaternion.slerpQuaternions(this.startCameraRotation,this.targetCamera.quaternion,this.openness);
  }
  player.position.lerpVectors(this.startPlayer,landing,this.openness);
  // The same ballistic-looking arc is traversed in reverse on the way down.
  if(!reduced)player.position.y+=Math.sin(Math.PI*this.openness)*.85;
  player.quaternion.slerpQuaternions(this.startPlayerRotation,this.facingCamera,this.openness);
 }
}
