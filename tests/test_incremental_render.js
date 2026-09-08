'use strict';
const assert=require('node:assert/strict'),fs=require('node:fs'),vm=require('node:vm');
const source=fs.readFileSync('static/app.js','utf8');
const extract=(start,end)=>{const a=source.indexOf(start),b=source.indexOf(end,a);assert.ok(a>=0&&b>a,`Missing source boundary ${start}`);return source.slice(a,b);};
class Element{
 constructor(tag){this.tag=tag;this.children=[];this.parent=null;this.attrs={};this.dataset={};this.style={setProperty(){}};this.className='';this.value='';this.scrollHeight=36;this._text='';this.classList={add:name=>{if(!this.matches('.'+name))this.className+=' '+name;},remove:name=>{this.className=this.className.split(/\s+/).filter(c=>c!==name).join(' ');},toggle:(name,on)=>{this.classList[on?'add':'remove'](name);}};}
 append(...nodes){for(const node of nodes){if(typeof node==='string')continue;node.parent=this;this.children.push(node);}}
 replaceChildren(...nodes){for(const node of this.children)node.parent=null;this.children=[];this._text='';this.append(...nodes);}
 set textContent(value){this.replaceChildren();this._text=String(value);}get textContent(){return this._text+this.children.map(child=>child.textContent).join('');}
 setAttribute(key,value){this.attrs[key]=value;}removeAttribute(key){delete this.attrs[key];}
 contains(element){return !!element&&(element===this||this.children.some(child=>child.contains(element)));}
 matches(selector){const row=selector.match(/^\.expression\[data-id="([^"]+)"\]$/);if(row)return this.dataset.id===row[1]&&this.matches('.expression');if(selector.startsWith('.'))return this.className.split(/\s+/).includes(selector.slice(1));return this.tag===selector;}
 querySelector(selector){for(const node of this.children){if(node.matches(selector))return node;const nested=node.querySelector(selector);if(nested)return nested;}return null;}
 querySelectorAll(selector){return this.children.flatMap(node=>[...(node.matches(selector)?[node]:[]),...node.querySelectorAll(selector)]);}
}
const row=(id,text,type='expression')=>({id,text,type,color:'#2864d7',visible:true,min:-5,max:5,plotName:'',plotComponent:'all',plotSlice:null});
const curve=text=>({kind:'curve',text,x:[0,1],y:[0,1],function:{name:'f',parameters:['x'],body:'x'}});
const scalar=(text,value)=>({kind:'scalar',text,value,numeric:value});
function fixture(){
 const elements=new Map(),listeners=new Map(),timers=new Map(),runs=[];let timerId=0;
 const $=id=>{if(!elements.has(id))elements.set(id,new Element('div'));return elements.get(id);};
 const document={activeElement:null,createElement:tag=>new Element(tag),querySelector:selector=>$('expressions').querySelector(selector),addEventListener:(event,callback)=>listeners.set(event,callback)};
 const context={$,document,rows:[row('a','f(x)=x'),row('b','a=1'),row('note','Remember this','note')],results:[curve('f(x)=x'),scalar('a=1',1),{kind:'empty',text:'Remember this'}],resultIds:['a','b','note'],graphs:[{id:'graph-a'},{id:'graph-b'}],graphResults:[],datasets:[],bounds:[-5,5,-5,5],view:'graph',requestId:1,pendingRows:new Set([0,1]),dirtyResults:new Set(),deferredResults:new Set(),dirtyGraphs:false,paintTimer:null,
  fmt:String,renderMath:()=>{},saveLocal:()=>true,renderGraphs:()=>{},drawPlot:async()=>{},toast:message=>assert.fail('Unexpected toast: '+message),setComputing:()=>{},computeClient:{run:(payload,callbacks)=>{runs.push({payload,callbacks});return Promise.resolve();}},
  setTimeout:callback=>{timers.set(++timerId,callback);return timerId;},clearTimeout:id=>timers.delete(id)};
 vm.createContext(context);
 const code=extract('function renderRows(){','function setComputing(')+extract('function queueResultPaint(){','function schedule(')+extract('async function evaluate(){',"$('stopComputeBtn').onclick=")+extract("document.addEventListener('focusout'",'function selectView(');
 vm.runInContext(code,context);
 const flush=()=>{let rounds=0;while(timers.size){assert.ok(++rounds<20,'Unexpected timer loop');const current=[...timers.values()];timers.clear();for(const callback of current)callback();}};
 const article=id=>document.querySelector(`.expression[data-id="${id}"]`),box=id=>article(id).querySelector('.result');
 return {context,document,listeners,timers,runs,flush,article,box};
}
(async()=>{
 // Adding/removing notes and reordering rows preserve completed controls by ID.
 const retained=fixture(),c=retained.context;c.renderRows();assert.equal(retained.box('a').querySelector('button').textContent,'Edit function');assert.ok(retained.box('b').querySelector('.slider-line'));
 c.rows=[c.rows[2],c.rows[1],c.rows[0],row('new-note','Next step','note')];c.renderRows();assert.deepEqual(Array.from(c.resultIds),['note','b','a','new-note']);assert.equal(c.results[1].numeric,1);assert.equal(c.results[2].function.name,'f');assert.ok(retained.box('a').querySelector('.plot-name-field'));assert.ok(retained.box('b').querySelector('.slider-line'));assert.equal(retained.article('new-note').querySelector('.result'),null);
 c.rows=c.rows.filter(r=>r.id!=='new-note');c.renderRows();assert.ok(retained.box('a').querySelector('.plot-name-field'));
 c.rows[2].text='f(x)=x^2';c.renderRows();assert.equal(c.results[2].kind,'empty');assert.equal(retained.box('a').children.length,0,'Changed formula must not reuse old formula controls');assert.ok(retained.box('b').querySelector('.slider-line'));
 // An arriving result cannot replace the focused name field or its selection.
 const focused=fixture(),f=focused.context;f.renderRows();const name=focused.box('a').querySelector('.plot-name-field').querySelector('input');name.value='My current graph';name.selectionStart=3;name.selectionEnd=7;name.oninput();focused.document.activeElement=name;
 f.results[0]={kind:'error',text:'f(x)=x',error:'New calculation result'};f.renderResults(new Set([0]));assert.equal(focused.box('a').querySelector('.plot-name-field').querySelector('input'),name);assert.equal(name.selectionStart,3);assert.equal(name.selectionEnd,7);assert.equal(f.deferredResults.has('a'),true);
 // Moving focus within the same result still defers repaint.
 focused.document.activeElement=focused.box('a').querySelector('button');focused.listeners.get('focusout')();focused.flush();assert.equal(f.deferredResults.has('a'),true);assert.ok(focused.box('a').contains(name));
 focused.document.activeElement=null;focused.listeners.get('focusout')();focused.flush();assert.equal(f.deferredResults.has('a'),false);assert.match(focused.box('a').textContent,/New calculation result/);assert.equal(f.rows[0].plotName,'My current graph');
 // A focused slider survives newer scalar results until focus leaves its row.
 const slider=focused.box('b').querySelector('.slider-line').querySelectorAll('input').find(input=>input.type==='range');focused.document.activeElement=slider;f.results[1]=scalar('a=1',2);f.renderResults(new Set([1]));assert.ok(focused.box('b').contains(slider));assert.equal(slider.value,1);focused.document.activeElement=null;focused.listeners.get('focusout')();focused.flush();assert.equal(focused.box('b').querySelector('.slider-line').querySelectorAll('input').find(input=>input.type==='range').value,2);
 // Focusout follows stable row IDs if an earlier update's indices have shifted.
 const shifted=fixture(),s=shifted.context;s.renderRows();shifted.document.activeElement=shifted.box('a').querySelector('button');s.results[0]={kind:'error',text:'f(x)=x',error:'Only row a'};s.renderResults(new Set([0]));[s.rows[0],s.rows[1]]=[s.rows[1],s.rows[0]];[s.results[0],s.results[1]]=[s.results[1],s.results[0]];s.deferredResults.add('removed-row');shifted.document.activeElement=null;shifted.listeners.get('focusout')();shifted.flush();assert.match(shifted.box('a').textContent,/Only row a/);assert.ok(shifted.box('b').querySelector('.slider-line'));assert.equal(s.deferredResults.size,0);
 // Late responses are isolated by both generation and row/graph identity.
 const asyncRows=fixture(),a=asyncRows.context;a.renderRows();await a.evaluate();const old=asyncRows.runs[0].callbacks;old.onResult({kind:'row',index:1,result:scalar('a=1',9)});assert.equal(a.results[1].numeric,9);assert.equal(a.pendingRows.has(1),false);assert.equal(a.dirtyResults.has(1),true);
 const previous=a.results[0];a.rows[0]=row('replacement','g(x)=x');old.onResult({kind:'row',index:0,result:scalar('wrong',99)});assert.equal(a.results[0],previous,'Matching index with a different row ID must be ignored');
 for(const index of [-1,1.5,50])old.onResult({kind:'row',index,result:scalar('invalid',99)});assert.equal(a.results.length,3);
 a.graphs[0]={id:'replacement-graph'};old.onResult({kind:'graph',index:0,result:{id:'graph-a',value:99}});assert.equal(a.graphResults.length,0);old.onResult({kind:'graph',index:1,result:{id:'graph-b',value:2}});assert.equal(a.graphResults[0].id,'graph-b');
 a.requestId++;old.onResult({kind:'row',index:1,result:scalar('stale',100)});old.onResult({kind:'graph',index:1,result:{id:'graph-b',value:100}});assert.equal(a.results[1].numeric,9);assert.equal(a.graphResults[0].value,2);
 await a.evaluate();const latest=asyncRows.runs[1].callbacks;latest.onResult({kind:'row',index:0,result:scalar('g(x)=x',7)});assert.equal(a.results[0].numeric,7);assert.equal(a.resultIds[0],'replacement');asyncRows.flush();
 // Multiple incremental paints serialize Plotly work and coalesce queued redraws.
 const draws=[];const plot={plotTask:null,plotQueued:false,drawPlotNow:()=>new Promise(resolve=>draws.push(resolve))};vm.createContext(plot);vm.runInContext(extract('function drawPlot(){','async function drawPlotNow(){'),plot);
 const first=plot.drawPlot(),second=plot.drawPlot(),third=plot.drawPlot();assert.equal(first,second);assert.equal(second,third);assert.equal(draws.length,1);draws[0]();for(let i=0;i<8;i++)await Promise.resolve();assert.equal(draws.length,2,'Queued updates should coalesce into one subsequent draw');draws[1]();await first;assert.equal(plot.plotTask,null);
 console.log('Incremental rendering: retained controls, focus/caret and slider preservation, deferred ID lookup, row/graph generation isolation, and serialized/coalesced redraws passed.');
})().catch(error=>{console.error(error);process.exitCode=1;});
