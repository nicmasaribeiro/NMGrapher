/* Surface appearance is independent of function sampling. */
'use strict';
const SurfaceTools=(()=>{
 const scales=['auto','Viridis','Cividis','Plasma','RdBu','Turbo','HSV'];
 const defaults={axes:{x:{title:'',type:'linear',range:null},y:{title:'',type:'linear',range:null},z:{title:'',type:'linear',range:null}},grid:true,background:true,aspect:'auto',zRatio:1,projection:'perspective',drag:'orbit',colorscale:'auto',reverse:false,colorbar:true,colorRange:null,opacity:1,contours:false,floor:false,camera:null,revision:0};
 const copy=o=>JSON.parse(JSON.stringify(o));
 const label=s=>String(s).replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
 function number(n,min,max,name){if(typeof n!=='number'||!Number.isFinite(n)||n<min||n>max)throw Error(`${name} must be between ${min} and ${max}.`);return n;}
 function range(r,name,type='linear'){
  if(r==null)return null;
  if(!Array.isArray(r)||r.length!==2)throw Error(`${name} needs a minimum and maximum.`);
  r=r.map(n=>number(n,-1e100,1e100,name));
  if(r[0]>=r[1])throw Error(`${name}: minimum must be smaller than maximum.`);
  if(type==='log'&&r[0]<=0)throw Error(`${name}: logarithmic limits must be positive.`);
  return r;
 }
 function camera(c){
  if(c==null)return null;
  const out={};
  for(const part of ['eye','center','up']){
   if(!c[part]||typeof c[part]!=='object')throw Error('Camera needs eye, center and up coordinates.');
   out[part]=Object.fromEntries(['x','y','z'].map(k=>[k,number(c[part][k],-1e6,1e6,'Camera coordinate')]));
  }
  if(Math.hypot(...Object.values(out.eye))<1e-8||Math.hypot(...Object.values(out.up))<1e-8)throw Error('Camera eye and up direction must be nonzero.');
  return out;
 }
 function settings(raw){
  if(raw==null)return copy(defaults);
  if(typeof raw!=='object'||Array.isArray(raw))throw Error('Invalid surface settings.');
  const o=copy(defaults);
  for(const name of ['grid','background','reverse','colorbar','contours','floor']){if(raw[name]!==undefined){if(typeof raw[name]!=='boolean')throw Error(`Invalid surface ${name}.`);o[name]=raw[name];}}
  for(const [name,values] of Object.entries({aspect:['auto','data','cube','manual'],projection:['perspective','orthographic'],drag:['orbit','pan'],colorscale:scales})){
   if(raw[name]!==undefined){if(!values.includes(raw[name]))throw Error(`Invalid surface ${name}.`);o[name]=raw[name];}
  }
  for(const axis of ['x','y','z']){
   const a=raw.axes?.[axis]??{};
   if(a.title!==undefined&&(typeof a.title!=='string'||a.title.length>80))throw Error('Axis labels support up to 80 characters.');
   const type=a.type??'linear';if(!['linear','log'].includes(type))throw Error('Choose linear or log axes.');
   o.axes[axis]={title:a.title??'',type,range:range(a.range,axis.toUpperCase()+' display range',type)};
  }
  o.zRatio=number(raw.zRatio??1,.1,10,'Vertical ratio');o.opacity=number(raw.opacity??1,.1,1,'Opacity');
  o.colorRange=range(raw.colorRange,'Color range');o.camera=camera(raw.camera);
  o.revision=number(raw.revision??0,0,1e12,'Camera revision');
  return o;
 }
 function preset(name){
  const eyes={iso:[1.5,1.5,1.25],top:[0,0,2.5],front:[0,-2.5,0],side:[2.5,0,0]};
  const eye=eyes[name];if(!eye)throw Error('Unknown camera preset.');
  return {eye:{x:eye[0],y:eye[1],z:eye[2]},center:{x:0,y:0,z:0},up:name==='top'?{x:0,y:1,z:0}:{x:0,y:0,z:1}};
 }
 function apply(data,layout,raw){
  const o=settings(raw),surfaces=data.filter(t=>t.type==='surface');
  if(!surfaces.length)return {data,layout};
  const scene={...layout.scene},names={};
  for(const axis of ['x','y','z']){
   const a=o.axes[axis],existing=scene[axis+'axis']||{};
   // A log axis cannot represent zero or negative coordinates. Never silently discard them.
   if(a.type==='log')for(const t of surfaces){const values=(t[axis]||[]).flat(Infinity).filter(v=>typeof v==='number'&&Number.isFinite(v));if(values.some(v=>v<=0))throw Error(`${axis.toUpperCase()} log axis requires positive plotted values. Change the input range or use a linear axis.`);}
   const title=a.title?label(a.title):(existing.title?.text||axis);
   names[axis]=title;
   scene[axis+'axis']={...existing,title:{text:title,font:{size:14}},type:a.type,showgrid:o.grid,showbackground:o.background,showline:true,linewidth:2,ticks:'outside',tickfont:{size:11},nticks:7,exponentformat:'power',showexponent:'all',zeroline:a.type==='linear',autorange:!a.range};
   delete scene[axis+'axis'].range;
   if(a.range)scene[axis+'axis'].range=a.type==='log'?a.range.map(Math.log10):a.range.slice();
  }
  scene.aspectmode=o.aspect;
  if(o.aspect==='manual')scene.aspectratio={x:1,y:1,z:o.zRatio};else delete scene.aspectratio;
  scene.dragmode=o.drag;
  scene.camera={...(o.camera||preset('iso')),projection:{type:o.projection}};
  scene.uirevision='surface-camera-'+o.revision;
  let sharedColors=null;
  if(surfaces.length>1&&!o.colorRange){
   let min=Infinity,max=-Infinity;
   for(const t of surfaces)for(const row of t.surfacecolor||t.z||[])for(const v of row||[])if(typeof v==='number'&&Number.isFinite(v)){min=Math.min(min,v);max=Math.max(max,v);}
   if(Number.isFinite(min)&&max>min)sharedColors=[min,max];
  }
  const traces=data.map(t=>{
   if(t.type!=='surface')return t;
   const scale=o.colorscale==='auto'?(t.colorscale==='HSV'?'HSV':'Viridis'):o.colorscale;
   const next={...t,colorscale:scale,reversescale:o.reverse,showscale:o.colorbar&&t===surfaces[0],opacity:o.opacity,
    colorbar:{...t.colorbar,title:{text:names.z},thickness:15,len:.78,x:1.02},
    contours:{x:{show:o.contours,usecolormap:true},y:{show:o.contours,usecolormap:true},z:{show:o.contours||o.floor,usecolormap:true,project:{z:o.floor}}},
    hovertemplate:`${names.x}: %{x:.6g}<br>${names.y}: %{y:.6g}<br>${names.z}: %{z:.6g}<extra>%{fullData.name}</extra>`};
   if(o.colorRange||sharedColors){next.cauto=false;[next.cmin,next.cmax]=o.colorRange||sharedColors;}
   return next;
  });
  return {data:traces,layout:{...layout,scene,margin:{l:20,r:o.colorbar?100:25,b:30,t:layout.title?55:30}}};
 }
 return {settings,apply,preset,camera,defaults,scales};
})();
if(typeof module!=='undefined')module.exports=SurfaceTools;
