'use strict';
(() => {
 const namespace='http://www.w3.org/1998/Math/MathML';
 const tags=new Set(['mrow','mi','mn','mo','mfrac','msup','msub','msubsup','msqrt','mtable','mtr','mtd','mspace']);
 const attributes=new Set(['mathvariant','width']);
 const pending=new Map(),latest=new WeakMap(),cache=new Map();let timer;
 function build(tree){
  if(!tree||!tags.has(tree.tag))throw Error('Invalid mathematical preview.');
  const node=document.createElementNS(namespace,tree.tag);
  for(const [key,value] of Object.entries(tree.attrs||{}))if(attributes.has(key))node.setAttribute(key,String(value));
  if(tree.text!==undefined)node.textContent=String(tree.text);
  for(const child of tree.children||[])node.append(build(child));
  return node;
 }
 function apply(container,source,result){
  if(latest.get(container)!==source||!container.isConnected)return;
  if(result.tree){const math=document.createElementNS(namespace,'math');math.setAttribute('display','block');math.setAttribute('aria-label',source);math.append(build(result.tree));container.replaceChildren(math);container.classList.remove('math-fallback');container.removeAttribute('title');}
  else{container.textContent=source;container.classList.add('math-fallback');container.title=result.error||'Finish the expression to show its mathematical preview.';}
 }
 async function flush(){
  const entries=[...pending.entries()].filter(([container])=>container.isConnected);pending.clear();
  for(let start=0;start<entries.length;start+=60){const batch=entries.slice(start,start+60);
   try{const response=await fetch('/api/preview',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({expressions:batch.map(([,source])=>source)})});if(!response.ok)continue;const data=await response.json();batch.forEach(([container,source],i)=>{const result=data.previews[i];if(!result)return;cache.set(source,result);if(cache.size>200)cache.delete(cache.keys().next().value);apply(container,source,result);});}catch{}
  }
 }
 function render(container,source){
  if(!container)return;latest.set(container,source);container.hidden=!source.trim();container.textContent=source;container.classList.add('math-fallback');
  if(!source.trim())return;
  if(cache.has(source)&&container.isConnected){apply(container,source,cache.get(source));return;}
  pending.set(container,source);clearTimeout(timer);timer=setTimeout(flush,70);
 }
 const api={render,build};if(typeof window!=='undefined')window.MathPreview=api;if(typeof module!=='undefined')module.exports=api;
})();
