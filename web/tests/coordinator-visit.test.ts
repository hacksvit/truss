import {describe,it,expect} from 'vitest';
import {Object3D,PerspectiveCamera,Vector3} from 'three';
import {CoordinatorVisit} from '../src/components/coordinatorVisit';
function setup(){
 const camera=new PerspectiveCamera(),player=new Object3D(),visit=new CoordinatorVisit();
 camera.position.set(2,1.8,4);camera.lookAt(.5,.4,.1);
 player.position.set(.3,.02,2);player.rotation.y=2.4;
 const original={camera:camera.position.clone(),rotation:camera.quaternion.clone(),player:player.position.clone(),playerRotation:player.quaternion.clone()};
 const target=new Vector3(0,2,6),look=new Vector3(0,1,0),landing=new Vector3(0,2.1545,0);
 const step=(dt:number,reduced=false)=>{visit.advance(dt,reduced);visit.apply(camera,player,target,look,landing,reduced);};
 return {camera,player,visit,original,target,look,landing,step};
}
describe('coordinator visit',()=>{
 it('jumps above the direct path, lands on the roof, and keeps the character visible at its full scale',()=>{
  const s=setup();s.visit.enter(s.camera,s.player);s.step(.625);
  expect(s.visit.openness).toBe(.5);
  expect(s.player.position.y).toBeGreaterThan((s.original.player.y+s.landing.y)/2+.8);
  expect(s.player.scale.toArray()).toEqual([1,1,1]);
  s.step(.625);expect(s.visit.phase).toBe('open');
  expect(s.player.position.distanceTo(s.landing)).toBeLessThan(1e-10);
 });
 it('returns to the exact original camera and character pose after inspecting with a different camera position',()=>{
  const s=setup();s.visit.enter(s.camera,s.player);s.step(1.25);
  s.camera.position.set(1.3,3,3.7);s.camera.lookAt(-1,1,0);
  const exit=s.camera.position.clone();s.visit.leave(s.camera);s.step(0);
  expect(s.camera.position.toArray()).toEqual(exit.toArray());
  s.step(.625);expect(s.player.position.y).toBeGreaterThan(s.landing.y/2);
  s.step(.625);
  expect(s.visit.phase).toBe('idle');
  expect(s.camera.position.toArray()).toEqual(s.original.camera.toArray());
  expect(s.camera.quaternion.toArray()).toEqual(s.original.rotation.toArray());
  expect(s.player.position.toArray()).toEqual(s.original.player.toArray());
  expect(s.player.quaternion.toArray()).toEqual(s.original.playerRotation.toArray());
 });
 it('reverses a partially completed opening without snapping either the camera or the jump',()=>{
  const s=setup();s.visit.enter(s.camera,s.player);s.step(.4);
  const camera=s.camera.position.clone(),player=s.player.position.clone();
  s.visit.leave(s.camera);s.step(0);
  expect(s.camera.position.distanceTo(camera)).toBeLessThan(1e-10);
  expect(s.player.position.distanceTo(player)).toBeLessThan(1e-10);
  s.step(1.25);expect(s.player.position.toArray()).toEqual(s.original.player.toArray());
 });
 it('honors reduced motion and ignores duplicate entry requests',()=>{
  const s=setup();s.visit.enter(s.camera,s.player);s.step(.1,true);
  expect(s.visit.phase).toBe('open');expect(s.player.position.toArray()).toEqual(s.landing.toArray());
  s.visit.enter(s.camera,s.player);s.visit.leave(s.camera);s.step(.1,true);
  expect(s.camera.position.toArray()).toEqual(s.original.camera.toArray());
 });
});
