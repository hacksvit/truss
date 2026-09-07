/** Project the rendered camera's forward direction onto the ground. Three's
 * camera looks down local -Z, so Euler yaw alone is not a reliable input basis. */
export function movementOnGround(view:{x:number;z:number},forward:number,right:number,fallbackYaw=Math.PI){
 const length=Math.hypot(view.x,view.z);
 const fx=length>1e-6?view.x/length:Math.sin(fallbackYaw);
 const fz=length>1e-6?view.z/length:Math.cos(fallbackYaw);
 const x=fx*forward-fz*right,z=fz*forward+fx*right;
 const scale=Math.max(1,Math.hypot(x,z));
 return {x:x/scale,z:z/scale};
}
