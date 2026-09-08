'use strict';
const assert=require('node:assert/strict'),fs=require('node:fs'),vm=require('node:vm');
global.GreekInput=require('../static/greek-input.js');
const EnergyTools=require('../static/energy-tools.js'),DatasetTools=require('../static/dataset-tools.js');
const source=fs.readFileSync('static/app.js','utf8');
function node(){return {value:'',checked:false,hidden:false,disabled:false,textContent:'',open:false,listeners:{},append(){},replaceChildren(){},showModal(){this.open=true;},close(){this.open=false;},addEventListener(event,handler){this.listeners[event]=handler;}};}
const nodes=new Map(),$=id=>{if(!nodes.has(id))nodes.set(id,node());return nodes.get(id);};
const model={kind:'rbm',weights:[[.1,.2],[.3,.4]],visible_bias:[0,0],hidden_bias:[0,0],temperature:1};
const report={model,kind:'rbm',visible:2,hidden:2,temperature:1,exact_available:false,samples:[[0,0],[1,1]]};
let sent,active,cancelled=0,saves=0;
const client={cancel(){cancelled++;},run(payload,callbacks){sent=payload;return new Promise(resolve=>{active={callbacks,resolve};});}};
const context={$,EnergyTools,DatasetTools,energyState:null,energyRevision:0,energyBusy:false,energyReport:null,energyClient:client,
 rows:[],datasets:[],requestId:0,document:{createElement:node},window:{addEventListener(){}},Plotly:{react(){},purge(){}},
 fetch:async(url,options)=>{sent=JSON.parse(options.body);return {ok:true,json:async()=>url==='/api/evaluate'?{results:[]}:{analysis:report}};},
 plotTheme:()=>({paper:'white',text:'black'}),fmt:String,saveLocal:()=>saves++,newRow:text=>({text}),uid:()=> 'samples',
 renderRows(){},renderDatasets(){},schedule(){},toast(){}};
vm.createContext(context);vm.runInContext(source.slice(source.indexOf('const energyIds=')),context);
async function main(){
 for(const [key,value] of Object.entries(EnergyTools.defaults))if(key==='energyBinarize')$(key).checked=value;else $(key).value=value;
 // Loading a worksheet model must work even when the parameter draft is invalid.
 $('energyWeights').value='invalid JSON';$('energySource').value='M';await context.energyAnalyze('load');
 assert.equal(sent.source,'M');assert(!('model' in sent));assert.equal($('energyWeights').value,JSON.stringify(model.weights));
 assert.equal(context.energyState.model.kind,'rbm');assert(saves>0);
 // A late response after an edit must never overwrite the new draft.
 let resolve;context.fetch=()=>new Promise(r=>{resolve=r;});const old=context.energyAnalyze();
 $('energyWeights').value='[[9,9],[9,9]]';$('energyWeights').listeners.input();
 resolve({ok:true,json:async()=>({analysis:report})});await old;
 assert.equal($('energyWeights').value,'[[9,9],[9,9]]');assert.equal(context.energyBusy,false);
 // Training continues with its input snapshot after the dialog is closed.
 context.setEnergyModel(model);$('energyData').value='[[0,0],[1,1]]';
 const pending=$('energyTrain').onclick();assert.equal(context.energyBusy,true);$('energyDialog').close();
 assert.equal(sent.data.length,2);assert.equal(sent.model.weights[0][0],.1);
 const trained={...report,model:{...model,visible_bias:[.5,.5]},history:[{epoch:0,train_nll:1.4},{epoch:2,train_nll:1.2}]};
 active.callbacks.onResult({kind:'energy',result:trained});active.callbacks.onDone();active.resolve();await pending;
 assert.equal(context.energyState.model.visible_bias[0],.5);assert.equal(context.energyState.history.length,2);assert.equal(context.energyBusy,false);
 // Cancelling discards a completed-but-late training event.
 const stopped=$('energyTrain').onclick();$('energyStop').onclick();
 active.callbacks.onResult({kind:'energy',result:report});active.callbacks.onDone();active.resolve();await stopped;
 assert.equal(context.energyState.model.visible_bias[0],.5);assert(cancelled>0);
 // Samples become a valid persisted dataset; exported parameters are equation cells.
 context.fetch=async(url,options)=>({ok:true,json:async()=>({results:[]})});
 await $('energyExportSamples').onclick();assert.equal(context.datasets.length,1,$('energyError').textContent);assert.equal(context.datasets[0].columns.length,3);
 await $('energyExport').onclick();assert(context.rows.some(row=>row.text.startsWith('BM_1=rbm(')));
 assert(context.rows.some(row=>row.text==='BM_1_a=[0.5,0.5]'));
 console.log('Energy UI: model loading, stale responses, background training, cancellation and worksheet/dataset exports passed.');
}
main().catch(error=>{console.error(error);process.exitCode=1;});
