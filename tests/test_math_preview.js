'use strict';
const assert=require('node:assert/strict');
class Element{
 constructor(tag){this.tag=tag;this.children=[];this.attrs={};this.isConnected=true;this.classes=new Set();this.classList={add:name=>this.classes.add(name),remove:name=>this.classes.delete(name)};this._text='';}
 append(child){this.children.push(child);}setAttribute(k,v){this.attrs[k]=v;}removeAttribute(k){delete this.attrs[k];if(k==='title')delete this.title;}replaceChildren(...children){this.children=children;this._text='';}
 set textContent(value){this._text=value;this.children=[];}get textContent(){return this._text;}
}
global.document={createElementNS(namespace,tag){assert.equal(namespace,'http://www.w3.org/1998/Math/MathML');return new Element(tag);}};
let timerId=0;const timers=new Map();
global.setTimeout=fn=>{timers.set(++timerId,fn);return timerId;};global.clearTimeout=id=>timers.delete(id);
const requests=[];
global.fetch=(url,options)=>new Promise((resolve,reject)=>requests.push({url,options,sources:JSON.parse(options.body).expressions,resolve,reject}));
const {build,render}=require('../static/math-preview.js');
const tick=async()=>{for(let i=0;i<8;i++)await Promise.resolve();};
const flush=async()=>{const current=[...timers.values()];timers.clear();for(const fn of current)fn();await tick();};
const respond=async(request,overrides={})=>{request.resolve({ok:true,json:async()=>({previews:request.sources.map(source=>({tree:{tag:'mi',text:source}})),...overrides})});await tick();};
const text=container=>container.children[0]?.children[0]?.textContent;
const result=build({tag:'mfrac',children:[{tag:'mi',text:'d'},{tag:'mrow',children:[{tag:'mi',text:'d',attrs:{mathvariant:'normal',onclick:'bad'}},{tag:'mi',text:'x'}]}]});
assert.equal(result.children[1].children[0].attrs.onclick,undefined);
assert.equal(build({tag:'mi',text:'<img src=x>'}).textContent,'<img src=x>');
assert.throws(()=>build({tag:'script',text:'bad'}),/Invalid/);
(async()=>{
 const container=new Element('div');render(container,'old');await flush();const old=requests.at(-1);
 render(container,'new');assert.equal(old.options.signal.aborted,true);await flush();const current=requests.at(-1);
 await respond(current);await respond(old);assert.equal(text(container),'new');assert.equal(container.attrs['aria-busy'],undefined);
 // Retain formatted content and make its updating state explicit until ready.
 render(container,'next');assert.equal(text(container),'new');assert.equal(container.attrs['aria-busy'],'true');assert.equal(container.classes.has('preview-loading'),true);assert.match(container.attrs['aria-label'],/Updating/);
 await flush();await respond(requests.at(-1));assert.equal(text(container),'next');assert.equal(container.classes.has('preview-loading'),false);
 // Several targets, including one added in flight, share a single formula item.
 const first=new Element('div'),second=new Element('div'),third=new Element('div');const before=requests.length;
 render(first,'shared');render(second,'shared');assert.equal(timers.size,1);await flush();const shared=requests.at(-1);render(third,'shared');await flush();assert.equal(requests.length,before+1);assert.deepEqual(shared.sources,['shared']);
 render(first,'different');assert.equal(shared.options.signal.aborted,false);await flush();const different=requests.at(-1);
 await respond(shared);await respond(different);assert.equal(text(first),'different');assert.equal(text(second),'shared');assert.equal(text(third),'shared');
 // Rebuilding rows while a request is in flight must keep a newly attaching target.
 const replaced=new Element('div');render(replaced,'reattach');await flush();const reattach=requests.at(-1);replaced.isConnected=false;const replacement=new Element('div');replacement.isConnected=false;render(replacement,'reattach');replacement.isConnected=true;assert.equal(reattach.options.signal.aborted,false);await respond(reattach);assert.equal(text(replacement),'reattach');
 // Cache hits also render immediately into a new element before it is attached.
 const cached=new Element('div');cached.isConnected=false;const cachedCount=requests.length;render(cached,'shared');assert.equal(text(cached),'shared');await flush();assert.equal(requests.length,cachedCount);
 // Rapid edits are batched once and only send the newest formula, first in line.
 const edit=new Element('div'),other=new Element('div');render(other,'background');render(edit,'draft1');const leading=[...timers.keys()][0];render(edit,'draft2');render(edit,'draft3');assert.equal([...timers.keys()][0],leading);await flush();assert.deepEqual(requests.at(-1).sources,['draft3','background']);await respond(requests.at(-1));assert.equal(text(edit),'draft3');
 // Clearing/detaching cancels work with no remaining consumers.
 render(edit,'clear-me');await flush();const clearing=requests.at(-1);render(edit,'');assert.equal(clearing.options.signal.aborted,true);assert.equal(edit.hidden,true);assert.equal(edit.attrs['aria-busy'],undefined);await respond(clearing);assert.equal(edit.children.length,0);
 render(edit,'detached');await flush();const detached=requests.at(-1);edit.isConnected=false;render(other,'trigger-cleanup');assert.equal(detached.options.signal.aborted,true);await flush();await respond(requests.at(-1));await respond(detached);
 // Failed requests clear the busy state and can be retried without cached errors.
 const failed=new Element('div');render(failed,'retry-me');await flush();requests.at(-1).reject(Error('offline'));await tick();assert.equal(failed.attrs['aria-busy'],undefined);assert.equal(failed.textContent,'retry-me');assert.match(failed.title,/unavailable/);render(failed,'retry-me');await flush();await respond(requests.at(-1));assert.equal(text(failed),'retry-me');
 // Large batches stay under the API cap with at most two requests in flight.
 const many=Array.from({length:125},()=>new Element('div'));const start=requests.length;many.forEach((el,index)=>render(el,`bounded_${index}`));await flush();assert.equal(requests.length,start+2);assert.equal(requests[start].sources.length,60);assert.equal(requests[start+1].sources.length,60);await respond(requests[start]);assert.equal(requests.length,start+3);assert.equal(requests[start+2].sources.length,5);await respond(requests[start+1]);await respond(requests[start+2]);assert.equal(text(many[0]),'bounded_0');assert.equal(text(many[124]),'bounded_124');
 // Cache remains bounded: old formulas are evicted and fetched again.
 const more=Array.from({length:90},()=>new Element('div'));more.forEach((el,index)=>render(el,`cache_${index}`));await flush();const lastTwo=requests.slice(-2);await respond(lastTwo[0]);await respond(lastTwo[1]);const evicted=new Element('div');const oldCount=requests.length;render(evicted,'shared');await flush();assert.equal(requests.length,oldCount+1);await respond(requests.at(-1));
 // Malformed trees never bypass the tag allow-list and clear loading safely.
 render(evicted,'malformed');await flush();await respond(requests.at(-1),{previews:[{tree:{tag:'script',text:'bad'}}]});assert.equal(evicted.children.length,0);assert.equal(evicted.textContent,'malformed');assert.equal(evicted.attrs['aria-busy'],undefined);
 console.log('Math preview: safe MathML, retained previews, stale cancellation, leading batching, shared requests, bounded concurrency/cache, and failure recovery passed.');
})().catch(error=>{console.error(error);process.exitCode=1;});
