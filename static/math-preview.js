'use strict';
(() => {
 const namespace='http://www.w3.org/1998/Math/MathML';
 const tags=new Set(['mrow','mi','mn','mo','mfrac','msup','msub','msubsup','msqrt','mtable','mtr','mtd','mspace']);
 const attributes=new Set(['mathvariant','width']);
 const latest=new WeakMap(),formatted=new WeakSet(),cache=new Map(),queued=new Map(),jobs=new Set();
 const batchSize=60,maxRequests=2,cacheLimit=200;let timer=null,priority=0;
 function build(tree){
  if(!tree||!tags.has(tree.tag))throw Error('Invalid mathematical preview.');
  const node=document.createElementNS(namespace,tree.tag);
  for(const [key,value] of Object.entries(tree.attrs||{}))if(attributes.has(key))node.setAttribute(key,String(value));
  if(tree.text!==undefined)node.textContent=String(tree.text);
  for(const child of tree.children||[])node.append(build(child));
  return node;
 }
 function loading(container,busy){
  if(busy){container.classList.add('preview-loading');container.setAttribute('aria-busy','true');container.setAttribute('aria-label','Updating mathematical preview');container.title='Updating mathematical preview…';}
  else{container.classList.remove('preview-loading');container.removeAttribute('aria-busy');container.removeAttribute('aria-label');container.removeAttribute('title');}
 }
 function apply(container,source,result){
  if(latest.get(container)!==source)return;
  let math;
  try{if(result.tree){math=document.createElementNS(namespace,'math');math.setAttribute('display','block');math.setAttribute('aria-label',source);math.append(build(result.tree));}}catch{result={error:'Could not format this mathematical preview.'};}
  loading(container,false);
  if(math&&math.children.length){container.replaceChildren(math);container.classList.remove('math-fallback');formatted.add(container);}
  else{container.textContent=source;container.classList.add('math-fallback');container.title=result.error||'Finish the expression to show its mathematical preview.';formatted.delete(container);}
 }
 function remember(source,result){cache.delete(source);cache.set(source,result);if(cache.size>cacheLimit)cache.delete(cache.keys().next().value);}
 function wanted(record,attaching=null){
  for(const container of record.targets)if(latest.get(container)!==record.source||(!container.isConnected&&container!==attaching))record.targets.delete(container);
  return record.targets.size>0;
 }
 function cancelUnused(attaching=null){
  for(const job of jobs){
   if(job.records.some(record=>wanted(record,attaching)))continue;
   job.cancelled=true;jobs.delete(job);job.controller.abort();
   for(const record of job.records)if(queued.get(record.source)===record)queued.delete(record.source);
  }
 }
 async function request(job){
  try{
   const response=await fetch('/api/preview',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({expressions:job.records.map(record=>record.source)}),signal:job.controller.signal});
   if(!response.ok)throw Error('Preview request failed.');
   const data=await response.json();
   if(job.cancelled)return;
   if(!Array.isArray(data.previews))throw Error('Invalid preview response.');
   job.records.forEach((record,index)=>{
    const result=data.previews[index]||{error:'Preview unavailable. Edit the expression to retry.'};remember(record.source,result);
    for(const container of record.targets)if(container.isConnected)apply(container,record.source,result);
   });
  }catch{
   if(!job.cancelled)for(const record of job.records)for(const container of record.targets)if(container.isConnected)apply(container,record.source,{error:'Preview unavailable. Edit the expression to retry.'});
  }finally{
   jobs.delete(job);
   for(const record of job.records)if(queued.get(record.source)===record)queued.delete(record.source);
   flush();
  }
 }
 function flush(){
  if(timer!==null){clearTimeout(timer);timer=null;}
  cancelUnused();
  const pending=[];
  for(const record of queued.values())if(!record.job){if(wanted(record))pending.push(record);else queued.delete(record.source);}
  // The latest edited field goes first; duplicate formulas share one request item.
  pending.sort((a,b)=>b.priority-a.priority);
  while(pending.length&&jobs.size<maxRequests){
   const job={records:pending.splice(0,batchSize),controller:new AbortController(),cancelled:false};
   for(const record of job.records)record.job=job;
   jobs.add(job);void request(job);
  }
 }
 function render(container,source){
  if(!container)return;source=String(source??'');
  const previous=latest.get(container);
  if(previous!==source){const old=queued.get(previous);if(old){old.targets.delete(container);if(!old.targets.size&&!old.job)queued.delete(previous);}}
  latest.set(container,source);container.hidden=!source.trim();
  if(!source.trim()){container.textContent='';formatted.delete(container);loading(container,false);cancelUnused();return;}
  if(cache.has(source)){const result=cache.get(source);remember(source,result);apply(container,source,result);cancelUnused();return;}
  // Keep the existing typeset formula until its replacement is ready. The visible
  // loading indicator and accessible label identify it as an updating preview.
  if(!formatted.has(container)){container.textContent=source;container.classList.add('math-fallback');}
  loading(container,true);
  let record=queued.get(source);
  if(!record){record={source,targets:new Set(),priority:0,job:null};queued.set(source,record);}
  record.targets.add(container);record.priority=++priority;cancelUnused(container);
  // A leading batch window avoids postponing previews indefinitely while typing.
  if(!record.job&&timer===null)timer=setTimeout(flush,25);
 }
 const api={render,build};if(typeof window!=='undefined')window.MathPreview=api;if(typeof module!=='undefined')module.exports=api;
})();
