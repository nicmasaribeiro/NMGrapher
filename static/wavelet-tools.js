'use strict';
(() => {
 const defaults={source:'',time:'',dt:1,unit:'seconds',missing:'reject',resample:false,detrend:'mean',cwt_wavelet:'cmor1.5-1.0',dwt_wavelet:'db4',level:null,boundary:'symmetric',strength:1,threshold_mode:'soft',min_scale:4,max_scale:null,scale_count:48};
 function settings(input){
  if(input==null)return {...defaults};if(typeof input!=='object'||Array.isArray(input))throw Error('Invalid saved wavelet settings.');
  const out={...defaults};
  for(const field of ['source','time']){if(input[field]!==undefined&&(typeof input[field]!=='string'||input[field].length>1200))throw Error('Signal expressions support 1,200 characters.');out[field]=input[field]??out[field];}
  const choices={unit:['seconds','days','samples'],missing:['reject','interpolate'],detrend:['none','mean','linear'],cwt_wavelet:['cmor1.5-1.0','morl','mexh','gaus1'],dwt_wavelet:['haar','db2','db4','sym4','coif1'],boundary:['symmetric','periodization'],threshold_mode:['soft','hard']};
  for(const [key,values] of Object.entries(choices)){if(input[key]!==undefined&&!values.includes(input[key]))throw Error('Choose a supported '+key+'.');out[key]=input[key]??out[key];}
  for(const [key,lo,hi,whole] of [['dt',1e-12,1e12,false],['strength',0,10,false],['min_scale',2,1024,false],['scale_count',8,96,true],['level',1,10,true],['max_scale',2,1024,false]]){
   const value=input[key]??out[key];if(value===null&&['level','max_scale'].includes(key)){out[key]=null;continue;}
   if(typeof value!=='number'||!Number.isFinite(value)||value<lo||value>hi||whole&&!Number.isInteger(value))throw Error('Invalid '+key+' value.');out[key]=value;
  }
  if(input.resample!==undefined&&typeof input.resample!=='boolean')throw Error('Invalid resampling option.');out.resample=input.resample??false;
  if(out.max_scale!==null&&out.max_scale<=out.min_scale)throw Error('Maximum scale must exceed minimum scale.');
  return out;
 }
 function parseValues(text){
  if(typeof text!=='string'||text.length>500000)throw Error('Paste up to 10,000 real samples.');
  const values=text.trim().split(/[\s,;]+/).filter(Boolean).map(s=>{if(!/^[+-]?(?:\d+\.?\d*|\.\d+)(?:e[+-]?\d+)?$/i.test(s))throw Error('Paste real numbers separated by spaces, commas, or newlines. Use Import data for tables with headers.');const n=Number(s);if(!Number.isFinite(n)||Math.abs(n)>1e100)throw Error('Use finite signal values within ±1e100.');return n;});
  if(values.length<8||values.length>10000)throw Error('Use 8–10,000 samples.');return values;
 }
 function demo(){
  let seed=123456789;const random=()=>{seed=(1664525*seed+1013904223)>>>0;return (seed+.5)/4294967296;};
  const time=[],values=[],clean=[];
  for(let k=0;k<512;k++){const t=k/128,frequency=t<2?6:20,v=Math.sin(2*Math.PI*frequency*t)+.35*Math.sin(2*Math.PI*2*t),noise=.2*Math.sqrt(-2*Math.log(random()))*Math.cos(2*Math.PI*random());time.push(t);clean.push(v);values.push(v+noise);}
  return {time,values,clean};
 }
 function columns(report){
  const columns=[{name:'time',values:report.time},{name:'signal',values:report.observed},{name:'prepared',values:report.prepared},{name:'baseline',values:report.baseline},{name:'reconstruction',values:report.dwt.reconstruction},{name:'denoised',values:report.dwt.denoised},{name:'residual',values:report.observed.map((v,i)=>v-report.dwt.denoised[i])}];
  for(const band of report.dwt.bands)columns.push({name:band.name,values:band.values});return columns;
 }
 function csv(report){const cols=columns(report);return cols.map(c=>c.name).join(',')+'\n'+report.time.map((_,i)=>cols.map(c=>c.values[i]).join(',')).join('\n')+'\n';}
 function dataset(report,key,name,id){
  const chosen=columns(report).find(c=>c.name===key);if(!chosen||key==='time')throw Error('Choose an output signal.');
  return {id,name,columns:[{name:'time',label:'Time',values:[...report.time]},{name:key,label:key,values:[...chosen.values]}],x:'time',y:[key],style:'lines',visible:true};
 }
 function power(report,log){return report.cwt.power.map(row=>row.map(v=>log?(v>0?Math.log10(v):null):v));}
 function edgeLines(report){
  const start=report.time[0],end=report.time.at(-1),freq=report.cwt.frequency;
  return [1,-1].map(sign=>({type:'scatter',mode:'lines',x:report.cwt.edge_width.map(w=>start+w<=end-w?(sign===1?start+w:end-w):null),y:freq,line:{color:'#fff',dash:'dot',width:1.5},hoverinfo:'skip',showlegend:false,connectgaps:false}));
 }
 const api={defaults,settings,parseValues,demo,columns,csv,dataset,power,edgeLines};if(typeof window!=='undefined')window.WaveletTools=api;if(typeof module!=='undefined')module.exports=api;
})();
