// Brief compositor transitions. No duplicated grids or permanently running loop.
(() => {
 const brand=document.querySelector('.brand-label');
 function syncBrand(){if(brand)brand.style.animationPlayState=document.hidden?'paused':'running'}
 document.addEventListener('visibilitychange',syncBrand);syncBrand();
 const grid=document.querySelector('#grid'),nav=document.querySelector('.nav');
 let transition;
 const originalRender=render;
 render=function(){
  transition?.cancel();originalRender();
  transition=grid.animate([{opacity:.35,transform:'translateY(8px)',filter:lowEffects?'none':'blur(2px)'},{opacity:1,transform:'none',filter:'none'}],{duration:lowEffects?150:240,easing:'cubic-bezier(.2,.8,.2,1)'});
 };
 document.addEventListener('click',e=>{
  const b=e.target.closest('button');if(!b||b.disabled)return;
  b.animate([{transform:'scale(1)'},{transform:'scale(.97)'},{transform:'scale(1)'}],{duration:170,easing:'ease-out'});
 });
 const toast=document.querySelector('#toast');
 let showing=false;
 new MutationObserver(()=>{if(!toast.hidden&&!showing)toast.animate([{opacity:0,translate:'0 8px'},{opacity:1,translate:'0 0'}],{duration:220});showing=!toast.hidden}).observe(toast,{attributes:true,attributeFilter:['hidden']});
 const trail=document.createElement('div');trail.className='mouse-trail';trail.setAttribute('aria-hidden','true');document.body.append(trail);
 let x=0,y=0,tx=0,ty=0,frame=0,last=0,started=false;
 function stop(){cancelAnimationFrame(frame);frame=0;last=0;started=false;trail.style.opacity='0'}
 function tick(now){
  if(document.hidden){stop();return}
  const dt=last?Math.min(now-last,40):16;last=now;
  const dx=tx-x,dy=ty-y,d=Math.hypot(dx,dy),a=1-Math.exp(-dt/40);
  x+=dx*a;y+=dy*a;
  trail.style.transform=`translate3d(${x-45}px,${y-10}px,0) rotate(${Math.atan2(dy,dx)}rad) scaleX(${Math.min(2,.5+d/55)})`;
  trail.style.opacity=String(Math.min(.65,d/45));
  if(d>.4)frame=requestAnimationFrame(tick);else{frame=0;last=0;trail.style.opacity='0'}
 }
 document.addEventListener('pointermove',e=>{
  if(e.pointerType==='touch'||document.querySelector('#intro-frame'))return;
  tx=e.clientX;ty=e.clientY;if(!started){x=tx;y=ty;started=true}
  if(!frame)frame=requestAnimationFrame(tick);
 },{passive:true});
 document.addEventListener('pointerleave',stop);window.addEventListener('blur',stop);
 document.addEventListener('visibilitychange',()=>{if(document.hidden)stop()});
})();
