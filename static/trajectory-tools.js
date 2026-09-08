'use strict';
(() => {
 const defaults={kind:'gbm',initial:100,drift:.05,volatility:.2,horizon:1,steps:252,paths:8,seed:42,start:0,expression:'[cos(t),sin(t),t/4]',update:'s + dt*[-s[1],s[0]]',state:'[1,0]',name:'Trajectory',display:'time',coordinates:'0,1',speed:1,trail:0};
 function settings(raw){
  if(raw==null)return {...defaults};if(typeof raw!=='object'||Array.isArray(raw))throw Error('Invalid trajectory settings.');
  const out={...defaults};
  for(const key of Object.keys(defaults))if(raw[key]!==undefined){const v=raw[key];if(typeof v!==typeof defaults[key]||typeof v==='number'&&!Number.isFinite(v)||typeof v==='string'&&v.length>1200)throw Error('Invalid saved trajectory setting: '+key);out[key]=v;}
  if(!['gbm','parametric','sequence'].includes(out.kind)||!['time','2d','3d'].includes(out.display)||out.speed<.1||out.speed>8||!Number.isInteger(out.trail)||out.trail<0||out.trail>2000)throw Error('Invalid trajectory playback settings.');
  return out;
 }
 function coordinates(report,display,text){
  if(report.kind==='gbm')return [0];
  const result=String(text).split(',').map(x=>Number(x.trim()));const n=display==='time'?1:display==='2d'?2:3;
  if(result.length!==n||result.some(v=>!Number.isInteger(v)||v<0||v>=report.dimensions)||new Set(result).size!==result.length)throw Error(`Choose ${n} distinct component indices from 0 to ${report.dimensions-1}.`);
  return result;
 }
 function extent(values){let low=Infinity,high=-Infinity;for(const x of values){low=Math.min(low,x);high=Math.max(high,x);}const pad=(high-low||Math.max(1,Math.abs(low)))*.07;return [low-pad,high+pad];}
 const colors=['#2864d7','#dd6b35','#8a4dc2','#169582','#cf4166','#a57b17'];
 const plotQueues=new Map();
 function draw(plot,callback){const next=(plotQueues.get(plot)||Promise.resolve()).catch(()=>{}).then(callback);plotQueues.set(plot,next);return next.finally(()=>{if(plotQueues.get(plot)===next)plotQueues.delete(plot);});}
 function config(report,options={}){
  const display=report.kind==='gbm'?'time':options.display||'2d',coords=coordinates(report,display,options.coordinates??'0,1');
  const mapped=report.values.map(path=>({x:display==='time'?report.time:path.map(p=>p[coords[0]]),y:path.map(p=>p[coords[display==='time'?0:1]]),...(display==='3d'?{z:path.map(p=>p[coords[2]])}:{})}));
  const theme=options.theme||{paper:'#fff',text:'#26364a',grid:'#dce3ec'};
  const axis=(title,values)=>({title:{text:title},range:extent(values),gridcolor:theme.grid,zerolinecolor:theme.grid});
  const all=key=>mapped.flatMap(p=>p[key]);let yvalues=all('y');
  if(report.reference)yvalues=yvalues.concat(report.reference.lower,report.reference.upper);
  const layout={paper_bgcolor:theme.paper,plot_bgcolor:theme.paper,font:{color:theme.text},margin:{l:65,r:25,t:45,b:55},height:450,showlegend:report.paths<=8,title:{text:options.name||'Trajectory'},uirevision:'trajectory',legend:{orientation:'h'}};
  if(display==='3d')layout.scene={xaxis:axis('State '+coords[0],all('x')),yaxis:axis('State '+coords[1],yvalues),zaxis:axis('State '+coords[2],all('z')),aspectmode:'cube'};
  else{layout.xaxis=axis(display==='time'?'Time':'State '+coords[0],all('x'));layout.yaxis=axis('State '+coords[display==='time'?0:1],yvalues);if(report.kind==='gbm')layout.yaxis.title.text='S(t)';if(display==='2d')layout.yaxis.scaleanchor='x';}
  return {display,coords,mapped,layout};
 }
 function frame(report,plan,index,trail=0){
  const k=Math.max(0,Math.min(report.frames-1,Math.floor(index))),begin=trail?Math.max(0,k-trail+1):0,type=plan.display==='3d'?'scatter3d':'scatter',data=[];
  if(report.reference){const r=report.reference,x=report.time.slice(0,k+1);data.push({type:'scatter',x,y:r.lower.slice(0,k+1),mode:'lines',line:{width:0},name:'Pointwise 95% range',showlegend:false,hoverinfo:'skip'},{type:'scatter',x,y:r.upper.slice(0,k+1),mode:'lines',line:{width:0},fill:'tonexty',fillcolor:'rgba(40,100,215,.10)',name:'Pointwise 95% range',hoverinfo:'skip'},{type:'scatter',x,y:r.mean.slice(0,k+1),mode:'lines',line:{color:'#169582',dash:'dash',width:3},name:'Theoretical mean'});}
  plan.mapped.forEach((path,i)=>{const color=colors[i%colors.length],line={type,mode:'lines',name:'Path '+(i+1),line:{color,width:2},connectgaps:false},head={type,mode:'markers',name:'Path '+(i+1)+' current',marker:{color,size:plan.display==='3d'?4:7},showlegend:false};for(const key of ['x','y',...(plan.display==='3d'?['z']:[])]){line[key]=path[key].slice(begin,k+1);head[key]=[path[key][k]];}data.push(line,head);});
  return data;
 }
 class Player{
  constructor(plot,report,options={}){this.plot=plot;this.report=report;this.options=options;this.plan=config(report,options);this.position=0;this.playing=false;this.generation=0;this.busy=false;this.dirty=false;this.disposed=false;this.last=null;this.paint();}
  get index(){return Math.floor(this.position);}
  paint(){this.dirty=true;if(this.busy||this.disposed)return;this.busy=true;const generation=this.generation;const data=frame(this.report,this.plan,this.index,this.options.trail||0);this.dirty=false;this.options.onFrame?.(this.index,this.playing);
   this.pending=draw(this.plot,()=>{if(!this.disposed)return Plotly.react(this.plot,data,this.plan.layout,{responsive:true,displaylogo:false});}).catch(e=>{if(!this.disposed){this.pause();this.options.onError?.(e);}}).finally(()=>{this.busy=false;if(!this.disposed&&(this.dirty||generation!==this.generation))this.paint();});
  }
  play(){if(this.disposed||this.playing)return;if(this.position>=this.report.frames-1)this.position=0;this.playing=true;this.last=null;this.options.onFrame?.(this.index,true);this.raf=requestAnimationFrame(t=>this.tick(t));}
  tick(now){if(!this.playing||this.disposed)return;if(this.last!==null)this.position=Math.min(this.report.frames-1,this.position+(now-this.last)*(this.options.speed||1)*(this.report.frames-1)/10000);this.last=now;if(this.lastPaint===undefined||now-this.lastPaint>=50||this.position>=this.report.frames-1){this.lastPaint=now;this.paint();}if(this.position>=this.report.frames-1)this.pause();else this.raf=requestAnimationFrame(t=>this.tick(t));}
  pause(){this.playing=false;cancelAnimationFrame(this.raf);this.last=null;this.options.onFrame?.(this.index,false);}
  seek(k){this.pause();this.position=Math.max(0,Math.min(this.report.frames-1,Number(k)||0));this.paint();}
  dispose(){this.pause();this.disposed=true;this.generation++;}
  async ready(){while(this.busy)await this.pending;}
 }
 function dataset(report,name,id){
  if(!/^[\p{L}_][\p{L}\p{N}_]{0,59}$/u.test(name))throw Error('Use a dataset name with letters, digits, or underscores, starting with a letter.');
  const columns=[{name:'time',values:report.time.slice()}];report.values.forEach((path,i)=>{for(let j=0;j<report.dimensions;j++)columns.push({name:'path_'+(i+1)+(report.dimensions>1?'_state_'+j:''),values:path.map(p=>p[j])});});
  if(columns.length>32)throw Error('This trajectory has too many columns for one dataset.');
  return {id,name,columns,x:'time',y:columns.slice(1,9).map(c=>c.name),style:'lines',visible:true};
 }
 function csv(report){const columns=dataset(report,'trajectory','csv').columns;return columns.map(c=>c.name).join(',')+'\n'+report.time.map((_,i)=>columns.map(c=>c.values[i]).join(',')).join('\n')+'\n';}
 const api={defaults,settings,coordinates,config,frame,Player,dataset,csv};if(typeof window!=='undefined')window.TrajectoryTools=api;if(typeof module!=='undefined')module.exports=api;
})();
