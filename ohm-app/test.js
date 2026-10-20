const assert=require('node:assert/strict'),fs=require('node:fs'),{solve}=require('./solver.js');
const edge=(a,b,r,ref='R')=>({a,b,r,ref});
const near=(a,b)=>assert.ok(Math.abs(a-b)<Math.max(1e-6,Math.abs(b)*1e-8),a+' != '+b);
near(solve([edge('a','b',100),edge('b','c',200)],'a','c').resistance,300);
near(solve([edge('a','b',100),edge('a','b',100)],'a','b').resistance,50);
near(solve([edge('a','x',0),edge('x','b',100)],'a','b').resistance,100);
near(solve([],'a','a').resistance,0);assert.equal(solve([],'a','b').resistance,Infinity);
near(solve([edge('a','b',10),edge('c','d',2)],'a','b').resistance,10);
const bs=JSON.parse(fs.readFileSync(__dirname+'/data/boards.json'));
assert.equal(bs.length,10);
const dc3=bs.find(b=>b.name==='DC3');
const pin=n=>dc3.pads.find(p=>p.ref==='U1'&&p.pin===n).net;
near(solve(dc3.edges,pin('6'),pin('7')).resistance,100000);
const mb=bs.find(b=>b.name==='Motherboard');
near(solve(mb.edges,'SCORE_6','SCORE_DIV_6').resistance,220000);
near(solve(mb.edges,'SCORE_DIV_6','GND').resistance,1/(1/22000+1/(22000+44000/9)));
for(const [name,n] of [['DC1A',191],['DC1B',230],['DC1C',181],['DC1D',141]])assert.equal(bs.find(b=>b.name===name).edges.length,n);
for(const b of bs){if(b.name!=='DC1 universal')assert.deepEqual(b.warnings,[]);for(const p of b.pads)assert.ok(Number.isFinite(p.x)&&Number.isFinite(p.y));}
console.log('network and source-board assertions passed');

