'use strict';
(() => {
 const fields={kind:'Kind',initial:'Initial',drift:'Drift',volatility:'Volatility',horizon:'Horizon',steps:'Steps',paths:'Paths',seed:'Seed',start:'Start',expression:'Expression',update:'Update',state:'State',name:'Name',display:'Display',coordinates:'Coordinates',speed:'Speed',trail:'Trail'};
 let report=null,player=null,revision=0,busy=false,sourceRevision=null,dirty=false;
 const client=new AsyncCompute.ComputeClient({fetch:(url,options)=>fetch(url==='/api/jobs'?'/api/trajectories/jobs':url,options)});
 const get=key=>$('trajectory'+fields[key]);
 function form(){return Object.fromEntries(Object.entries(fields).map(([key])=>[key,typeof TrajectoryTools.defaults[key]==='number'?Number(get(key).value):get(key).value]));}
 function fill(o){for(const key of Object.keys(fields))get(key).value=o[key]??TrajectoryTools.defaults[key];controls();}
 function capture(){try{trajectorySettings=TrajectoryTools.settings(form());saveLocal();}catch{}}
 function controls(){const kind=get('kind').value;for(const [mode,id] of [['gbm','GBM'],['parametric','Parametric'],['sequence','Sequence']])$('trajectory'+id).hidden=kind!==mode;$('trajectoryStartLabel').hidden=kind==='gbm';get('display').disabled=kind==='gbm';get('coordinates').disabled=kind==='gbm';$('trajectoryEquation').textContent=kind==='gbm'?'dS = μS dt + σS dW · Exact update: Sₖ₊₁ = Sₖ exp((μ − σ²/2)dt + σ√dt Zₖ), Zₖ ~ N(0,1).':kind==='sequence'?'sₖ₊₁ = G(sₖ,k,tₖ,dt) · dt = horizon / steps. Each update uses the previous completed state.':'Sample a scalar or vector position at evenly spaced times. Use t, or call a worksheet function r(t).';}
 function setBusy(value,message){busy=value;$('trajectoryGenerate').disabled=value;$('trajectoryCancel').hidden=!value;if(message)$('trajectoryStatus').textContent=message;}
 function current(){if(!report||dirty)throw Error('Generate paths for the current settings first.');if(report.kind!=='gbm'&&sourceRevision!==requestId)throw Error('The worksheet changed. Generate this trajectory again.');return report;}
 function options(){return {name:get('name').value.trim()||'Trajectory',display:get('display').value,coordinates:get('coordinates').value,speed:Number(get('speed').value),trail:Number(get('trail').value),theme:plotTheme()};}
 function paint(start=0){
  if(!report)return;const o=options();if(!Number.isInteger(o.trail)||o.trail<0||o.trail>2000)throw Error('Trail must be 0–2000 samples.');TrajectoryTools.config(report,o);
  const shown=report;player?.dispose();player=new TrajectoryTools.Player('trajectoryPlot',report,{...o,onFrame:(k,playing)=>{if(report!==shown)return;$('trajectoryScrub').value=k;$('trajectoryPlay').textContent=playing?'Pause':'Play';$('trajectoryTime').textContent='t = '+fmt(shown.time[k])+' · step '+k;},onError:e=>$('trajectoryError').textContent=e.message});
  $('trajectoryScrub').max=report.frames-1;player.seek(start);
 }
 function accept(data){report=data;dirty=false;sourceRevision=requestId;
  if(data.kind==='gbm'){get('display').value='time';get('coordinates').value='0';}
  else{try{TrajectoryTools.coordinates(data,get('display').value,get('coordinates').value);}catch{get('display').value=data.dimensions===1?'time':data.dimensions===2?'2d':'3d';get('coordinates').value=data.dimensions===1?'0':data.dimensions===2?'0,1':'0,1,2';}}
  paint();const n=data.frames-1;
  $('trajectorySummary').textContent=data.kind==='gbm'?`${data.paths} independent simulated paths · ${n} steps · terminal theoretical mean ${fmt(data.reference.mean.at(-1))}, variance ${fmt(data.reference.terminal_variance)}. Shading is a pointwise 95% probability range, not a band covering 95% of complete paths.`:`${n} sequential samples after the initial state · ${data.dimensions} state components. Playback shows stored values; it does not reevaluate formulas.`;capture();
 }
 function open(data=null,name=null){
  if(!$('trajectoryDialog').open)$('trajectoryDialog').showModal();
  if(data){reset();const o={...trajectorySettings,...data.spec,name:name||trajectorySettings.name};if(data.kind==='sequence')o.state=JSON.stringify(data.spec.initial);if(data.kind!=='gbm')o.initial=trajectorySettings.initial;fill(o);accept(data);setBusy(false,'Trajectory ready');}
  else{fill(trajectorySettings);if(report){try{paint(player?.index||0);}catch(e){$('trajectoryError').textContent=e.message;}}else $('trajectoryStatus').textContent='Choose settings and generate paths.';}
 }
 function reset(){revision++;client.cancel();player?.dispose();player=null;report=null;dirty=false;setBusy(false);}
 $('trajectoryBtn').onclick=()=>open();
 $('trajectoryDialog').addEventListener('close',()=>player?.pause());document.addEventListener('visibilitychange',()=>{if(document.hidden)player?.pause();});window.addEventListener('pagehide',()=>{player?.dispose();client.cancel();});
 for(const key of Object.keys(fields))get(key).addEventListener('input',()=>{
  if(['name','display','coordinates','speed','trail'].includes(key)){
   if(key==='speed'){if(player)player.options.speed=Number(get(key).value);capture();return;}
   if(key==='display')get('coordinates').value=get(key).value==='time'?'0':get(key).value==='2d'?'0,1':'0,1,2';
   try{if(report&&!dirty){paint(player?.index||0);$('trajectoryError').textContent='';}}catch(e){$('trajectoryError').textContent=e.message;}capture();return;
  }
  revision++;client.cancel();player?.pause();dirty=true;setBusy(false,'Settings changed. Generate paths to update the animation.');controls();capture();
 });
 $('trajectoryReseed').onclick=()=>{get('seed').value=crypto.getRandomValues(new Uint32Array(1))[0];get('seed').dispatchEvent(new Event('input'));};
 $('trajectoryGenerate').onclick=async()=>{
  const ticket=++revision,worksheet=requestId;$('trajectoryError').textContent='';let failed=false;
  try{
   const o=form();if(!o.name.trim()||o.name.trim().length>80)throw Error('Use a trajectory name of 1–80 characters.');
   const spec={...o};if(o.kind==='sequence')spec.initial=JSON.parse(o.state);
   capture();player?.pause();setBusy(true,'Generating in background…');
   await client.run({expressions:rows.map(r=>({text:r.text,type:r.type??'expression'})),datasets,trajectory:spec},{
    onResult:event=>{if(ticket!==revision||event.kind!=='trajectory')return;if(o.kind!=='gbm'&&worksheet!==requestId){failed=true;$('trajectoryError').textContent='The worksheet changed. Generate paths again.';return;}if(event.result.error){failed=true;$('trajectoryError').textContent=event.result.error;return;}try{accept(event.result);}catch(e){failed=true;$('trajectoryError').textContent=e.message;}},
    onDone:()=>{if(ticket===revision)setBusy(false,failed?'Generation failed':'Ready · press Play to animate');},
    onCancelled:()=>{if(ticket===revision)setBusy(false,'Generation cancelled');},
    onError:e=>{if(ticket===revision){$('trajectoryError').textContent=e.message;setBusy(false,'Generation failed');}}
   });
  }catch(e){if(ticket===revision){$('trajectoryError').textContent=e.message;setBusy(false,'Check trajectory settings');}}
 };
 $('trajectoryCancel').onclick=()=>{revision++;client.cancel();setBusy(false,'Generation cancelled');};
 $('trajectoryPlay').onclick=()=>{try{current();if(player.playing)player.pause();else player.play();}catch(e){$('trajectoryError').textContent=e.message;}};
 $('trajectoryReset').onclick=()=>player?.seek(0);$('trajectoryEnd').onclick=()=>player?.seek(report.frames-1);$('trajectoryScrub').oninput=e=>player?.seek(e.target.value);
 function download(blob,name){const a=document.createElement('a'),url=URL.createObjectURL(blob);a.href=url;a.download=name;document.body.append(a);a.click();a.remove();setTimeout(()=>URL.revokeObjectURL(url),1000);}
 function filename(extension){return (get('name').value.trim().replace(/[\\/:*?"<>|\u0000-\u001f]/g,'_')||'Trajectory')+extension;}
 $('trajectoryCSV').onclick=()=>{try{download(new Blob([TrajectoryTools.csv(current())],{type:'text/csv'}),filename('.csv'));}catch(e){$('trajectoryError').textContent=e.message;}};
 $('trajectoryPNG').onclick=async()=>{try{current();const shown=player,ticket=revision;shown.seek(shown.index);await shown.ready();if(shown!==player||ticket!==revision)return;await Plotly.downloadImage('trajectoryPlot',{format:'png',filename:filename(''),scale:2});}catch(e){$('trajectoryError').textContent=e.message;}};
 $('trajectoryAnimation').onclick=async()=>{const button=$('trajectoryAnimation');try{const data=current(),ticket=revision;button.disabled=true;const response=await fetch('/api/trajectories/export',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({trajectory:data,options:options()})});if(!response.ok)throw Error((await response.json()).error||'Animation export failed.');const blob=await response.blob();if(ticket!==revision)return;download(blob,filename('.html'));}catch(e){$('trajectoryError').textContent=e.message;}finally{button.disabled=false;}};
 $('trajectoryDataset').onclick=async()=>{const ticket=revision,worksheet=requestId;try{
  const data=current();let base=get('name').value.trim().replace(/[^\p{L}\p{N}_]/gu,'_')||'trajectory';if(!/^[\p{L}_]/u.test(base))base='trajectory_'+base;const name=base.slice(0,50)+'_paths';
  const candidate=DatasetTools.validate([...datasets,TrajectoryTools.dataset(data,name,uid())]);
  const response=await fetch('/api/evaluate',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({expressions:rows.map(r=>({text:r.text,type:r.type??'expression'})),datasets:candidate,validate_only:true})});const result=await response.json();if(ticket!==revision||worksheet!==requestId)return;if(!response.ok)throw Error(result.error||'Could not add dataset.');if(result.results.some(r=>r.error?.includes('reserved or already defined')))throw Error('Dataset columns conflict with a worksheet name. Rename the trajectory.');datasets=candidate;renderDatasets();schedule(0);sourceRevision=requestId;$('trajectoryDialog').close();toast('Trajectory values added. Save worksheet to keep them.');
 }catch(e){$('trajectoryError').textContent=e.message;}};
 const examples={
  gbm:{...TrajectoryTools.defaults,name:'GBM ensemble',coordinates:'0'},
  helix:{kind:'parametric',name:'Helix',horizon:4*Math.PI,steps:600,display:'3d',coordinates:'0,1,2',expression:'[cos(t),sin(t),t/4]'},
  rotation:{kind:'sequence',name:'Sequential rotation',state:'[1,0]',update:'[[cos(dt),-sin(dt)],[sin(dt),cos(dt)]] @ s',horizon:4*Math.PI,steps:400,display:'2d',coordinates:'0,1'},
  logistic:{kind:'sequence',name:'Logistic map',state:'[0.2]',update:'[3.8*s[0]*(1-s[0])]',horizon:100,steps:100,display:'time',coordinates:'0'},
  descent:{kind:'sequence',name:'Gradient descent',state:'[3,2]',update:'s - dt*[2*s[0],4*s[1]]',horizon:3,steps:150,display:'2d',coordinates:'0,1'},
  markov:{kind:'sequence',name:'Markov probabilities',state:'[1,0,0]',update:'s @ [[0.9,0.08,0.02],[0.05,0.9,0.05],[0.02,0.08,0.9]]',horizon:50,steps:50,display:'3d',coordinates:'0,1,2'}
 };
 $('trajectoryExample').onchange=e=>{if(!examples[e.target.value])return;reset();fill({...TrajectoryTools.defaults,...examples[e.target.value]});capture();setBusy(false,'Example ready. Generate paths.');e.target.value='';};
 fill(trajectorySettings);window.TrajectoryStudio={open,reset};
})();
