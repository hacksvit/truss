import {useEffect,useRef} from 'react';

/** Headline that resolves from a heavily pixelated buffer into real type.
 *
 *  Visibility: the text is visible by DEFAULT and is only hidden from inside a
 *  frame that has actually painted over it, with an unconditional watchdog that
 *  restores it if the loop ever stalls. Every failure path shows plain type.
 *
 *  Fidelity: the glyphs are rasterised ONCE into a source canvas, then each
 *  frame downscales that source by an INTEGER block size and blows it back up
 *  with smoothing off. Re-rasterising per frame at a fractional scale makes the
 *  text shimmer; integer blocks land on whole pixels and hold still. Canvas 2D
 *  also ignores CSS letter-spacing, so it is copied across explicitly or the
 *  canvas text draws wider than the real text and the swap looks like a shrink. */
export default function PixelText({lines,className=''}:{lines:string[];className?:string}){
 const cv=useRef<HTMLCanvasElement>(null);
 const h=useRef<HTMLHeadingElement>(null);

 useEffect(()=>{
  const canvas=cv.current, head=h.current;
  if(!canvas||!head) return;

  let cancelled=false, raf=0, started=false, tries=0, watchdog=0;
  const reveal=()=>{
   window.clearTimeout(watchdog);
   head.style.opacity='1';
   canvas.style.display='none';
  };

  const reduced=typeof matchMedia==='function'&&matchMedia('(prefers-reduced-motion: reduce)').matches;
  const hidden=typeof document!=='undefined'&&document.visibilityState==='hidden';
  if(reduced||hidden||typeof requestAnimationFrame!=='function'){ reveal(); return; }

  const bail=window.setTimeout(()=>{ if(!started&&!cancelled) reveal(); },700);

  const begin=()=>{
   if(cancelled||started) return;
   const rect=head.getBoundingClientRect();
   const w=Math.ceil(rect.width), ht=Math.ceil(rect.height);
   if(w<8||ht<8){ if(++tries>30){ reveal(); return; } raf=requestAnimationFrame(begin); return; }

   const ctx=canvas.getContext('2d');
   if(!ctx){ reveal(); return; }

   const cs=getComputedStyle(head);
   const font=cs.fontWeight+' '+cs.fontSize+'/'+cs.lineHeight+' '+cs.fontFamily;
   const lineH=parseFloat(cs.lineHeight)||parseFloat(cs.fontSize)*1.05;
   const dpr=Math.min(devicePixelRatio||1,2);

   // ---- rasterise the glyphs once, at full resolution ----
   const src=document.createElement('canvas');
   src.width=Math.max(2,Math.round(w*dpr));
   src.height=Math.max(2,Math.round(ht*dpr));
   const sctx=src.getContext('2d');
   if(!sctx){ reveal(); return; }
   sctx.setTransform(dpr,0,0,dpr,0,0);
   sctx.font=font;
   const ls=cs.letterSpacing;
   if('letterSpacing' in sctx && ls && ls!=='normal'){
    (sctx as CanvasRenderingContext2D&{letterSpacing:string}).letterSpacing=ls;
   }
   // Each line is its own <span> and may carry its own colour (line 2 is muted);
   // using the h1 colour for both makes line 2 change hue at the handover.
   const spans=[...head.querySelectorAll('span')];
   const colours=lines.map((_,i)=>spans[i]?getComputedStyle(spans[i]).color:cs.color);

   // Real text sits on the BASELINE inside its line box, not at the top of it.
   // Drawing from the top leaves the canvas a few px out, which reads as the
   // text nudging into place when the canvas hands over. Use real metrics.
   const m=sctx.measureText('Hxg');
   const fs=parseFloat(cs.fontSize)||16;
   const asc=m.fontBoundingBoxAscent??fs*0.8;
   const desc=m.fontBoundingBoxDescent??fs*0.2;
   const halfLead=(lineH-(asc+desc))/2;
   sctx.textBaseline='alphabetic';
   lines.forEach((ln,i)=>{
    sctx.fillStyle=colours[i];
    sctx.fillText(ln,0,i*lineH+halfLead+asc);
   });

   canvas.width=Math.round(w*dpr); canvas.height=Math.round(ht*dpr);
   canvas.style.width=w+'px'; canvas.style.height=ht+'px';
   canvas.style.display='block';

   const buf=document.createElement('canvas');
   const bctx=buf.getContext('2d');
   if(!bctx){ reveal(); return; }

   started=true;
   window.clearTimeout(bail);

   const t0=performance.now();
   const DUR=1150, MAX_BLOCK=44;
   watchdog=window.setTimeout(()=>{ if(!cancelled) reveal(); },DUR+1200);

   let lastBlock=-1;
   const tick=(now:number)=>{
    if(cancelled) return;
    head.style.opacity='0';                       // only ever from a painting frame

    const t=Math.min(1,(now-t0)/DUR);
    const e=1-Math.pow(1-t,3);
    // integer block size, large -> 1. Whole pixels, so nothing shimmers.
    const block=Math.max(1,Math.round(MAX_BLOCK*Math.pow(1-e,1.6)));

    if(block!==lastBlock){
     lastBlock=block;
     const bw=Math.max(1,Math.ceil(canvas.width/block));
     const bh=Math.max(1,Math.ceil(canvas.height/block));
     buf.width=bw; buf.height=bh;
     bctx.imageSmoothingEnabled=true;             // average down, then hard up
     bctx.clearRect(0,0,bw,bh);
     bctx.drawImage(src,0,0,src.width,src.height,0,0,bw,bh);
    }

    ctx.setTransform(1,0,0,1,0,0);
    ctx.clearRect(0,0,canvas.width,canvas.height);
    ctx.imageSmoothingEnabled=false;
    ctx.drawImage(buf,0,0,buf.width,buf.height,0,0,buf.width*block,buf.height*block);

    if(t>=1){ reveal(); return; }
    raf=requestAnimationFrame(tick);
   };
   raf=requestAnimationFrame(tick);
  };

  const fonts=(document as Document&{fonts?:{ready:Promise<unknown>}}).fonts;
  if(fonts&&fonts.ready) Promise.race([fonts.ready,new Promise(r=>setTimeout(r,500))]).then(begin,begin);
  else begin();

  const onVis=()=>{ if(document.visibilityState==='hidden') reveal(); };
  document.addEventListener('visibilitychange',onVis);

  return ()=>{
   cancelled=true;
   window.clearTimeout(bail); window.clearTimeout(watchdog);
   cancelAnimationFrame(raf);
   document.removeEventListener('visibilitychange',onVis);
   head.style.opacity='1';        // never unmount leaving the heading hidden
  };
 },[lines.join('\n')]);

 return <div className={'pixel-text '+className}>
  <h1 ref={h}>{lines.map((l,i)=><span key={i}>{l}<br/></span>)}</h1>
  <canvas ref={cv} aria-hidden="true"/>
 </div>;
}
