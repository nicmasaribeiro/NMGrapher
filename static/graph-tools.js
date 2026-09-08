'use strict';
(() => {
 const types={
  function:{label:'Cartesian curve · y = f(x)',fields:{y:'y(x)'},defaults:{y:'sin(x)'},range:[-6,6]},
  parametric:{label:'Parametric curve · (x(t), y(t))',fields:{x:'x(t)',y:'y(t)'},defaults:{x:'2*cos(t)',y:'sin(t)'},range:[0,2*Math.PI]},
  polar:{label:'Polar curve · r(θ)',fields:{r:'Radius r(θ)'},defaults:{r:'2*cos(3*θ)'},parameter:'θ',range:[0,2*Math.PI]},
  parametric3d:{label:'3D parametric curve',fields:{x:'x(t)',y:'y(t)',z:'z(t)'},defaults:{x:'cos(t)',y:'sin(t)',z:'t/4'},range:[0,4*Math.PI]},
  implicit:{label:'Implicit curve · F(x,y) = 0',fields:{expression:'Equation or zero-level expression'},defaults:{expression:'x^2+y^2=4'},grid:true},
  surface:{label:'3D surface · z = f(x,y)',fields:{z:'z(x,y)'},defaults:{z:'sin(x)*cos(y)'},grid:true},
  contour:{label:'Contour map · f(x,y)',fields:{z:'f(x,y)'},defaults:{z:'x^2+y^2'},grid:true},
  scatter:{label:'Scatter plot',fields:{x:'X values (blank = row index)',y:'Y values'},defaults:{x:'[0,1,2,3]',y:'[1,3,2,4]'},data:true},
  line:{label:'Line chart',fields:{x:'X values (blank = row index)',y:'Y values'},defaults:{x:'[0,1,2,3]',y:'[1,3,2,4]'},data:true},
  bar:{label:'Bar chart',fields:{x:'X values (blank = row index)',y:'Bar heights'},defaults:{x:'[1,2,3,4]',y:'[3,7,4,6]'},data:true},
  probability:{label:'Probability distribution',fields:{expression:'Distribution name or constructor'},defaults:{expression:'normal(0,1)'},range:[-4,4]},
  histogram:{label:'Histogram',fields:{values:'Values'},defaults:{values:'[1,1,2,2,2,3,4,5]'},data:true}
 };
 const is3d=g=>['surface','parametric3d'].includes(g.type);
 function fresh(type,id,color='#2864d7'){
  const config=types[type];if(!config)throw Error('Choose a supported graph type.');
  return {id,type,name:config.label.split(' · ')[0],color,visible:true,parameter:config.parameter||'t',range:config.range?[...config.range]:[-5,5],yrange:[-5,5],samples:400,bins:20,probability_mode:'density',x:'',y:'',z:'',r:'',expression:'',values:'',...config.defaults};
 }
 function validate(items){
  if(!Array.isArray(items)||items.length>12)throw Error('Use at most 12 saved graphs.');
  const ids=new Set();return items.map(g=>{
   if(!g||!Object.hasOwn(types,g.type))throw Error('Choose a supported graph type.');
   if(typeof g.id!=='string'||!/^[a-z0-9_-]{1,80}$/i.test(g.id)||ids.has(g.id)||['2d','3d'].includes(g.id))throw Error('Graph IDs must be unique.');ids.add(g.id);
   if(typeof g.name!=='string'||!g.name.trim()||g.name.trim().length>80)throw Error('Graph names need 1–80 characters.');
   if(typeof g.color!=='string'||!/^#[0-9a-f]{6}$/i.test(g.color))throw Error('Choose a graph color.');
   if(typeof g.visible!=='boolean')throw Error('Invalid graph visibility.');
   const out=fresh(g.type,g.id,g.color);out.name=g.name.trim();out.visible=g.visible;
   for(const key of ['x','y','z','r','expression','values']){
    if(g[key]!==undefined&&(typeof g[key]!=='string'||g[key].length>1200))throw Error('Graph formulas support at most 1200 characters.');
    out[key]=g[key]?.trim()??out[key];
   }
   for(const key of Object.keys(types[g.type].fields))if(key!=='x'&&!out[key])throw Error('Complete the graph formula fields.');
   if(!types[g.type].data){
    for(const key of ['range','yrange']){
     const r=g[key]??out[key];
     if(!Array.isArray(r)||r.length!==2||r.some(v=>typeof v!=='number'||!Number.isFinite(v)||Math.abs(v)>1e6)||r[1]-r[0]<1e-6||r[1]-r[0]>1e6)throw Error('Use increasing finite ranges within ±1,000,000, with width 0.000001–1,000,000.');
     out[key]=[...r];
    }
    if(typeof g.parameter!=='string'||g.parameter.length>40||!g.parameter.trim())throw Error('Enter a parameter name.');out.parameter=g.parameter.trim();
    if(!Number.isInteger(g.samples)||g.samples<50||g.samples>1000)throw Error('Use 50–1000 samples.');out.samples=g.samples;
   }
   if(g.type==='histogram'){if(!Number.isInteger(g.bins)||g.bins<1||g.bins>100)throw Error('Use 1–100 histogram bins.');out.bins=g.bins;}
   if(g.probability_mode!==undefined&&!['density','cdf'].includes(g.probability_mode))throw Error('Choose density/mass or cumulative probability.');out.probability_mode=g.probability_mode??'density';
   return out;
  });
 }
 const safeText=s=>String(s).replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;');
 function plot(graphs,results,selection='2d'){
  const three=selection==='3d'||is3d(graphs.find(g=>g.id===selection)||{});
  const group=selection==='2d'||selection==='3d';
  const selected=graphs.filter(g=>g.visible&&(group?is3d(g)===three:g.id===selection));
  const traces=[];
  for(const g of selected){
   const r=results.find(r=>r.id===g.id);if(!r||r.error||r.hidden)continue;
   const base={name:safeText(g.name),showlegend:true,connectgaps:false};
   const line={color:g.color,width:2.5},marker={color:g.color,size:6};
   if(g.type==='probability'){
    traces.push({...base,type:r.discrete&&g.probability_mode!=='cdf'?'bar':'scatter',mode:'lines',x:r.x,y:r.y,marker,line:{...line,...(r.discrete&&g.probability_mode==='cdf'?{shape:'hv'}:{})}});
   }else if(['function','parametric','polar','line','scatter','parametric3d'].includes(g.type)){
    traces.push({...base,type:three?'scatter3d':'scatter',mode:g.type==='scatter'?'markers':g.type==='line'?'lines+markers':'lines',x:r.x,y:r.y,...(three?{z:r.z}:{}),line,marker,...(r.parameter?{customdata:r.parameter,hovertemplate:'parameter: %{customdata:.5g}<br>x: %{x:.5g}<br>y: %{y:.5g}'+(three?'<br>z: %{z:.5g}':'')+'<extra>%{fullData.name}</extra>'}:{})});
   }else if(['bar','histogram'].includes(g.type)){
    traces.push({...base,type:'bar',x:r.x,y:r.y,marker,opacity:.8,...(g.type==='histogram'?{width:r.widths}:{}),hovertemplate:'x: %{x:.6g}<br>value: %{y:.6g}<extra>%{fullData.name}</extra>'});
   }else if(g.type==='surface'){
    traces.push({...base,type:'surface',x:r.x,y:r.y,z:r.z,colorscale:[[0,g.color],[1,g.color]],showscale:false,opacity:selected.filter(g=>g.type==='surface').length>1?.7:1});
   }else{
    traces.push({...base,type:'contour',x:r.x,y:r.y,z:r.z,colorscale:[[0,g.color],[1,g.color]],showscale:false,line:{color:g.color,width:2},...(g.type==='implicit'?{autocontour:false,contours:{start:0,end:0,size:1,coloring:'lines'}}:{ncontours:16,contours:{coloring:'lines'}})});
   }
  }
  const layout={margin:{l:48,r:24,t:24,b:50},showlegend:true,legend:{orientation:'h',y:-.15},hovermode:'closest',barmode:'group',uirevision:'created-'+selection,dragmode:three?'orbit':'pan'};
  if(!group&&selected.length){layout.title={text:safeText(selected[0].name)};layout.margin.t=50;}
  if(three)layout.scene={xaxis:{title:{text:'x'}},yaxis:{title:{text:'y'}},zaxis:{title:{text:'z'}},aspectmode:'data'};
  else {layout.xaxis={title:{text:'x'},autorange:true,zeroline:true};layout.yaxis={title:{text:'y'},autorange:true,zeroline:true};
   if(selected.length&&selected.every(g=>['polar','parametric','implicit'].includes(g.type)))Object.assign(layout.yaxis,{scaleanchor:'x',scaleratio:1});
   if(selected.length===1&&selected[0].type==='histogram'){layout.xaxis.title.text='Value';layout.yaxis.title.text='Count';}
  }
  return {data:traces,layout};
 }
 const api={types,is3d,fresh,validate,plot,label:safeText};if(typeof window!=='undefined')window.GraphTools=api;if(typeof module!=='undefined')module.exports=api;
})();
