/* Grounded resistor Laplacian with exact zero-ohm contraction. */
(function(root){
function solve(edges,a,b){
 const parent=new Map();
 function find(x){if(!parent.has(x))parent.set(x,x);if(parent.get(x)!==x)parent.set(x,find(parent.get(x)));return parent.get(x);}
 for(const e of edges)if(e.r===0)parent.set(find(e.a),find(e.b));
 a=find(a);b=find(b);
 if(a===b)return {resistance:0,currents:[]};
 const es=edges.filter(e=>e.r>0).map(e=>({...e,a:find(e.a),b:find(e.b)}));
 const adj=new Map();
 for(const e of es){for(const [x,y] of [[e.a,e.b],[e.b,e.a]]){if(!adj.has(x))adj.set(x,[]);adj.get(x).push(y);}}
 const seen=new Set([a]),q=[a];
 for(let i=0;i<q.length;i++)for(const n of adj.get(q[i])||[])if(!seen.has(n)){seen.add(n);q.push(n);}
 if(!seen.has(b))return {resistance:Infinity,currents:[]};
 const ns=q.filter(n=>n!==b),idx=new Map(ns.map((n,i)=>[n,i])),N=ns.length;
 const M=Array.from({length:N},()=>new Float64Array(N+1));
 M[idx.get(a)][N]=1;
 for(const e of es){if(!seen.has(e.a)||e.a===e.b)continue;const g=1/e.r,i=idx.get(e.a),j=idx.get(e.b);
 if(i!==undefined)M[i][i]+=g;if(j!==undefined)M[j][j]+=g;
 if(i!==undefined&&j!==undefined){M[i][j]-=g;M[j][i]-=g;}}
 for(let k=0;k<N;k++){
 let p=k;for(let i=k+1;i<N;i++)if(Math.abs(M[i][k])>Math.abs(M[p][k]))p=i;
 [M[k],M[p]]=[M[p],M[k]];
 if(M[k][k]===0)throw Error('Singular network');
 for(let i=k+1;i<N;i++){const f=M[i][k]/M[k][k];if(!f)continue;for(let j=k;j<=N;j++)M[i][j]-=f*M[k][j];}
 }
 const v=new Float64Array(N);
 for(let i=N-1;i>=0;i--){let s=M[i][N];for(let j=i+1;j<N;j++)s-=M[i][j]*v[j];v[i]=s/M[i][i];}
 const voltage=n=>n===b?0:v[idx.get(n)]||0;
 const currents=es.filter(e=>seen.has(e.a)).map(e=>({...e,current:Math.abs((voltage(e.a)-voltage(e.b))/e.r)})).filter(e=>e.current>1e-8).sort((a,b)=>b.current-a.current);
 return {resistance:v[idx.get(a)],currents};
}
if(typeof module!=='undefined')module.exports={solve};else root.Ohm={solve};
})(globalThis);

