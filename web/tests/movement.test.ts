import {describe,it,expect} from 'vitest';
import {PerspectiveCamera,Vector3} from 'three';
import {movementOnGround} from '../src/components/movement';
describe('camera-relative ground movement',()=>{
 it.each([0,.7,Math.PI,-2.4,5.8])('keeps forward/back and strafe correct after a visit at heading %s',yaw=>{
  const camera=new PerspectiveCamera();camera.position.set(2,3,4);
  camera.lookAt(2+Math.sin(yaw),2.8,4+Math.cos(yaw));
  const view=camera.getWorldDirection(new Vector3());
  const f=movementOnGround(view,1,0),b=movementOnGround(view,-1,0),r=movementOnGround(view,0,1);
  expect(f.x*view.x+f.z*view.z).toBeGreaterThan(.9);
  expect(b.x*view.x+b.z*view.z).toBeLessThan(-.9);
  expect(f.x*r.x+f.z*r.z).toBeCloseTo(0);
  expect(r.x).toBeCloseTo(-Math.cos(yaw));
  expect(r.z).toBeCloseTo(Math.sin(yaw));
  expect(Math.hypot(...Object.values(movementOnGround(view,1,1)))).toBeCloseTo(1);
 });
});
