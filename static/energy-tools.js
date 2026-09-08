'use strict';
(() => {
 const defaults={energyKind:'rbm',energyVisible:'4',energyHidden:'2',energyTemperature:'1',energyName:'BM_1',energySeed:'42',energyEpochs:'200',energyRate:'0.05',energyBatch:'32',energyCD:'1',energyDecay:'0.0001',energyValidation:'0.2',energyDataMode:'json',energyDataSource:'',energyThreshold:'0.5',energyBinarize:false,energyWeights:'[[0,0],[0,0],[0,0],[0,0]]',energyVisibleBias:'[0,0,0,0]',energyHiddenBias:'[0,0]',energyData:'[[0,0,0,0],[0,0,0,0],[1,1,1,1],[1,1,1,1],[1,1,0,0],[1,1,0,0],[0,0,1,1],[0,0,1,1]]'};
 function model(value){
  if(!value||!['bm','rbm'].includes(value.kind))throw Error('Choose a binary BM or RBM.');
  const {weights:W,visible_bias:a,hidden_bias:b=[],temperature:T=1}=value;
  const finite=x=>typeof x==='number'&&Number.isFinite(x)&&Math.abs(x)<=100;
  if(!Array.isArray(a)||a.length<1||a.length>(value.kind==='rbm'?16:12)||!a.every(finite))throw Error('Invalid visible biases.');
  if(!Array.isArray(b)||!b.every(finite)||(value.kind==='rbm'?(b.length<1||b.length>16):b.length!==0))throw Error('Invalid hidden biases.');
  const columns=value.kind==='rbm'?b.length:a.length;
  if(!Array.isArray(W)||W.length!==a.length||!W.every(r=>Array.isArray(r)&&r.length===columns&&r.every(finite)))throw Error('Weights must match visible and hidden unit counts.');
  if(value.kind==='bm'&&W.some((r,i)=>Math.abs(r[i])>1e-12||r.some((x,j)=>Math.abs(x-W[j][i])>1e-12)))throw Error('BM weights must be symmetric with zero diagonal.');
  if(typeof T!=='number'||!Number.isFinite(T)||T<.05||T>20)throw Error('Temperature must be 0.05–20.');
  return {kind:value.kind,weights:W.map(r=>[...r]),visible_bias:[...a],hidden_bias:[...b],temperature:T};
 }
 function saved(raw){
  if(raw==null)return null;
  if(typeof raw!=='object'||Array.isArray(raw))throw Error('Invalid saved energy studio.');
  const out={model:raw.model?model(raw.model):null,form:{...defaults},history:[]};
  for(const key of Object.keys(defaults)){
   if(raw.form?.[key]===undefined)continue;
   const value=raw.form[key];
   if(key==='energyBinarize'){if(typeof value!=='boolean')throw Error('Invalid binarization setting.');}
   else if(typeof value!=='string'||value.length>(key==='energyData'?100000:10000))throw Error('Saved energy inputs are too large.');
   out.form[key]=value;
  }
  if(raw.history!==undefined){
   if(!Array.isArray(raw.history)||raw.history.length>52)throw Error('Invalid energy training history.');
   const keys=['epoch','train_nll','validation_nll','train_reconstruction_mse','validation_reconstruction_mse'];
   out.history=raw.history.map(row=>{const r={};for(const key of keys)if(row[key]!==undefined){if(typeof row[key]!=='number'||!Number.isFinite(row[key]))throw Error('Invalid training metric.');r[key]=row[key];}return r;});
  }
  return out;
 }
 function definitions(raw,name){
  const m=model(raw);
  if(!/^[\p{L}][\p{L}\p{N}_]{0,30}$/u.test(name))throw Error('Use a model name of up to 31 letters/digits/underscores, starting with a letter.');
  const rows=[],W=name+'_W',a=name+'_a',b=name+'_b',literal=JSON.stringify(m.weights);
  if((W+'='+literal).length<=1200)rows.push(W+'='+literal);
  else{const parts=m.weights.map((r,i)=>W+'_'+i);m.weights.forEach((r,i)=>rows.push(parts[i]+'='+JSON.stringify(r)));rows.push(W+'=['+parts.join(',')+']');}
  rows.push(a+'='+JSON.stringify(m.visible_bias));if(m.kind==='rbm')rows.push(b+'='+JSON.stringify(m.hidden_bias));
  rows.push(name+'='+(m.kind==='rbm'?`rbm(${W},${a},${b},${m.temperature})`:`boltzmann_machine(${W},${a},${m.temperature})`));
  if(rows.some(r=>r.length>1200))throw Error('Model parameters exceed worksheet cell limits.');
  return rows;
 }
 const api={defaults,model,saved,definitions};if(typeof window!=='undefined')window.EnergyTools=api;if(typeof module!=='undefined')module.exports=api;
})();
