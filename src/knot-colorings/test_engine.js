/* Numerical and controller checks; this is not browser rendering or visual QA. */
'use strict';
const fs=require('node:fs'),path=require('node:path'),vm=require('node:vm'),assert=require('node:assert/strict');
const K=require('./engine.js'),M=require('./matrix_rule.js');
const artifactDir=path.join(__dirname,'data');
const study=JSON.parse(fs.readFileSync(path.join(artifactDir,'study.json'),'utf8'));
const witness=JSON.parse(fs.readFileSync(path.join(artifactDir,'matrix-colorings.json'),'utf8'));
let checks=0;
function equal(a,b,label){assert.deepEqual(a,b,label);checks++;}
function truth(value,label){assert.ok(value,label);checks++;}
for(const row of study.references){
 for(const q of [3,5,7,9,15]){
  const solutions=K.enumerate(row.strands,row.word,q);
  equal(solutions.length,row.counts[q],`${row.key}, q=${q}: Python/JS`);
  equal(solutions.filter(x=>new Set(x).size===1).length,q,'constant count');
  for(const solution of solutions){
   equal(K.propagate(solution,row.word,q),solution,'closure');
   const svg=K.renderBraid(row.strands,row.word,q,solution);
   truth(svg.startsWith('<svg')&&svg.endsWith('</svg>'),'complete SVG');
   equal((svg.match(/<circle /g)||[]).length,2*row.strands,'input/output labels');
  }
  equal(K.enumerate(row.strands,row.word.concat([1,-1]),q).length,solutions.length,'canceling pair');
  equal(K.enumerate(row.strands,row.word.map(x=>-x),q).length,solutions.length,'mirror');
 }
}
for(let n=1;n<=4;n++){
 equal(K.components(n,[]).length,n,'empty braid components');
 equal(K.enumerate(n,[],3).length,3**n,'empty braid colorings');
}
assert.throws(()=>K.enumerate(4,[1],31),/budget/);checks++;
assert.throws(()=>K.enumerate(2,[1.5],3),/braid/);checks++;
assert.throws(()=>K.renderBraid(2,[1,1,1],5,[0,1]),/close/);checks++;
// Independent JS multiplication of every Python-generated conjugation table entry.
for(let u=0;u<witness.labels.length;u++)for(let o=0;o<witness.labels.length;o++){
 equal(M.conjugate(witness.labels[u],witness.labels[o],1),witness.labels[witness.forward_table[u][o]],'forward table');
 equal(M.conjugate(witness.labels[u],witness.labels[o],-1),witness.labels[witness.backward_table[u][o]],'backward table');
}
for(const result of Object.values(witness.results))for(const solution of result.solutions){
 truth(M.checkWitness(witness.labels,result.equations,solution).every(Boolean),'matrix witness');
}
// Execute the actual inline app scripts against a deliberately small DOM stub.
// This establishes event wiring and computed text, not layout, accessibility or browser behavior.
class Element {
 constructor(tag='div'){this.tagName=tag;this.children=[];this.events={};this.attributes={};this.disabled=false;this._text='';this._html='';this._value=undefined;}
 set textContent(value){this._text=String(value);this.children=[];}
 get textContent(){return this._text+this.children.map(x=>x.textContent).join('');}
 set innerHTML(value){this._html=String(value);this.children=[];}
 get innerHTML(){return this._html;}
 set value(value){this._value=String(value);}
 get value(){return this._value===undefined?(this.children[0]?.value||''):this._value;}
 append(...children){this.children.push(...children);}
 replaceChildren(...children){this.children=children;this._text='';this._html='';}
 setAttribute(name,value){this.attributes[name]=String(value);}
 focus(){document.activeElement=this;}
 addEventListener(event,handler){(this.events[event]??=[]).push(handler);}
 fire(event){if(event==='click'&&this.disabled)return;for(const handler of this.events[event]||[])handler({target:this});}
}
const html=fs.readFileSync(path.join(__dirname,'index.html'),'utf8');
truth(!/__ENGINE__|__MATRIX_RULE__|__DATA__/.test(html),'no placeholders');
truth(!/<script[^>]+src=|<link[^>]+href=|<iframe|\bfetch\s*\(|\bXMLHttpRequest\b/i.test(html),'offline: no remote resources or fetch calls');
const ids=[...html.matchAll(/\bid="([^"]+)"/g)].map(x=>x[1]);
equal(new Set(ids).size,ids.length,'unique static HTML IDs');
const elements=Object.fromEntries(ids.map(id=>[id,new Element()]));
const document={getElementById(id){if(!elements[id])throw new Error(`Unknown id ${id}`);return elements[id];},createElement(tag){return new Element(tag);}};
const context=vm.createContext({document,console});
for(const match of html.matchAll(/<script>([\s\S]*?)<\/script>/g))vm.runInContext(match[1],context,{timeout:3000});
const $=id=>elements[id];
function change(id,value){$(id).value=value;$(id).fire('change');}
function count(total,extra){equal($('total').textContent,String(total),'controller total');equal($('extra').textContent,String(extra),'controller extra');}
count(9,6);
truth($('drawing').innerHTML.includes('A valid modulo 3 coloring'),'initial SVG');
change('preset','figure8');count(3,0);truth($('next').disabled,'no colorful solution button');
change('modulus','5');count(25,20);truth(!$('next').disabled,'colorful solution button');
let before=$('drawing').innerHTML;$('next').fire('click');truth($('drawing').innerHTML!==before,'next coloring changes diagram');count(25,20);
$('crossings').children[0].fire('click');count(5,0);equal(document.activeElement,$('crossings').children[0],'restore focus after crossing edit');
$('cancel').fire('click');count(5,0);
$('cut').fire('click');count(5,0);
$('mirror').fire('click');count(5,0);
$('reset').fire('click');count(25,20);
for(let i=0;i<10;i++)$('cancel').fire('click');
truth($('cancel').disabled,'crossing cap');equal($('crossings').children.length,16,'bounded crossings');count(25,20);
$('reset').fire('click');equal($('crossings').children.length,4,'reset exact source diagram');
change('preset','trefoil');change('modulus','9');count(27,18);
for(const q of [2,3,9,31]){change('conway-q',String(q));equal($('conway-count').textContent,String(q),'certificate display');}
const seen=new Set();
for(let sample=0;sample<12;sample++){
 for(let crossing=0;crossing<11;crossing++){
  change('matrix-crossing',String(crossing));
  truth($('matrix-status').textContent.includes('All 11 crossing relations hold'),'live matrix check');
  truth($('matrix-relation').innerHTML.includes('Calculated V'),'matrix cards');
 }
 seen.add($('matrix-relation').innerHTML);$('matrix-next').fire('click');
}
equal(seen.size,12,'all nonconstant matrix samples reachable');
truth($('matrix-witness-note').textContent.includes('Example 1 of 12'),'matrix sample wraps');
for(const [order,expectedTotal,expectedExtra,examples] of [['2',21,0,1],['7',360,336,14],['3',728,672,12]]){
 change('matrix-class',order);
 truth($('matrix-class-count').textContent.includes(`${expectedTotal} total colorings`),'class total');
 truth($('matrix-class-count').textContent.includes(`${expectedExtra} nonconstant`),'class nonconstant');
 equal($('matrix-next').disabled,expectedExtra===0,'disable only for class null result');
 for(let sample=0;sample<examples;sample++){
  for(let crossing=0;crossing<11;crossing++){
   change('matrix-crossing',String(crossing));truth($('matrix-status').textContent.includes('All 11 crossing relations hold'),'other-class witness');
  }
  $('matrix-next').fire('click');
 }
}
console.log(JSON.stringify({status:'PASS',checks,numericalParity:true,actualInlineControllerScripts:true,browserRendering:false,visualQA:false},null,2));
