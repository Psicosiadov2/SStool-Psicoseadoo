'use strict';
const nav=document.querySelector('.nav'), grid=document.querySelector('#grid');
let cooldownTimer=0;
function scheduleCooldown(){if(cooldownTimer||document.hidden)return;cooldownTimer=setTimeout(()=>{cooldownTimer=0;updateButtons();if([...states.values()].some(s=>s.busy||s.until>Date.now()))scheduleCooldown()},100)}
document.addEventListener("visibilitychange",()=>{if(document.hidden){clearTimeout(cooldownTimer);cooldownTimer=0}else{updateButtons();scheduleCooldown()}});
let language='en', selected=catalogue[0].id, hideTimer;
const states=new Map(), cardCache=new Map();
const reducedMotion=matchMedia("(prefers-reduced-motion:reduce)");
let categoryAnimation;
const label=(en,es)=>language==='es'?es:en;
function toast(message){document.querySelector('#toast-text').textContent=message;document.querySelector('#toast').hidden=false;clearTimeout(hideTimer);hideTimer=setTimeout(()=>document.querySelector('#toast').hidden=true,6000)}
function render(){
 if(!nav.children.length){
 for(const c of catalogue){const b=document.createElement('button');b.className='tab';b.textContent=c.labels[language];b.setAttribute('role','tab');b.dataset.category=c.id;b.setAttribute('aria-selected',c.id===selected);b.onclick=()=>{if(selected===c.id)return;selected=c.id;render()};nav.append(b)}
 }
 for(const b of nav.children){const c=catalogue.find(c=>c.id===b.dataset.category);b.textContent=c.labels[language];b.setAttribute('aria-selected',c.id===selected)}
 const c=catalogue.find(c=>c.id===selected);document.querySelector('#heading').textContent=c.labels[language];
 const tools=c.tools;
 grid.replaceChildren();
 const fragment=document.createDocumentFragment();
 const cacheKey=selected+':'+language;
 if(!cardCache.has(cacheKey))cardCache.set(cacheKey,tools.map(t=>{
  const b=document.createElement('button');b.className='card';b.dataset.id=t.id;
  const title=document.createElement('strong');title.textContent=t.name;
  const desc=document.createElement('span');desc.textContent=t.descriptions[language];
  const cool=document.createElement('span');cool.className='cooldown';b.append(title,desc,cool);
  b.onclick=()=>{if(!reducedMotion.matches)b.animate([{scale:'1'},{scale:'.98'},{scale:'1'}],{duration:200,easing:'ease-out'});launch(t)};return b;
 }));
 fragment.append(...cardCache.get(cacheKey));
 grid.append(fragment);
 if(!tools.length){const p=document.createElement('p');p.className='empty';p.textContent=label('No tools found.','No se encontraron herramientas.');grid.append(p)}
 categoryAnimation?.cancel();
 if(!reducedMotion.matches)categoryAnimation=grid.animate([{opacity:.35,transform:'translateY(7px)'},{opacity:1,transform:'none'}],{duration:220,easing:'cubic-bezier(.2,.75,.25,1)'});
 updateButtons();
}
function updateButtons(){for(const b of grid.querySelectorAll('.card')){const s=states.get(b.dataset.id);const remaining=s?Math.max(0,(s.until-Date.now())/1000):0;b.disabled=!!(s&&(s.busy||remaining));const cool=b.querySelector('.cooldown'),text=remaining?remaining.toFixed(1)+'s':s?.busy?label('Opening…','Abriendo…'):'';if(cool.textContent!==text)cool.textContent=text}}
async function launch(t){
 if(!window.pywebview?.api){toast(label('Preview only: run main.py to launch tools.','Solo vista previa: ejecuta main.py para abrir herramientas.'));return}
 states.set(t.id,{busy:true,until:Date.now()+5000});updateButtons();scheduleCooldown();
 document.querySelector('.progress-row').hidden=true;toast(label('Preparing ','Preparando ')+t.name+'…');
 try{const r=await window.pywebview.api.launch(t.id);if(!r.accepted){states.delete(t.id);toast(r.error)}}catch(e){states.delete(t.id);toast(String(e))}updateButtons();
}
window.SSTool={receive(p){
 if(p.kind==='status'){document.querySelector('.progress-row').hidden=true;toast(p.message)}
 if(p.kind==='progress'){toast(label('Downloading ','Descargando ')+p.name);const row=document.querySelector('.progress-row');row.hidden=false;const bar=document.querySelector('#progress');if(p.percent===null)bar.removeAttribute('value');else bar.value=p.percent;document.querySelector('#percent').textContent=p.percent===null?'…':Math.round(p.percent)+'%'}
 if(p.kind==='done'){const s=states.get(p.id);if(s)s.busy=false;updateButtons();document.querySelector('.progress-row').hidden=true}
}};
document.querySelector('#language').onclick=()=>{language=language==='en'?'es':'en';document.documentElement.lang=language;render()};
document.querySelectorAll('[data-window]').forEach(b=>b.onclick=async()=>{if(window.pywebview?.api)await window.pywebview.api.window_control(b.dataset.window);else toast('Desktop controls are available inside the app.')});
document.querySelectorAll('[data-link]').forEach(b=>b.onclick=()=>window.pywebview?.api.open_link(b.dataset.link));
document.querySelector('.brand').ondblclick=()=>window.pywebview?.api.window_control('maximize');
document.addEventListener('keydown',e=>{if(e.key==='F11'){e.preventDefault();window.pywebview?.api.window_control('fullscreen')}});
document.addEventListener('keydown',e=>{if(e.key==='Escape')window.pywebview?.api.window_control('exit-fullscreen')});
let hoverFrame=0,hoverPoint;
grid.addEventListener('pointermove',e=>{hoverPoint={card:e.target.closest('.card'),x:e.clientX,y:e.clientY};if(hoverFrame)return;hoverFrame=requestAnimationFrame(()=>{hoverFrame=0;const {card,x,y}=hoverPoint;if(!card?.isConnected)return;const r=card.getBoundingClientRect();card.style.setProperty('--mx',(x-r.left)/r.width*100+'%');card.style.setProperty('--my',(y-r.top)/r.height*100+'%')})});
render();
const introFrame=document.querySelector('#intro');
function startIntroTimer(){
 setTimeout(()=>{
  const app=document.querySelector('.window');app.classList.remove('waiting');
  if(!matchMedia('(prefers-reduced-motion:reduce)').matches){
   app.animate([{opacity:0},{opacity:1}],{duration:850,easing:'ease-out'});
   document.querySelector('#panel').animate([{opacity:0,transform:'translateY(10px)'},{opacity:1,transform:'none'}],{duration:700,delay:150,easing:'cubic-bezier(.2,.7,.2,1)',fill:'backwards'});
  }
  introFrame.contentWindow.SSToolIntro?.finish();
  setTimeout(()=>introFrame.remove(),450);
 },4500);
}
if(introFrame.contentDocument?.readyState==='complete'&&introFrame.contentWindow.SSToolIntro)startIntroTimer();
else introFrame.addEventListener('load',startIntroTimer,{once:true});
