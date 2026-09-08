'use strict';
const assert=require('node:assert/strict'),fs=require('node:fs'),vm=require('node:vm');
global.GreekInput=require('../static/greek-input.js');global.Plotly={react:async()=>{},downloadImage:async()=>{}};global.requestAnimationFrame=()=>1;global.cancelAnimationFrame=()=>{};
const T=require('../static/trajectory-tools.js'),D=require('../static/dataset-tools.js');let active,sent,saved;
const nodes=new Map(),$=id=>{if(!nodes.has(id))nodes.set(id,{value:'',textContent:'',open:false,listeners:{},disabled:false,showModal(){this.open=true;},close(){this.open=false;this.listeners.close?.();},addEventListener(k,fn){this.listeners[k]=fn;},dispatchEvent(e){this.listeners[e.type]?.(e);}});return nodes.get(id);};
class Client{cancel(){}run(payload,callbacks){sent=payload;return new Promise(resolve=>active={callbacks,resolve});}}
const c={$,TrajectoryTools:T,DatasetTools:D,AsyncCompute:{ComputeClient:Client},trajectorySettings:T.settings(null),rows:[{text:'a=2'}],datasets:[],requestId:1,
 window:{addEventListener(){}},document:{addEventListener(){},hidden:false},saveLocal(){saved=c.trajectorySettings;},plotTheme:()=>({paper:'#fff',text:'#123',grid:'#ddd'}),fmt:String,Plotly:global.Plotly,
 renderDatasets(){},schedule(){c.requestId++;},uid:()=> 'path_data',toast(){},fetch:async(url,o)=>{sent=JSON.parse(o.body);return {ok:true,json:async()=>({results:[]})};}};
vm.createContext(c);vm.runInContext(fs.readFileSync('static/trajectory-studio.js','utf8'),c);
(async()=>{
 $('trajectoryBtn').onclick();assert.equal($('trajectoryDialog').open,true);
 $('trajectoryExample').onchange({target:{value:'descent'}});assert.equal($('trajectoryKind').value,'sequence');assert.equal(saved.display,'2d');
 const pending=$('trajectoryGenerate').onclick();assert.equal(sent.trajectory.kind,'sequence');assert.equal(sent.trajectory.initial[0],3);assert.equal(sent.expressions[0].text,'a=2');
 const report={kind:'sequence',frames:3,paths:1,dimensions:2,time:[0,.02,.04],values:[[[3,2],[2.88,1.84],[2.7648,1.6928]]],spec:{kind:'sequence',initial:[3,2],update:'s-dt*[2*s[0],4*s[1]]',horizon:.04,steps:2,start:0}};
 active.callbacks.onResult({kind:'trajectory',result:report});active.callbacks.onDone();active.resolve();await pending;
 assert.equal($('trajectoryGenerate').disabled,false);assert.equal($('trajectoryScrub').max,2);
 $('trajectoryPlay').onclick();assert.equal($('trajectoryPlay').textContent,'Pause');$('trajectoryDialog').close();assert.equal($('trajectoryPlay').textContent,'Play');
 c.window.TrajectoryStudio.open();await $('trajectoryDataset').onclick();assert.equal(c.datasets.length,1,$('trajectoryError').textContent);assert.equal(c.datasets[0].columns[2].values[2],1.6928);
 c.requestId++;$('trajectoryPlay').onclick();assert($('trajectoryError').textContent.includes('worksheet changed'));
 const stale=$('trajectoryGenerate').onclick();$('trajectoryUpdate').value='s';$('trajectoryUpdate').listeners.input();
 active.callbacks.onResult({kind:'trajectory',result:report});active.callbacks.onDone();active.resolve();await stale;
 $('trajectoryPlay').onclick();assert($('trajectoryError').textContent.includes('Generate paths'));
 const html=fs.readFileSync('templates/index.html','utf8');for(const id of nodes.keys())assert(html.includes('id="'+id+'"'),id);
 console.log('Trajectory studio: examples, background generation, playback pause, dataset export and stale-input protection passed.');
})().catch(e=>{console.error(e);process.exitCode=1;});
