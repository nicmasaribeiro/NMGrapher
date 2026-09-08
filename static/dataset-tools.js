'use strict';
(() => {
 const limits={datasets:8,rows:10000,columns:32,cells:50000,bytes:1048576};
 function name(value){
  if(typeof value!=='string'||value.length<1||value.length>80)throw Error('Use dataset and column names of 1–80 characters.');
  const sub='₀₁₂₃₄₅₆₇₈₉ₐₑₕᵢⱼₖₗₘₙₒₚᵣₛₜᵤᵥₓᵦᵧᵨᵩᵪ',plain='0123456789aehijklmnoprstuvxβγρφχ';
  value=value.trim().replace(new RegExp('['+sub+']+','g'),m=>'_'+[...m].map(c=>plain[sub.indexOf(c)]).join('')).replace(/_\{([^{}]+)\}/g,(_,s)=>'_'+s.trim());
  if(/[⁰¹²³⁴⁵⁶⁷⁸⁹⁺⁻⁽⁾ⁿⁱ]/u.test(value))throw Error('Use letters, subscripts, digits, and underscores for dataset names.');
  value=GreekInput.normalize(value.normalize('NFKC').replace(/ς/g,'σ'));
  if(!/^[\p{L}_][\p{L}\p{Nd}_]*$/u.test(value)||['False','None','True','and','as','assert','async','await','break','class','continue','def','del','elif','else','except','finally','for','from','global','if','import','in','is','nonlocal','not','or','pass','raise','return','try','while','with','yield'].includes(value))throw Error('Use letters, digits, and underscores in dataset names.');
  return value;
 }
 function validate(items){
  if(!Array.isArray(items)||items.length>limits.datasets)throw Error('Use at most 8 datasets.');
  const ids=new Set(),names=new Set(),bindings=new Set();let cells=0;
  return items.map(d=>{
   if(!d||typeof d!=='object')throw Error('Invalid dataset.');
   const normalized=name(d.name);if(names.has(normalized))throw Error('Dataset names must be unique.');names.add(normalized);
   if(typeof d.id!=='string'||!d.id||d.id.length>80||ids.has(d.id))throw Error('Dataset IDs must be unique.');ids.add(d.id);
   if(!Array.isArray(d.columns)||!d.columns.length||d.columns.length>32)throw Error('Use 1–32 columns per dataset.');
   let length=null;const keys=new Set();
   const columns=d.columns.map(c=>{
    if(!c||typeof c!=='object')throw Error('Invalid column.');const key=name(c.name),binding=normalized+'_'+key;
    if(keys.has(key)||bindings.has(binding))throw Error('Dataset column names must be unique.');keys.add(key);bindings.add(binding);
    if(!Array.isArray(c.values)||!c.values.length||c.values.length>limits.rows||(length!==null&&length!==c.values.length))throw Error('Use equal-length columns with up to 10,000 rows.');
    length=c.values.length;cells+=length;if(cells>limits.cells)throw Error('Use at most 50,000 dataset cells per worksheet.');
    if(c.values.some(v=>v!==null&&(typeof v!=='number'||!Number.isFinite(v)||Math.abs(v)>1e100))||!c.values.some(v=>v!==null))throw Error('Columns need finite real numbers; missing cells use null.');
    if(c.label!==undefined&&(typeof c.label!=='string'||c.label.length>120))throw Error('Column labels can contain up to 120 characters.');
    return {name:key,label:c.label??key,values:[...c.values]};
   });
   const x=d.x==null?null:name(d.x),y=(d.y??[columns.at(-1).name]);
   if(!Array.isArray(y)||!y.length||y.length>8)throw Error('Choose 1–8 Y columns.');const ys=y.map(name);
   if((x!==null&&!keys.has(x))||ys.some(k=>!keys.has(k))||new Set(ys).size!==ys.length)throw Error('Plot columns must belong to the dataset.');
   const style=d.style??'markers';if(!['markers','lines','lines+markers'].includes(style))throw Error('Choose a supported plot style.');
   if(d.visible!==undefined&&typeof d.visible!=='boolean')throw Error('Invalid dataset visibility.');
   return {id:d.id,name:normalized,columns,x,y:ys,style,visible:d.visible!==false};
  });
 }
 function traces(items,colors){
  return items.flatMap((d,i)=>{
   if(!d.visible)return [];
   const sourceX=d.x===null?d.columns[0].values.map((_,k)=>k):d.columns.find(c=>c.name===d.x).values;
   return d.y.map((key,j)=>{const sourceY=d.columns.find(c=>c.name===key).values;return {type:'scatter',mode:d.style,connectgaps:false,x:sourceX.map((v,k)=>v===null||sourceY[k]===null?null:v),y:sourceY.map((v,k)=>v===null||sourceX[k]===null?null:v),name:d.name+'_'+key,marker:{size:6,color:colors[(i+j)%colors.length]},line:{width:1.6,color:colors[(i+j)%colors.length]},hovertemplate:'x: %{x:.6g}<br>y: %{y:.6g}<extra>%{fullData.name}</extra>'};});
  });
 }
 function fit(items){
  const plots=traces(items,['#2864d7']),xs=[],ys=[];
  for(const plot of plots)for(let i=0;i<plot.x.length;i++)if(plot.x[i]!==null&&plot.y[i]!==null){xs.push(plot.x[i]);ys.push(plot.y[i]);}
  if(!xs.length)throw Error('No complete X/Y pairs to plot.');
  const range=values=>{let lo=Infinity,hi=-Infinity;for(const v of values){lo=Math.min(lo,v);hi=Math.max(hi,v);}if(lo<-1e6||hi>1e6||hi-lo>1e6)throw Error('This data exceeds the graph range. Scale it in an expression with points(x_column, y_column/scale).');const pad=Math.min(Math.max((hi-lo)*.05,.5),(1e6-(hi-lo))/2);return [Math.max(-1e6,lo-pad),Math.min(1e6,hi+pad)];};
  return [...range(xs),...range(ys)];
 }
 const api={limits,name,validate,traces,fit};if(typeof window!=='undefined')window.DatasetTools=api;if(typeof module!=='undefined')module.exports=api;
})();
