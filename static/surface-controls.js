'use strict';
(()=>{
 const ids=['grid','background','aspect','zRatio','projection','drag','colorscale','reverse','colorbar','opacity','contours','floor'];
 const get=n=>$('surfaceDisplay_'+n);
 function fill(o){
  for(const n of ids){const el=get(n);if(el.type==='checkbox')el.checked=o[n];else el.value=o[n];}
  for(const a of ['x','y','z']){get(a+'Title').value=o.axes[a].title;get(a+'Type').value=o.axes[a].type;get(a+'Min').value=o.axes[a].range?.[0]??'';get(a+'Max').value=o.axes[a].range?.[1]??'';}
  get('colorMin').value=o.colorRange?.[0]??'';get('colorMax').value=o.colorRange?.[1]??'';get('camera').value='keep';
 }
 function limits(min,max){if(min.trim()===''&&max.trim()==='')return null;if(min.trim()===''||max.trim()==='')throw Error('Enter both limits, or leave both blank for automatic limits.');return [Number(min),Number(max)];}
 function read(){
  const raw={...surfaceSettings,axes:{}};
  for(const n of ids){const el=get(n);raw[n]=el.type==='checkbox'?el.checked:el.type==='number'?Number(el.value):el.value;}
  for(const a of ['x','y','z'])raw.axes[a]={title:get(a+'Title').value.trim(),type:get(a+'Type').value,range:limits(get(a+'Min').value,get(a+'Max').value)};
  raw.colorRange=limits(get('colorMin').value,get('colorMax').value);
  if(get('camera').value!=='keep')raw.camera=SurfaceTools.preset(get('camera').value);
  raw.revision++;
  return SurfaceTools.settings(raw);
 }
 function apply(o){
  // Validate against the current surface before saving. No computation request is made.
  SurfaceTools.apply($('plot').data||[],$('plot').layout||{},o);
  surfaceSettings=o;saveLocal();drawPlot();
 }
 $('surfaceControlsBtn').onclick=()=>{fill(surfaceSettings);$('surfaceDisplayError').textContent='';$('surfaceDisplayDialog').showModal();};
 $('surfaceDisplayForm').onsubmit=e=>{e.preventDefault();try{apply(read());$('surfaceDisplayDialog').close();}catch(error){$('surfaceDisplayError').textContent=error.message;}};
 $('surfaceDisplayDefaults').onclick=()=>{const o=SurfaceTools.settings(null);o.revision=surfaceSettings.revision+1;fill(o);try{apply(o);$('surfaceDisplayError').textContent='Display defaults restored.';}catch(e){$('surfaceDisplayError').textContent=e.message;}};
 window.SurfaceControls={capture(e){
  if(!$('plot').data?.some(t=>t.type==='surface')||view==='quantum')return;
  if(e['scene.camera']){try{surfaceSettings.camera=SurfaceTools.camera(e['scene.camera']);saveLocal();}catch{}}
 },reset(){const o={...surfaceSettings,camera:SurfaceTools.preset('iso'),revision:surfaceSettings.revision+1};apply(o);}};
 async function status(){
  const button=$('computeMode');button.disabled=true;button.textContent='Checking workers…';
  try{const response=await fetch('/api/compute/status',{cache:'no-store'}),result=await response.json();if(!response.ok)throw Error(result.error||'Worker status unavailable.');button.textContent=result.mode==='celery'?`Celery · ${result.workers} slots · ${result.nodes} workers`:`Local · ${result.workers} slots`;button.title=result.notice||'Click to refresh worker status';if(result.notice)toast(result.notice);}
  catch(e){button.textContent='Workers unavailable';button.title=e.message;toast(e.message);}
  finally{button.disabled=false;}
 }
 $('computeMode').onclick=status;status();
})();
