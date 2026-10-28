/* Projective 2x2 matrices modulo 7. M and -M are the same label. */
(function(root){'use strict';
const mod=x=>((x%7)+7)%7;
function canonical(values){
 if(!Array.isArray(values)||values.length!==4||values.some(x=>!Number.isInteger(x)))throw new Error('Expected four integer matrix entries');
 const a=values.map(mod),b=a.map(x=>mod(-x));
 for(let i=0;i<4;i++){if(a[i]<b[i])return a;if(a[i]>b[i])return b;}
 return a;
}
function multiply(a,b){const[x,y,z,w]=a,[e,f,g,h]=b;return canonical([x*e+y*g,x*f+y*h,z*e+w*g,z*f+w*h]);}
function inverse(a){const[x,y,z,w]=a;if(mod(x*w-y*z)!==1)throw new Error('Expected determinant one');return canonical([w,-y,-z,x]);}
function same(a,b){a=canonical(a);b=canonical(b);return a.every((x,i)=>x===b[i]);}
function conjugate(under,over,sign){if(sign!==1&&sign!==-1)throw new Error('Expected a signed crossing');return sign>0?multiply(multiply(inverse(over),under),over):multiply(multiply(over,under),inverse(over));}
function checkWitness(labels,equations,solution){return equations.map(([o,u,v,sign])=>same(conjugate(labels[solution[u]],labels[solution[o]],sign),labels[solution[v]]));}
const api={canonical,multiply,inverse,same,conjugate,checkWitness};
if(typeof module!=='undefined'&&module.exports)module.exports=api;else root.MatrixKnotRule=api;
})(globalThis);
