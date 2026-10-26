(() => {
 const reduce = matchMedia('(prefers-reduced-motion: reduce)');
 const glow = document.createElement('div');
 glow.setAttribute('aria-hidden','true');
 glow.style.cssText='position:fixed;left:0;top:0;width:100px;height:22px;border-radius:50%;pointer-events:none;z-index:10;background:radial-gradient(ellipse,#ffffff18,transparent 70%);filter:blur(9px);opacity:0;transform-origin:center;';
 document.body.append(glow);
 let x=0,y=0,tx=0,ty=0,frame=0,last=0,visible=false;
 function stop(){cancelAnimationFrame(frame);frame=0;last=0;visible=false;glow.style.opacity='0'}
 function tick(now){
  if(document.hidden||reduce.matches||window.SSToolLowEffects){stop();return}
  const dt=last?Math.min(now-last,40):16;last=now;
  const dx=tx-x,dy=ty-y,d=Math.hypot(dx,dy),alpha=1-Math.exp(-dt/45);
  x+=dx*alpha;y+=dy*alpha;
  glow.style.transform=`translate3d(${x-50}px,${y-11}px,0) rotate(${Math.atan2(dy,dx)}rad) scaleX(${Math.min(1.8,.5+d/65)})`;
  glow.style.opacity=String(Math.min(.8,d/40));
  if(d>.25)frame=requestAnimationFrame(tick);else{frame=0;last=0;glow.style.opacity='0'}
 }
 document.addEventListener('pointermove',e=>{
  if(e.pointerType==='touch'||reduce.matches||window.SSToolLowEffects||document.querySelector('#intro'))return;
  tx=e.clientX;ty=e.clientY;if(!visible){x=tx;y=ty;visible=true}
  if(!frame)frame=requestAnimationFrame(tick);
 },{passive:true});
 document.addEventListener('pointerleave',stop);
 document.addEventListener('visibilitychange',()=>{if(document.hidden)stop()});
 window.addEventListener('blur',stop);reduce.addEventListener('change',stop);
})();
