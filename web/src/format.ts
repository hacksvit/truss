export const watts=(n:number|null|undefined)=>n==null?'Unknown':`${Math.round(n).toLocaleString()} W`;
export const energy=(n:number)=>`${n.toFixed(2)} Wh`;
export const estimatedRemaining=(remaining:number|null,elapsed:number)=>remaining==null?null:Math.max(0,remaining-elapsed);
export const qualityLabel=(quality:string)=>quality==='fresh'?'Current':quality==='stale'?'Stale — last reading':'Unknown';
