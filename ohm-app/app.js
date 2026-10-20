'use strict';
const $=id=>document.getElementById(id),svg=$('pcb'),NS='http://www.w3.org/2000/svg';
let boards=[],board,side='F',probes=[],view,drag;
function el(tag,attrs,text){const e=document.createElementNS(NS,tag);for(const [k,v] of Object.entries(attrs))e.setAttribute(k,v);if(text)e.textContent=text;return e;}
function fmt(r){return !Number.isFinite(r)?'Open (∞)':r>=1e6?(r/1e6).toPrecision(5)+' MΩ':r>=1e3?(r/1e3).toPrecision(5)+' kΩ':r.toPrecision(5)+' Ω';}
function visible(p){return p.layers.includes(side+'.Cu')||p.layers.includes('*.Cu')||p.layers.includes('F&B.Cu');}
function X(x){return side==='B'?board.bounds[0]+board.bounds[2]-x:x;}
function setView(){svg.setAttribute('viewBox',view.join(' '));}
function fit(){const [x,y,x2,y2]=board.bounds;view=[x,y,x2-x,y2-y];setView();}
function pick(p){if(!p.net)return;if(probes.length===2)probes=[];probes.push(p);update();draw();}
function draw(){
 svg.replaceChildren();
 for(const o of board.outlines){
  if(o.kind==='gr_line')svg.append(el('line',{x1:X(o.a[0]),y1:o.a[1],x2:X(o.b[0]),y2:o.b[1],stroke:'#92ab91','stroke-width':.3}));
  if(o.kind==='gr_rect')svg.append(el('rect',{x:Math.min(X(o.a[0]),X(o.b[0])),y:Math.min(o.a[1],o.b[1]),width:Math.abs(o.b[0]-o.a[0]),height:Math.abs(o.b[1]-o.a[1]),stroke:'#92ab91','stroke-width':.3,fill:'none'}));
 }
 for(const t of board.tracks){
  if(t.layer!==side+'.Cu')continue;
  const p={net:t.net,ref:'track',pin:''},n=el('line',{x1:X(t.a[0]),y1:t.a[1],x2:X(t.b[0]),y2:t.b[1],stroke:color(t.net,'#42765d'),'stroke-width':Math.max(t.w,.22),class:'copper'});
  n.append(el('title',{},t.net));n.addEventListener('click',e=>{e.stopPropagation();pick(p);});svg.append(n);
 }
 for(const p of board.pads){
  if(!visible(p))continue;
  const a={fill:color(p.net,'#ccb779'),stroke:'#dbc58a','stroke-width':.08,class:'copper',transform:'translate('+X(p.x)+' '+p.y+') rotate('+(side==='B'?p.angle:-p.angle)+')'};
  const n=p.shape==='circle'?el('ellipse',{...a,rx:p.w/2,ry:p.h/2}):el('rect',{...a,x:-p.w/2,y:-p.h/2,width:p.w,height:p.h,rx:p.shape==='roundrect'?.15:0});
  n.append(el('title',{},p.ref+' pin '+p.pin+' · '+(p.net||'unconnected')));
  n.addEventListener('click',e=>{e.stopPropagation();pick(p);});svg.append(n);
 }
 if($('refs').checked)for(const l of board.labels)if(l.layer===side+'.SilkS')svg.append(el('text',{x:X(l.x),y:l.y,fill:'#e7edcf','font-size':.8,'text-anchor':'middle','pointer-events':'none'},l.text));
 for(let i=0;i<probes.length;i++){const p=probes[i];if(p.x===undefined)continue;
 svg.append(el('circle',{cx:X(p.x),cy:p.y,r:1.4,fill:'none',stroke:i?'#8fbfff':'#ff916e','stroke-width':.3,'pointer-events':'none'}));
 svg.append(el('text',{x:X(p.x)+1.6,y:p.y,fill:i?'#8fbfff':'#ff916e','font-size':2,'pointer-events':'none'},i?'B':'A'));}
}
function color(net,fallback){return probes[1]?.net===net?'#8fbfff':probes[0]?.net===net?'#ff916e':fallback;}
function update(){
 $('paths').replaceChildren();
 for(let i=0;i<2;i++){const p=probes[i];$(i?'b':'a').value=p?String(board.pads.indexOf(p)):'';}
 $('nets').textContent=probes.map((p,i)=>(i?'B':'A')+' · '+p.ref+' '+p.pin+' · '+p.net).join('\n');
 if(probes.length<2){$('result').textContent='Place probe '+(probes.length?'B':'A');return;}
 try{const r=Ohm.solve(board.edges,probes[0].net,probes[1].net);$('result').textContent=fmt(r.resistance);
 for(const e of r.currents.slice(0,18)){const d=document.createElement('div');d.textContent=e.ref+' · '+fmt(e.r)+' · '+(100*e.current).toFixed(2)+'% of test current';$('paths').append(d);}
 }catch(e){$('result').textContent='Solver error';$('notice').textContent=e.message;}
}
function load(){
 board=boards[Number($('board').value)];probes=[];
 for(const id of ['a','b']){const s=$(id);s.replaceChildren(new Option('Choose a pad',''));
 board.pads.forEach((p,i)=>{if(p.net)s.add(new Option(p.ref+' '+p.pin+' · '+p.net,String(i)));});}
 $('notice').textContent=board.name==='DC1 universal'?'Universal layout is unpopulated. Select DC1A/B/C/D for fitted resistors.':board.warnings.length?board.warnings.join('; '):'';
 $('source').textContent=board.source+' · '+board.edges.length+' fitted resistors · SHA256 '+board.sha256;
 fit();update();draw();
}
for(const [id,s] of [['front','F'],['back','B']])$(id).onclick=()=>{side=s;$('front').setAttribute('aria-pressed',s==='F');$('back').setAttribute('aria-pressed',s==='B');draw();};
$('board').onchange=load;$('refs').onchange=draw;$('fit').onclick=fit;$('reset').onclick=()=>{probes=[];update();draw();};
for(const [id,i] of [['a',0],['b',1]])$(id).onchange=()=>{const v=$(id).value;if(v===''){probes=[];}else{if(i===1&&!probes[0]){$('notice').textContent='Choose A first.';return;}probes[i]=board.pads[Number(v)];}update();draw();};
svg.addEventListener('wheel',e=>{e.preventDefault();const scale=e.deltaY>0?1.15:1/1.15,box=svg.getBoundingClientRect(),fx=(e.clientX-box.left)/box.width,fy=(e.clientY-box.top)/box.height;view[0]+=view[2]*fx*(1-scale);view[1]+=view[3]*fy*(1-scale);view[2]*=scale;view[3]*=scale;setView();},{passive:false});
svg.addEventListener('pointerdown',e=>{if(e.target.closest('.copper'))return;drag={x:e.clientX,y:e.clientY,v:[...view]};svg.setPointerCapture(e.pointerId);});
svg.addEventListener('pointermove',e=>{if(!drag)return;const b=svg.getBoundingClientRect(),scale=Math.max(view[2]/b.width,view[3]/b.height);view[0]=drag.v[0]-(e.clientX-drag.x)*scale;view[1]=drag.v[1]-(e.clientY-drag.y)*scale;setView();});
svg.addEventListener('pointerup',()=>drag=null);svg.addEventListener('pointercancel',()=>drag=null);
fetch('data/boards.json').then(r=>{if(!r.ok)throw Error('Board data unavailable');return r.json();}).then(data=>{boards=data;boards.forEach((b,i)=>$('board').add(new Option(b.name,i)));$('board').value=String(boards.findIndex(b=>b.name==='DC3'));load();}).catch(e=>$('result').textContent=e.message);

