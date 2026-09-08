'use strict';
const $ = id => document.getElementById(id);
const colors = ['#2864d7','#dd6b35','#8a4dc2','#169582','#cf4166','#a57b17'];
const examples = {
 probability:['D=normal(0,1)','pdf(D,x)','cdf(D,x)','N=poisson(4)','pmf(N,2)','B=binomial(10,0.5)','prob(B,3,7)','Q=boltzmann([0,1,2],1)','probabilities(Q)','expected_energy(Q)'],
 linear_algebra:['A = [[2,1],[1,3]]','λ = eigvals(A)','V = eigvecs(A)','A@V - V@diag(λ)','B = [[1,2,3],[2,4,6]]','nullspace(B)','svdU(B) @ svdS(B) @ svdVh(B)'],
 integral_functions:['S_1(x) = x','Q_1(t,x,φ) = -t*x + i*φ','π_1(t,θ,φ) = ∫_{0}^{θ} (S_1(x)*exp(Q_1(t,x,φ))) dx','π_1(0,2,0)','C(t) = t^3','d/dt(C(t))','F(x) = ∫ (sin(x)) dx'],
 vector_calculus:['F(x,y,z) = [-y, x, z^2]','divergence(F(x,y,z), [x,y,z], [1,2,3])','curl(F(x,y,z), [x,y,z], [1,2,3])','jacobian(F(x,y,z), [x,y,z], [1,2,3])'],
 energy_calculus:['E(x,y,z) = x^2 + 2*y^2 + 3*z^2 + x*y','g(x,y,z) = grad(E(x,y,z), [x,y,z])','hessian(E(x,y,z), [x,y,z], [1,2,3])','directional(E(x,y,z), [x,y,z], [1,0,0], [1,2,3])'],
 n_vars:['f(x, y, z, t) = sin(x) * cos(y) + z^2 + t','f(1, 2, 3, 4)','v(a, b, c, d) = [a+b, c*d]','M(a, b, c, d) = [[a, b], [c, d]]','alpha_1 = 2','omega(t) = alpha_1 * sin(t)'],
 array_functions:['φ_1 = [1, i]','w(t) = exp(i*t)','Φ_1(t) = φ_1 * w(t)','v(t) = [cos(t), sin(t)]','R(t) = [[cos(t), -sin(t)], [sin(t), cos(t)]]','q(t) = R(t) @ v(t)','q(0)'],
 qubit:['θ = 1.5707963267948966','φ = 0','ψ = blochstate(θ, φ)','hadamard() @ ψ','probabilities(ψ)','expect(pauliZ(), ψ)','density(ψ)'],
 bell:['ψ = CNOT() @ tensor(hadamard() @ ket0(), ket0())','probabilities(ψ)','ρ_0 = reduced(ψ, 0)','ρ_1 = reduced(ψ, 1)','entropy(ρ_0)'],
 products:['A = [[1, 2], [3, 4]]','v = [2, 1]','A * v','v @ A','dot(v, v)','outer(v, v)','tensor(v, v)','bra([1, i]) @ col([1, i])'],
 calculus:['f(x) = sin(x)','d_1(x) = diff(f(x), x)','d_2(x) = diff(f(x), x, x, 2)','F(x) = integrate(f(t), t, 0, x)','integrate(f(t), t, 0, pi)'],
 partials:['f(x, y) = exp(-(x^2+y^2)/4)','d_x(x,y) = diff(f(x,y),x)','d_y(x,y) = diff(f(x,y),y)','I(y) = integrate(f(x,y),x,-2,2)'],
 two_vars:['α_1 = 1','f₁(x₁, x₂) = α_1 * exp(-(x₁² + x₂²)/4) * cos(x₁) * sin(x₂)','f_1(1, 2)','g(x) = f_1(x, 1)','ψ(x, y) = exp(i*x) * cos(y)'],
 greek:['α = 2','β = 3','ζ = α + β*i','ψ(θ) = α * exp(i*θ)','Α = [[α, i], [-i, β]]','H(Α)','eigvals(Α)'],
 complex:['z = 2 + 3i','sqrt(-1)','roots(1, 5)','f(t) = 2 * exp(i*t)'],
 domain:['f(z) = z^2 - 1','g(z) = log(z)','h(z) = 1/z'],
 hermitian:['A = [[2, i], [-i, 3]]','H(A)','eigvals(A)','U = expm(i * A)','H(U) @ U','isunitary(U)'],
 basics:['a = 2','y = a * sin(x)','y = 0.15 * x^2 - 3','A = [[2, 1], [1, 3]]','det(A)'],
 matrix:['A = [[2, 1], [1, 3]]','B = [[1, -1], [0, 2]]','A @ B','inv(A)','eigvals(A)','solve(A, [1, 2])'],
 geometry:['r = 3','x^2 + y^2 = r^2','y = sin(x)','y < 0.3 * x - 2','x = -4'],
 wavelet:['s = 1','b = 0','f(x) = (1 - ((x-b)/s)^2) * exp(-((x-b)/s)^2 / 2) / sqrt(s)','y = exp(-x^2 / 2)'],
 ctmc:['t = 2','Q = [[-0.3, 0.2, 0.1], [0.1, -0.3, 0.2], [0.2, 0.1, -0.3]]','P = expm(t * Q)','p = [[0, 1, 0]]','p @ P','trace(Q)']
};
let waveletSettings=WaveletTools.settings(null);
let graphs=[],graphResults=[],graphSelection='2d',graphEdit=null,graphRevision=0;
let datasets=[],rows=[],results=[],resultIds=[],view='graph',bounds=[-10,10,-7,7],selectedMatrix='',requestId=0,timer,rendering=false,matrixEdit=null,gridRows=2,gridCols=2,component='real',functionEdit=null;
let symbolTarget=null;
let dragState=null,dragFrame=0;
document.addEventListener('focusin',e=>{if(e.target.matches('.expression textarea, #matrixGrid input, #matrixName, #functionForm input, #functionBody, #calculusExpression, #calculusForm input:not([type=checkbox]), #qubitAlpha, #qubitBeta, #qubitName'))symbolTarget=e.target;});
const uid=()=>Math.random().toString(36).slice(2,11);
const newRow=(text='',i=rows.length)=>({id:uid(),text:GreekInput.normalize(text),color:colors[i%colors.length],plotName:'',visible:true,min:-5,max:5,plotComponent:'all',plotSlice:null});
function toast(message){$('toast').textContent=message;$('toast').hidden=false;clearTimeout(toast.timer);toast.timer=setTimeout(()=>$('toast').hidden=true,3500);}
function fmt(v){return typeof v==='number'?Number(v.toPrecision(7)).toString():String(v);}
function worksheetData(){return {version:5,rows,datasets,graphs,graphSelection,wavelet_settings:waveletSettings,bounds,view,component,curve_range:[Number($('parameterMin').value),Number($('parameterMax').value)]};}
function restoreViewOptions(data){
 waveletSettings=WaveletTools.settings(data.wavelet_settings);
 graphs=GraphTools.validate(data.graphs??[]);graphResults=[];graphSelection=['2d','3d',...graphs.map(g=>g.id)].includes(data.graphSelection)?data.graphSelection:'2d';renderGraphs();
 datasets=DatasetTools.validate(data.datasets??[]);renderDatasets();
 component=['real','imag','magnitude','phase'].includes(data.component)?data.component:'real';
 if(view==='domain'&&!['phase','magnitude'].includes(component))component='phase';
 const range=data.curve_range;
 if(Array.isArray(range)&&range.length===2&&range.every(v=>Number.isFinite(v)&&Math.abs(v)<=1e4)&&range[1]>range[0]){$('parameterMin').value=range[0];$('parameterMax').value=range[1];}
 else{$('parameterMin').value=0;$('parameterMax').value=2*Math.PI;}
}
function saveLocal(){try{localStorage.setItem('matrix-graph-v1',JSON.stringify(worksheetData()));saveLocal.warned=false;}catch{if(!saveLocal.warned){toast('Browser storage is full. Use Save worksheet to keep your data.');saveLocal.warned=true;}}}
function validateWorksheet(data){
 if(!data || !Array.isArray(data.rows) || data.rows.length>40)throw Error('The file must contain at most 40 expression rows.');
 return data.rows.map((r,i)=>{if(!r || typeof r.text!=='string' || r.text.length>1200)throw Error('Invalid expression in worksheet.');if(r.plotName!==undefined&&(typeof r.plotName!=='string'||r.plotName.length>80))throw Error('Plot names support at most 80 characters.');return {...newRow(r.text,i),plotName:r.plotName?.trim()||'',...(typeof r.color==='string'&&/^#[0-9a-f]{6}$/i.test(r.color)?{color:r.color}:{}),plotSlice:validPlotSlice(r.plotSlice)?r.plotSlice:null,plotComponent:Number.isInteger(r.plotComponent)&&r.plotComponent>=0&&r.plotComponent<1024?r.plotComponent:'all',visible:r.visible!==false,min:Number.isFinite(r.min)?r.min:-5,max:Number.isFinite(r.max)?r.max:5};});
}
function loadExample(name){if(!examples[name])return;graphs=[];graphResults=[];renderGraphs();rows=examples[name].map(newRow);if(name==='qubit'){rows[0].min=0;rows[0].max=Math.PI;rows[1].min=0;rows[1].max=2*Math.PI;}if(name==='wavelet'){rows[0].min=0.1;rows[0].max=4;}if(name==='ctmc'){rows[0].min=0;rows[0].max=20;}view=['qubit','bell'].includes(name)?'quantum':name==='ctmc'||name==='hermitian'?'heatmap':['complex','greek'].includes(name)?'complex':name==='domain'?'domain':['two_vars','partials','n_vars'].includes(name)?'surface':'graph';if(view==='domain')component='phase';if(view==='surface')component='real';selectedMatrix=['ctmc','qubit'].includes(name)?rows[2].id:name==='bell'?rows[0].id:'';bounds=['complex','domain','hermitian','greek','two_vars','calculus','partials'].includes(name)?[-4,4,-3,3]:[-10,10,-7,7];renderRows();schedule(0);}
function addExpression(text=''){if(rows.length>=40){toast('Maximum 40 expressions per worksheet.');return;}rows.push(newRow(text));renderRows();schedule(0);$('expressions').lastElementChild.querySelector('textarea').focus();}
function renderRows(){
 const prior=new Map(resultIds.map((id,i)=>[id,results[i]]));results=rows.map(row=>{const r=prior.get(row.id);return r&&r.text===row.text.trim()?r:{kind:'empty',text:row.text.trim()};});resultIds=rows.map(row=>row.id);
 const container=$('expressions');container.replaceChildren();$('rowCount').textContent=rows.length;
 rows.forEach((row,index)=>{
  const el=document.createElement('article');el.className='expression';el.dataset.id=row.id;el.style.setProperty('--row-color',row.color);
  const handle=document.createElement('button');handle.type='button';handle.className='drag-handle';handle.textContent='⋮⋮';handle.title='Drag to reorder · arrow keys move';handle.setAttribute('aria-label',`Move equation ${index+1}`);handle.setAttribute('aria-describedby','reorderHelp');handle.onpointerdown=e=>beginRowDrag(e,row.id,handle);handle.onkeydown=e=>{const at=rows.findIndex(r=>r.id===row.id);let to;if(e.key==='ArrowUp')to=at-1;else if(e.key==='ArrowDown')to=at+1;else if(e.key==='Home')to=0;else if(e.key==='End')to=rows.length-1;else return;e.preventDefault();moveRow(row.id,to);};el.append(handle);
  const toggle=document.createElement('button');toggle.className='color-toggle'+(row.visible?'':' off');toggle.title='Show or hide plot';toggle.setAttribute('aria-label',`Show expression ${index+1}`);toggle.setAttribute('aria-pressed',String(row.visible));toggle.onclick=()=>{row.visible=!row.visible;toggle.classList.toggle('off',!row.visible);toggle.setAttribute('aria-pressed',String(row.visible));saveLocal();drawPlot();};el.append(toggle);
  const n=document.createElement('span');n.className='row-number';n.textContent=index+1;el.append(n);
  const top=document.createElement('div');top.className='row-top';const input=document.createElement('textarea');input.value=row.text;input.rows=1;input.spellcheck=false;input.placeholder='Enter an expression…';input.setAttribute('aria-label',`Expression ${index+1}`);
  input.oninput=()=>{row.text=input.value;row.plotComponent='all';row.plotSlice=null;input.style.height='auto';input.style.height=Math.min(160,input.scrollHeight)+'px';renderMath(el.querySelector('.math-preview'),row.text);schedule();};input.onkeydown=e=>{if(e.key==='Enter'&&!e.shiftKey){e.preventDefault();addExpression();}};
  const remove=document.createElement('button');remove.textContent='×';remove.className='remove';remove.title='Delete expression';remove.setAttribute('aria-label',`Delete expression ${index+1}`);remove.onclick=()=>{rows=rows.filter(r=>r.id!==row.id);renderRows();schedule(0);};top.append(input,remove);el.append(top);
  const preview=document.createElement('div');preview.className='math-preview';renderMath(preview,row.text);el.append(preview);
  const result=document.createElement('div');result.className='result';el.append(result);container.append(el);input.style.height=Math.min(160,Math.max(36,input.scrollHeight))+'px';
 });
}
function schedule(delay=280){clearTimeout(timer);requestId++;$('status').textContent='Updating…';timer=setTimeout(evaluate,delay);saveLocal();}
async function evaluate(){
 const id=requestId;const snapshotIds=rows.map(row=>row.id);
 try{
  const post=async (url,payload)=>{const res=await fetch(url,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(payload)});const data=await res.json();if(!res.ok)throw Error(data.error||'Could not calculate.');return data;};
  const [data,created]=await Promise.all([post('/api/evaluate',{datasets,expressions:rows.map(r=>({text:r.text,plot_component:r.plotComponent??'all',plot_slice:r.plotSlice})),bounds,complex_domain:view==='domain',...(view==='complex'?{curve_range:[Number($('parameterMin').value),Number($('parameterMax').value)]}:{})}),graphs.length?post('/api/graphs',{graphs,expressions:rows.map(r=>({text:r.text})),datasets}):Promise.resolve({results:[]})]);
  if(id!==requestId)return;results=data.results;graphResults=created.results;resultIds=snapshotIds;renderResults();renderGraphs();await drawPlot();
  const errors=results.filter(r=>r.error).length+graphResults.filter(r=>r.error).length;$('status').textContent=errors?`${errors} item${errors===1?'':'s'} to check`:'All expressions and graphs updated';
 }catch(e){if(id===requestId){$('status').textContent='Could not update';toast(e.message);}}
}
function renderResults(){
 rows.forEach((row,i)=>{
  const el=document.querySelector(`.expression[data-id="${row.id}"]`);if(!el)return;const box=el.querySelector('.result');box.replaceChildren();const r=results[i];if(!r)return;
  box.className='result'+(r.error?' error':'');if(r.function){const b=document.createElement('button');b.textContent='Edit function';b.className='edit-function';b.onclick=()=>openFunction(i);box.append(b);const calculus=document.createElement('button');calculus.textContent='Calculus';calculus.className='edit-function';calculus.onclick=()=>openCalculus(i);box.append(calculus);if(r.kind==='surface'&&!r.error){const surface=document.createElement('button');surface.className='edit-function';surface.textContent='Surface';surface.onclick=()=>selectView('surface',row.id);box.append(surface);}}if(r.function&&r.function.parameters.length>1)renderSliceControls(box,row,r);if(r.error){const error=document.createElement('div');error.textContent=r.error;box.append(error);return;}
  if(r.kind==='wavelet_transform'){
   const t=r.transform,tag=document.createElement('div');tag.className='result-tag';tag.textContent=`${t.type.toUpperCase()} · ${t.wavelet} · ${t.length} samples · ${t.labels.length} bands/scales`;box.append(tag);
   const source=r.name||r.text;for(const [label,formula] of [['Coefficients',`wavelet_coeffs(${source},0)`],...(t.type==='dwt'?[['Reconstruct',`idwt(${source})`]]:[['Power',`wavelet_power(${source},0)`],['Frequencies',`wavelet_frequencies(${source})`]])]){const b=document.createElement('button');b.className='edit-function';b.textContent=label;b.onclick=()=>addExpression(formula);box.append(b);}
  }else if(r.kind==='distribution'){
   const d=r.distribution,tag=document.createElement('div');tag.className='result-tag';tag.textContent=`${d.family} · ${d.discrete?'discrete':'continuous'} distribution`;box.append(tag);
   const stats=document.createElement('div');stats.className='matrix-summary';stats.textContent=`Mean ${fmt(d.mean)} · variance ${fmt(d.variance)} · std ${fmt(d.std)}`;box.append(stats);
   const b=document.createElement('button');b.className='edit-function';b.textContent='Probability';b.onclick=()=>openProbability(i);box.append(b);
  }else if(r.kind==='series'){
   const tag=document.createElement('div');tag.className='result-tag';tag.textContent=`${r.shape[0]} observations · ${r.count} finite · ${r.missing} missing/undefined`;box.append(tag);
   const values=document.createElement('div');values.className='result-value';values.textContent='['+r.value.map(v=>v===null?'—':fmt(v)).join(', ')+(r.shape[0]>12?', …':'')+']';box.append(values);
  }else if(r.kind==='data_plot'){const tag=document.createElement('div');tag.className='result-tag';tag.textContent='Dataset points · '+r.x.length+' observations';box.append(tag);
  }else if(r.kind==='matrix'&&r.empty_basis){
   const tag=document.createElement('div');tag.className='result-tag';tag.textContent=`${r.shape[0]} × ${r.shape[1]} empty basis · the subspace has dimension zero`;box.append(tag);
  }else if(r.kind==='matrix'){
   const tag=document.createElement('div');tag.className='result-tag';tag.textContent=`${r.shape[0]} × ${r.shape[1]} matrix${r.complex?' · complex':''}`;box.append(tag);
   const grid=document.createElement('div');grid.className='matrix-result';grid.style.gridTemplateColumns=`repeat(${r.shape[1]}, auto)`;r.value.flat().forEach(v=>{const s=document.createElement('span');s.textContent=fmt(v);grid.append(s);});box.append(grid);
   if(r.hermitian||r.unitary){const tag=document.createElement('div');tag.className='result-tag';tag.textContent=[r.hermitian?'Hermitian':'',r.unitary?'Unitary':''].filter(Boolean).join(' · ');box.append(tag);}
   if(r.details){const summary=document.createElement('div');summary.className='matrix-summary';summary.textContent=`det ${fmt(r.details.det)}   ·   trace ${fmt(r.details.trace)}   ·   rank ${r.details.rank}`;box.append(summary);}
   const actions=document.createElement('div');actions.className='matrix-buttons';const lab=document.createElement('button');lab.textContent='Linear algebra';lab.onclick=()=>openLinearAlgebra(i);actions.append(lab);const heat=document.createElement('button');heat.textContent='Heatmap';heat.onclick=()=>selectView('heatmap',row.id);actions.append(heat);
   if(r.shape[0]===2&&r.shape[1]===2&&!r.complex){const b=document.createElement('button');b.textContent='Transform';b.onclick=()=>selectView('transform',row.id);actions.append(b);}
   if(r.name){const edit=document.createElement('button');edit.textContent='Edit grid';edit.onclick=()=>openMatrix(i);actions.append(edit);}box.append(actions);
  }else if(r.kind==='scalar'||r.kind==='vector'){
   const val=document.createElement('div');val.className='result-value';val.textContent=r.kind==='vector'?'['+r.value.map(fmt).join(', ')+']':'= '+fmt(r.value);box.append(val);if(r.kind==='scalar'&&r.complex){const polar=document.createElement('div');polar.className='matrix-summary';polar.textContent=`Magnitude ${fmt(r.magnitude)} · phase ${r.phase===null?'undefined':fmt(r.phase)+' rad'}`;box.append(polar);}
  }else if(r.kind!=='empty'){const tag=document.createElement('span');tag.className='result-tag';tag.textContent=r.kind==='surface'?'Two-input slice · level curves / surface':r.kind==='complex_curve'?'Complex function · solid Re, dashed Im':r.kind==='complex_field'?'Complex input domain':r.kind==='curve'?'Function':r.kind==='implicit'?'Implicit curve':'Shaded region';box.append(tag);}
  if(['curve','complex_curve','surface','complex_field','implicit','inequality','series','data_plot'].includes(r.kind)){
   const label=document.createElement('label');label.className='plot-name-field';label.textContent='Plot name';const input=document.createElement('input');input.maxLength=80;input.value=row.plotName||'';input.placeholder='Optional name for this graph';input.setAttribute('aria-label',`Plot name for equation ${i+1}`);input.oninput=()=>{row.plotName=input.value.trim();saveLocal();};input.onchange=()=>drawPlot();label.append(input);box.append(label);
  }
  if(r.components){
   const label=document.createElement('label');label.className='entry-picker';label.append(`${r.shape.length===1?'Vector '+r.shape[0]:r.shape.join(' × ')+' matrix'} output · plot entry `);
   const select=document.createElement('select');select.setAttribute('aria-label',`Output entry for equation ${i+1}`);
   const all=document.createElement('option');all.value='all';all.textContent=['surface','complex_field'].includes(r.kind)?'First entry':r.component_count>8?'First 8 entries':'All entries';select.append(all);
   for(let k=0;k<r.component_count;k++){const opt=document.createElement('option');opt.value=k;opt.textContent=entryLabel(r.shape,k);select.append(opt);}
   select.value=String(r.selected_component);select.onchange=()=>{row.plotComponent=select.value==='all'?'all':Number(select.value);schedule(0);};label.append(select);box.append(label);
  }
  if(r.quantum){const button=document.createElement('button');button.className='edit-function';button.textContent=r.quantum.qubits===1?'Bloch sphere':'Quantum probabilities';button.onclick=()=>selectView('quantum',row.id);box.append(button);}
  if(r.calculus?.length){const info=r.calculus[r.calculus.length-1];const note=document.createElement('div');note.className='calculus-note';note.textContent=`Numerical ${info.operation} · estimated error ${info.error_estimate===null?'unavailable':Number(info.error_estimate).toExponential(2)}${info.undefined_samples?' · '+info.undefined_samples+' undefined entries':''}${info.evaluations?' · '+info.evaluations+' evaluations':''}${info.variables?' · '+info.variables.join(', '):''}`;box.append(note);}
  const match=row.text.match(/^\s*([\p{L}_][\p{L}\p{N}_]*)\s*=\s*(-?(?:\d+\.?\d*|\.\d+))\s*$/u);
  if(match&&r.kind==='scalar'&&Number.isFinite(r.numeric)){
   const line=document.createElement('div');line.className='slider-line';const low=document.createElement('input'),high=document.createElement('input'),slider=document.createElement('input');
   low.type=high.type='number';low.className=high.className='slider-bound';low.value=row.min;high.value=row.max;low.setAttribute('aria-label','Slider minimum');high.setAttribute('aria-label','Slider maximum');slider.type='range';slider.min=Math.min(row.min,r.numeric);slider.max=Math.max(row.max,r.numeric);slider.step=(slider.max-slider.min)/200||0.01;slider.value=r.numeric;slider.setAttribute('aria-label',`${match[1]} value`);
   const updateBounds=()=>{const lo=Number(low.value),hi=Number(high.value);if(!Number.isFinite(lo)||!Number.isFinite(hi)||lo>=hi){toast('Slider minimum must be less than maximum.');return;}row.min=lo;row.max=hi;slider.min=lo;slider.max=hi;slider.step=(hi-lo)/200;saveLocal();};low.onchange=high.onchange=updateBounds;
   slider.oninput=()=>{row.text=`${match[1]} = ${Number(Number(slider.value).toPrecision(8))}`;el.querySelector('textarea').value=row.text;renderMath(el.querySelector('.math-preview'),row.text);schedule();};line.append(low,slider,high);box.append(line);
  }
 });
}
function selectView(next,id){view=next;if(id)selectedMatrix=id;if(view==='domain'&&!['magnitude','phase'].includes(component))component='phase';schedule(0);}
function graphLayout(){return {margin:{l:42,r:20,t:20,b:35},paper_bgcolor:'#fff',plot_bgcolor:'#fff',font:{family:'Inter, Segoe UI, sans-serif',color:'#637285',size:12},showlegend:false,dragmode:'pan',hovermode:'closest',xaxis:{range:bounds.slice(0,2),zeroline:true,zerolinecolor:'#8290a0',zerolinewidth:1.5,gridcolor:'#e9edf3',ticks:'outside',tickcolor:'#cbd4df'},yaxis:{range:bounds.slice(2),zeroline:true,zerolinecolor:'#8290a0',zerolinewidth:1.5,gridcolor:'#e9edf3',ticks:'outside',tickcolor:'#cbd4df'}};}
async function drawPlot(){
 if(!window.Plotly){toast('Plot library could not load. Check the static files.');return;}
 document.querySelectorAll('[data-view]').forEach(b=>b.setAttribute('aria-selected',String(b.dataset.view===view)));
 const plotResults=results.flatMap((r,i)=>(r.components||[r]).map((c,k)=>({r:{...r,...c,text:GraphTools.label(rows[i]?.plotName||r.text)+(c.label?' '+c.label:'')},i,color:k?colors[(i+k)%colors.length]:rows[i]?.color})));
 const selector=$('matrixSelect');selector.hidden=['graph','complex','created'].includes(view);selector.replaceChildren();
 const matrices=results.map((r,i)=>({r,i})).filter(({r})=>!r.error&&(view==='quantum'?!!r.quantum:view==='surface'?r.kind==='surface':view==='domain'?r.kind==='complex_field':r.kind==='matrix'&&!r.empty_basis)&&(view!=='transform'||(r.shape[0]===2&&r.shape[1]===2&&!r.complex)));
 matrices.forEach(({r,i})=>{const opt=document.createElement('option');opt.value=rows[i].id;opt.textContent=rows[i].plotName||r.name||`Expression ${i+1}`;selector.append(opt);});
 if(!matrices.some(({i})=>rows[i].id===selectedMatrix))selectedMatrix=matrices.length?rows[matrices[0].i].id:'';selector.value=selectedMatrix;
 $('graphSelection').hidden=view!=='created';
 $('parameterControls').hidden=view!=='complex';$('componentSelect').hidden=!['heatmap','domain','surface'].includes(view);for(const option of $('componentSelect').options)option.hidden=view==='domain'&&!['phase','magnitude'].includes(option.value);$('componentSelect').value=component;
 $('surfaceBounds').hidden=view!=='surface';['surfaceXmin','surfaceXmax','surfaceYmin','surfaceYmax'].forEach((id,i)=>{if(document.activeElement!==$(id))$(id).value=bounds[i];});
 $('quantumStats').hidden=view!=='quantum';$('quantumStats').replaceChildren();
 let data=[],layout=graphLayout();$('plotEmpty').hidden=true;
 if(view==='created'){
  const custom=GraphTools.plot(graphs,graphResults,graphSelection);data=custom.data;layout=custom.layout;
  $('viewHint').textContent='Edit sampling ranges in Create graph · choose a graph or overlay group · legend toggles traces';
  if(!data.length){$('plotEmpty').hidden=false;$('plotEmpty').textContent=graphs.length?'No visible graphs in this selection. Choose another group or check the graph cards.':'Choose ＋ Create graph to start a named graph.';}
 }else if(view==='graph'){
  data.push(...DatasetTools.traces(datasets,colors));
  $('viewHint').textContent='Drag to pan · scroll to zoom · complex functions: solid Re, dashed Im';
  plotResults.forEach(({r,i,color})=>{if(r.error||!rows[i]?.visible)return;
   if(['series','data_plot'].includes(r.kind)){
    const xs=r.kind==='series'?r.real.map((_,k)=>k):r.x,ys=r.kind==='series'?r.real:r.y;
    data.push({type:'scatter',mode:'markers',x:xs,y:ys,connectgaps:false,marker:{color,size:6},name:r.text,hovertemplate:'x: %{x:.6g}<br>y: %{y:.6g}<extra>%{fullData.name}</extra>'});
    if(r.complex)data.push({type:'scatter',mode:'markers',x:xs,y:r.imag,marker:{color,size:6,symbol:'cross'},name:'Im '+r.text});
   }
   if(r.kind==='complex_curve'){data.push({type:'scatter',mode:'lines',x:r.x,y:r.y,line:{color,width:2.6},name:'Re '+r.text,hovertemplate:'x: %{x:.5g}<br>Re: %{y:.5g}<extra></extra>'},{type:'scatter',mode:'lines',x:r.x,y:r.imag,line:{color,width:2.2,dash:'dash'},name:'Im '+r.text,hovertemplate:'x: %{x:.5g}<br>Im: %{y:.5g}<extra></extra>'});}
   if(r.kind==='curve')data.push({type:'scatter',mode:'lines',x:r.x,y:r.y,line:{color,width:2.6},name:r.text,connectgaps:false,hovertemplate:'x: %{x:.5g}<br>y: %{y:.5g}<extra></extra>'});
   if(r.kind==='surface')data.push({type:'contour',x:r.x,y:r.y,z:r.real,ncontours:14,contours:{coloring:'lines'},colorscale:[[0,color],[1,color]],showscale:false,line:{width:1.5},name:r.text,hovertemplate:'First: %{x:.4g}<br>Second: %{y:.4g}<br>Re f: %{z:.5g}<extra></extra>'});
   if(r.kind==='implicit')data.push({type:'contour',x:r.x,y:r.y,z:r.z,contours:{start:0,end:0,size:1,coloring:'lines'},autocontour:false,line:{width:2.4},colorscale:[[0,color],[1,color]],showscale:false,hoverinfo:'skip'});
   if(r.kind==='inequality')data.push({type:'heatmap',x:r.x,y:r.y,z:r.z,zmin:0,zmax:1,colorscale:[[0,'rgba(255,255,255,0)'],[0.499,'rgba(255,255,255,0)'],[0.5,color],[1,color]],opacity:0.18,zsmooth:false,showscale:false,hoverinfo:'skip'});
   if(r.kind==='scalar'&&!r.name&&Number.isFinite(r.numeric))data.push({type:'scatter',mode:'lines',x:bounds.slice(0,2),y:[r.numeric,r.numeric],line:{color,width:2.4},name:r.text});
  });
 }else if(view==='complex'){
  layout.xaxis.title={text:'Real'};layout.yaxis.title={text:'Imaginary'};layout.yaxis.scaleanchor='x';layout.yaxis.scaleratio=1;layout.yaxis.constrain='domain';layout.xaxis.constrain='domain';
  plotResults.forEach(({r,i,color})=>{if(r.error||!rows[i]?.visible)return;
   if(['scalar','vector','series'].includes(r.kind))data.push({type:'scatter',mode:'markers',x:[r.real].flat(),y:[r.imag].flat(),text:(r.kind==='series'?r.real:[r.value].flat()).map(fmt),marker:{color,size:10,line:{color:plotTheme().paper,width:1}},name:r.text,hovertemplate:'%{text}<br>Re: %{x:.5g}<br>Im: %{y:.5g}<extra></extra>'});
   if(['curve','complex_curve'].includes(r.kind))data.push({type:'scatter',mode:'lines',x:r.y,y:r.imag||r.y.map(v=>v===null?null:0),customdata:r.x,line:{color,width:2.6},name:r.text,connectgaps:false,hovertemplate:'t: %{customdata:.5g}<br>Re: %{x:.5g}<br>Im: %{y:.5g}<extra></extra>'});
  });
  $('viewHint').textContent='Points: scalar/vector values · curves: f(t) over the real parameter interval';
 }else{
  const chosen=matrices.find(({i})=>rows[i].id===selectedMatrix);
  if(!chosen){$('plotEmpty').hidden=false;$('plotEmpty').textContent=view==='quantum'?'Create a qubit, or enter ψ = qubit(1, i).':view==='surface'?'Define a function and choose two Plot inputs below its equation to explore a surface.':view==='domain'?'Define f(z) = z^2, then select a function.':view==='transform'?'Add a real 2 × 2 matrix to explore its transformation.':'Add a matrix expression to see its heatmap.';}
  else if(view==='quantum'){
   const quantumPlot=buildQuantumPlot(chosen.r.quantum,rows[chosen.i].color);data=quantumPlot.data;layout=quantumPlot.layout;
  }
  else if(view==='surface'){
   const r=chosen.r;data=[{type:'surface',x:r.x,y:r.y,z:r[component],colorscale:component==='phase'?'HSV':'Viridis',...(component==='phase'?{cmin:-Math.PI,cmax:Math.PI}:{}),connectgaps:false,colorbar:{title:{text:component},thickness:14},hovertemplate:'First: %{x:.4g}<br>Second: %{y:.4g}<br>Value: %{z:.5g}<extra></extra>'}];
   layout={margin:{l:5,r:5,t:10,b:5},paper_bgcolor:'#fff',font:{color:'#637285'},scene:{xaxis:{title:{text:r.parameters[0]},range:bounds.slice(0,2)},yaxis:{title:{text:r.parameters[1]},range:bounds.slice(2)},zaxis:{title:{text:component+' '+(r.name||'f')+(r.label||'')}},aspectmode:'auto'},uirevision:'surface-'+selectedMatrix};
  }
  else if(view==='domain'){
   const r=chosen.r;data=[{type:'heatmap',x:r.x,y:r.y,z:r[component],colorscale:component==='phase'?'HSV':'Viridis',...(component==='phase'?{zmin:-Math.PI,zmax:Math.PI}:{}),colorbar:{title:{text:component==='phase'?'arg f(z) [rad]':'|f(z)|'},thickness:14},hovertemplate:'Re z: %{x:.4g}<br>Im z: %{y:.4g}<br>value: %{z:.5g}<extra></extra>'}];layout.xaxis.title={text:'Real input'};layout.yaxis.title={text:'Imaginary input'};layout.yaxis.scaleanchor='x';layout.xaxis.constrain='domain';layout.yaxis.constrain='domain';
  }
  else if(view==='heatmap'){
   const r=chosen.r;data=[{type:'heatmap',z:r[component],colorscale:component==='phase'?'HSV':component==='magnitude'?'Viridis':[[0,'#2254b3'],[0.5,'#f0f4f9'],[1,'#df6937']],...(component==='phase'?{zmin:-Math.PI,zmax:Math.PI}:component==='magnitude'?{}:{zmid:0}),text:r[component].map(row=>row.map(v=>v===null?'undefined':fmt(v))),texttemplate:'%{text}',textfont:{size:15},hovertemplate:'row %{y}, column %{x}<br>%{text}<extra></extra>',colorbar:{thickness:14}}];
   layout.xaxis={title:{text:'Column index'},dtick:1,side:'top',constrain:'domain'};layout.yaxis={title:{text:'Row index'},dtick:1,autorange:'reversed',scaleanchor:'x'};layout.margin={l:55,r:40,t:50,b:45};
  }else{
   const A=chosen.r.real;const tr=(x,y)=>[A[0][0]*x+A[0][1]*y,A[1][0]*x+A[1][1]*y];
   for(let k=-5;k<=5;k++)for(const vertical of [true,false]){
    const p=vertical?[[k,-5],[k,5]]:[[-5,k],[5,k]],q=p.map(([x,y])=>tr(x,y));data.push({type:'scatter',mode:'lines',x:p.map(p=>p[0]),y:p.map(p=>p[1]),line:{color:plotTheme().grid,width:1},hoverinfo:'skip'});data.push({type:'scatter',mode:'lines',x:q.map(p=>p[0]),y:q.map(p=>p[1]),line:{color:'#2864d750',width:1},hoverinfo:'skip'});
   }
   const circle=Array.from({length:181},(_,k)=>[Math.cos(k*Math.PI/90),Math.sin(k*Math.PI/90)]),ellipse=circle.map(([x,y])=>tr(x,y));
   for(const [pts,color,dash] of [[circle,'#99a8ba','dot'],[ellipse,'#2359d5','solid']])data.push({type:'scatter',mode:'lines',x:pts.map(p=>p[0]),y:pts.map(p=>p[1]),line:{color,width:2.5,dash},hoverinfo:'skip'});
   layout.annotations=[[A[0][0],A[1][0],'#dd6b35','A e₁'],[A[0][1],A[1][1],'#169582','A e₂']].map(([x,y,color,text])=>({x,y,ax:0,ay:0,axref:'x',ayref:'y',xref:'x',yref:'y',text,showarrow:true,arrowhead:3,arrowsize:1.2,arrowwidth:3,arrowcolor:color,font:{color,size:14}}));layout.yaxis.scaleanchor='x';layout.yaxis.scaleratio=1;
  }
  $('viewHint').textContent=view==='quantum'?'Born-rule probabilities in the computational basis · Bloch sphere for one qubit':view==='surface'?'Drag to rotate · scroll to zoom · choose an output component or change the input range':view==='domain'?`Complex input → ${component} of function output · hover to inspect`:view==='heatmap'?`Matrix entries · ${component}${component==='phase'?' in radians':''}`:'Gray: original grid & circle · blue: transformed · arrows: basis vectors';
 }
 $('boundsLabel').hidden=['heatmap','quantum','created'].includes(view);$('boundsLabel').textContent=`x [${fmt(bounds[0])}, ${fmt(bounds[1])}]   y [${fmt(bounds[2])}, ${fmt(bounds[3])}]`;
 if(['graph','complex'].includes(view)&&(rows.some(r=>r.visible&&r.plotName)||datasets.some(d=>d.visible)||results.some((r,i)=>(r.components||['series','data_plot'].includes(r.kind))&&rows[i]?.visible))){
  layout.showlegend=true;layout.legend={orientation:'h',y:-0.18,font:{size:10}};
  for(const trace of data)if(trace.hovertemplate)trace.hovertemplate=trace.hovertemplate.replace('<extra></extra>','<extra>%{fullData.name}</extra>');
 }
 if(['surface','domain'].includes(view)){const selected=rows.find(r=>r.id===selectedMatrix);if(selected?.plotName){layout.title={text:GraphTools.label(selected.plotName)};layout.margin.t=50;}}
 applyPlotTheme(layout);
 rendering=true;
 try{await Plotly.react('plot',data,layout,{responsive:true,scrollZoom:true,displayModeBar:false,displaylogo:false});}finally{rendering=false;}
 if(!$('plot')._boundEvents){$('plot').on('plotly_relayout',e=>{if(rendering||view==='created'||view==='heatmap'||view==='surface'||view==='quantum')return;if(e['xaxis.autorange']||e['yaxis.autorange']){bounds=[-10,10,-7,7];schedule(0);return;}const b=[e['xaxis.range[0]']??bounds[0],e['xaxis.range[1]']??bounds[1],e['yaxis.range[0]']??bounds[2],e['yaxis.range[1]']??bounds[3]];if(b.some((v,i)=>Math.abs(v-bounds[i])>1e-9)){bounds=b;schedule(140);}});$('plot')._boundEvents=true;}
}
// Parse only bracket structure here; cell expressions are evaluated by the Python interpreter.
function matrixCells(text){const rhs=text.slice(text.indexOf('=')+1).trim();if(!rhs.startsWith('[[')||!rhs.endsWith(']]'))return null;let depth=0,start=0,parts=[];for(let i=1;i<rhs.length-1;i++){if(rhs[i]==='['){if(depth===0)start=i+1;depth++;}else if(rhs[i]===']'){depth--;if(depth===0)parts.push(rhs.slice(start,i));}}if(!parts.length)return null;return parts.map(p=>{let cells=[],s=0,d=0;for(let i=0;i<p.length;i++){if('(['.includes(p[i]))d++;if(')]'.includes(p[i]))d--;if(p[i]===','&&d===0){cells.push(p.slice(s,i).trim());s=i+1;}}cells.push(p.slice(s).trim());return cells;});}
function buildGrid(r,c,values){gridRows=r;gridCols=c;const grid=$('matrixGrid');grid.replaceChildren();grid.style.gridTemplateColumns=`repeat(${c},minmax(70px,1fr))`;for(let i=0;i<r;i++)for(let j=0;j<c;j++){const input=document.createElement('input');input.value=values?.[i]?.[j]??(i===j?'1':'0');input.required=true;input.maxLength=100;input.setAttribute('aria-label',`Row ${i+1}, column ${j+1}`);grid.append(input);}}
function readGrid(){const values=[...$('matrixGrid').querySelectorAll('input')].map(i=>i.value.trim());return Array.from({length:gridRows},(_,i)=>values.slice(i*gridCols,(i+1)*gridCols));}
function openMatrix(index=null){
 matrixEdit=index;$('matrixError').textContent='';let values=null;
 if(index!==null){values=matrixCells(rows[index].text);if(!values){toast('This matrix is calculated. Edit its expression directly.');return;}if(values.length>12||values[0].length>12){toast('Edit matrices larger than 12 × 12 in the expression field.');return;}$('matrixName').value=results[index].name;}
 else{let name='A',n=1;while(rows.some(r=>new RegExp(`^\\s*${name}\\s*=`).test(r.text)))name='M'+n++;$('matrixName').value=name;}
 $('matrixRows').value=values?.length||2;$('matrixCols').value=values?.[0].length||2;buildGrid(Number($('matrixRows').value),Number($('matrixCols').value),values);$('matrixDialog').showModal();
}
$('matrixForm').onsubmit=e=>{e.preventDefault();const name=$('matrixName').value.trim(),cells=readGrid();const text=`${name} = [${cells.map(r=>'['+r.join(', ')+']').join(', ')}]`;if(text.length>1200){$('matrixError').textContent='Matrix expression exceeds 1200 characters.';return;}if(matrixEdit===null){if(rows.length>=40){$('matrixError').textContent='Maximum 40 expressions.';return;}rows.push(newRow(text));}else rows[matrixEdit].text=text;$('matrixDialog').close();renderRows();schedule(0);};
$('resizeMatrix').onclick=()=>{const r=Number($('matrixRows').value),c=Number($('matrixCols').value);if(!Number.isInteger(r)||!Number.isInteger(c)||r<1||c<1||r>12||c>12){$('matrixError').textContent='Grid editor supports 1–12 rows and columns.';return;}$('matrixError').textContent='';buildGrid(r,c,readGrid());};
$('addBtn').onclick=()=>addExpression();$('matrixBtn').onclick=()=>openMatrix();$('helpBtn').onclick=()=>$('help').showModal();document.querySelectorAll('[data-close]').forEach(b=>b.onclick=()=>$(b.dataset.close).close());
$('examples').onchange=e=>{loadExample(e.target.value);e.target.value='';};document.querySelectorAll('[data-view]').forEach(b=>b.onclick=()=>selectView(b.dataset.view));$('matrixSelect').onchange=e=>{selectedMatrix=e.target.value;drawPlot();};
$('componentSelect').onchange=e=>{component=e.target.value;saveLocal();drawPlot();};
for(const id of ['parameterMin','parameterMax'])$(id).onchange=()=>schedule(0);
$('resetBtn').onclick=()=>{if(view==='created'){const change=$('plot').layout?.scene?{'scene.camera':{eye:{x:1.25,y:1.25,z:1.25}}}:{'xaxis.autorange':true,'yaxis.autorange':true};Plotly.relayout('plot',change);return;}if(['surface','quantum'].includes(view)&&$('plot').layout?.scene)Plotly.relayout('plot',{'scene.camera':{eye:{x:1.25,y:1.25,z:1.25}}});bounds=[-10,10,-7,7];schedule(0);};$('exportBtn').onclick=()=>Plotly.downloadImage('plot',{format:'png',filename:'NMGrapher',scale:2});
$('saveBtn').onclick=()=>{const blob=new Blob([JSON.stringify(worksheetData(),null,2)],{type:'application/json'});const a=document.createElement('a');a.href=URL.createObjectURL(blob);a.download='NMGrapher-worksheet.json';a.click();setTimeout(()=>URL.revokeObjectURL(a.href),1000);toast('Worksheet downloaded.');};
$('importBtn').onclick=()=>$('fileInput').click();$('fileInput').onchange=async e=>{const file=e.target.files[0];if(!file)return;try{if(file.size>2*1024*1024)throw Error('Choose a worksheet smaller than 2 MB.');const data=JSON.parse(await file.text());const importedRows=validateWorksheet(data);DatasetTools.validate(data.datasets??[]);GraphTools.validate(data.graphs??[]);WaveletTools.settings(data.wavelet_settings);rows=importedRows;bounds=validBounds(data.bounds)?data.bounds:[-10,10,-7,7];view=['graph','heatmap','transform','complex','domain','surface','quantum','created'].includes(data.view)?data.view:'graph';restoreViewOptions(data);renderRows();schedule(0);toast('Worksheet opened.');}catch(err){toast(err.message);}e.target.value='';};
function validBounds(b){return Array.isArray(b)&&b.length===4&&b.every(v=>Number.isFinite(v)&&Math.abs(v)<=1e6)&&b[1]>b[0]&&b[3]>b[2];}
try{const data=JSON.parse(localStorage.getItem('matrix-graph-v1'));if(data){const importedRows=validateWorksheet(data);DatasetTools.validate(data.datasets??[]);GraphTools.validate(data.graphs??[]);WaveletTools.settings(data.wavelet_settings);rows=importedRows;bounds=validBounds(data.bounds)?data.bounds:bounds;view=['graph','heatmap','transform','complex','domain','surface','quantum','created'].includes(data.view)?data.view:'graph';restoreViewOptions(data);}}catch{}
if(!rows.length&&!datasets.length&&!graphs.length)rows=examples.basics.map(newRow);renderRows();schedule(0);
new ResizeObserver(()=>{if($('plot').data)Plotly.Plots.resize('plot');}).observe($('plot'));

async function openGreek(){
 if(!symbolTarget?.isConnected){if($('qubitDialog').open)symbolTarget=$('qubitName');else if($('calculusDialog').open)symbolTarget=$('calculusExpression');else if($('functionDialog').open)symbolTarget=$('functionBody');else if(!$('matrixDialog').open){if(!rows.length)addExpression();symbolTarget=$('expressions').querySelector('textarea');}else symbolTarget=$('matrixName');}
 try{
  if(!$('greekLetters').children.length){
   const res=await fetch('/api/symbols');if(!res.ok)throw Error('Could not load Greek symbols.');const catalog=await res.json();
   const makeButton=(symbol,title)=>{const b=document.createElement('button');b.type='button';b.textContent=symbol;b.title=title;b.setAttribute('aria-label',title);b.onclick=()=>{const target=symbolTarget;if(!target?.isConnected)return;const start=target.selectionStart??target.value.length,end=target.selectionEnd??start;target.setRangeText(symbol,start,end,'end');target.dispatchEvent(new Event('input',{bubbles:true}));$('greekDialog').close();target.focus();};return b;};
   for(const letter of catalog.letters){const cell=document.createElement('div');const label=document.createElement('span');label.textContent=letter.name;cell.append(label,makeButton(letter.lower,letter.name+' lowercase'),makeButton(letter.upper,letter.name+' uppercase'));$('greekLetters').append(cell);}
   for(const variant of catalog.variants){const b=makeButton(variant.symbol,variant.name+'; alias of '+variant.canonical);b.textContent=variant.symbol+' → '+variant.canonical;$('greekVariants').append(b);}
  }
  $('greekDialog').showModal();
 }catch(e){toast(e.message);}
}
$('greekBtn').onclick=openGreek;$('matrixGreekBtn').onclick=openGreek;

// Previews use safe MathML generated from the calculator's own parser.
function renderMath(container,source){MathPreview.render(container,source);}
function functionArguments(){return GreekInput.normalize($('functionArgs').value).split(',').map(s=>s.trim());}
function functionDraft(){const name=GreekInput.normalize($('functionName').value.trim()),args=functionArguments();return `${name}(${args.join(', ')}) = ${$('functionBody').value.trim()}`;}
let functionCalcDefault='x_1';
function updateFunctionPreview(){const first=functionArguments()[0]||'x_1';for(const id of ['functionCalcVariable','functionIntegralUpper'])if(!$(id).value||$(id).value===functionCalcDefault)$(id).value=first;functionCalcDefault=first;renderMath($('functionPreview'),functionDraft());$('functionError').textContent='';}
function openFunction(index=null){
 functionEdit=index;const info=index===null?null:results[index]?.function;
 if(index!==null&&!info){toast('Write a function definition first.');return;}
 let name='f_1',n=1;while(results.some(r=>r.function?.name===name)||rows.some(r=>r.text.startsWith(name+'(')||r.text.startsWith(name+' (')))name='f_'+(++n);
 $('functionTemplate').value='';$('functionCalcVariable').value=info?.parameters[0]||'x_1';$('functionIntegralLower').value='0';$('functionIntegralUpper').value=info?.parameters[0]||'x_1';functionCalcDefault=info?.parameters[0]||'x_1';
 $('functionName').value=info?.name||name;$('functionArgs').value=info?info.parameters.join(', '):'x_1, x_2';$('functionBody').value=info?.body||'sin(x_1) * cos(x_2)';updateFunctionPreview();$('functionDialog').showModal();$('functionBody').focus();
}
$('functionBtn').onclick=()=>openFunction();$('functionGreekBtn').onclick=openGreek;
for(const id of ['functionName','functionArgs','functionBody'])$(id).addEventListener('input',updateFunctionPreview);
$('functionForm').onsubmit=async e=>{
 e.preventDefault();const text=functionDraft(),index=functionEdit??rows.length;
 if(text.length>1200){$('functionError').textContent='Function exceeds 1200 characters.';return;}
 if(functionEdit===null&&rows.length>=40){$('functionError').textContent='Maximum 40 expressions.';return;}
 const candidate=rows.map(r=>({text:r.text}));if(functionEdit===null)candidate.push({text});else candidate[index]={text};
 const button=e.submitter||$('functionForm').querySelector('button[type=submit]');button.disabled=true;
 try{
  const res=await fetch('/api/evaluate',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({datasets,expressions:candidate,bounds})});const data=await res.json();if(!res.ok)throw Error(data.error||'Could not validate function.');
  const result=data.results[index];if(!result.function)throw Error(result.error||'Use a valid function name and distinct argument names.');
  if(functionEdit===null)rows.push(newRow(text));else {rows[index].text=text;rows[index].plotComponent='all';rows[index].plotSlice=null;}
  if(result.function.parameters.length>=2){view='surface';component='real';selectedMatrix=rows[index].id;}
  $('functionDialog').close();renderRows();schedule(0);
 }catch(err){$('functionError').textContent=err.message;}finally{button.disabled=false;}
};
document.querySelectorAll('[data-script]').forEach(button=>button.onclick=()=>{
 let target=symbolTarget;
 if($('functionDialog').open&&!target?.closest('#functionForm'))target=$('functionBody');
 if(!target?.isConnected){if(!rows.length)addExpression();target=$('expressions').querySelector('textarea');}
 const start=target.selectionStart??target.value.length,end=target.selectionEnd??start;
 const token=button.dataset.script==='sub'?'_1':'^(2)';target.setRangeText(token,start,end,'end');
 const offset=button.dataset.script==='sub'?1:2;target.setSelectionRange(start+offset,start+offset+1);target.dispatchEvent(new Event('input',{bubbles:true}));target.focus();
});
$('surfaceBoundsForm').onsubmit=e=>{e.preventDefault();const next=['surfaceXmin','surfaceXmax','surfaceYmin','surfaceYmax'].map(id=>Number($(id).value));if(!validBounds(next)||next[1]-next[0]<=1e-6||next[3]-next[2]<=1e-6||next[1]-next[0]>1e6||next[3]-next[2]>1e6){toast('Use increasing finite ranges with widths between 0.000001 and 1,000,000.');return;}bounds=next;$('surfaceBounds').open=false;schedule(0);};

let calculusRevision=0,calculusSourceSlice=null;
for(const [value,info] of Object.entries(CalculusEditor.operations)){const opt=document.createElement('option');opt.value=value;opt.textContent=info.label;$('calculusOperation').append(opt);}
function calculusArguments(){return GreekInput.normalize($('calculusArguments').value).split(',').map(s=>s.trim());}
function calculusDraft(){return CalculusEditor.draft({args:calculusArguments(),variable:$('calculusVariable').value,variables:[...$('calculusVariables').querySelectorAll('input:checked')].map(e=>e.value),operation:$('calculusOperation').value,expression:GreekInput.normalize($('calculusExpression').value.trim()),lower:$('calculusLower').value.trim(),upper:$('calculusUpper').value.trim(),name:GreekInput.normalize($('calculusName').value.trim()),resultMode:$('calculusResultMode').value,point:GreekInput.normalize($('calculusPoint').value.trim()),direction:GreekInput.normalize($('calculusDirection').value.trim()),step:$('calculusStep').value.trim(),absTol:$('calculusAbsTol').value.trim(),relTol:$('calculusRelTol').value.trim()});}
function updateCalculusPreview(){
 calculusRevision++;$('calculusComputed').hidden=true;
 const args=calculusArguments(),old=$('calculusVariable').value;$('calculusVariable').replaceChildren();
 args.filter(Boolean).forEach(arg=>{const option=document.createElement('option');option.value=arg;option.textContent=arg;$('calculusVariable').append(option);});if(args.includes(old))$('calculusVariable').value=old;
 const key=JSON.stringify(args),list=$('calculusVariables');
 if(list.dataset.arguments!==key){const prior=new Map([...list.querySelectorAll('input')].map(el=>[el.value,el.checked]));list.replaceChildren();for(const arg of args.filter(Boolean)){const label=document.createElement('label'),input=document.createElement('input');input.type='checkbox';input.value=arg;input.checked=prior.get(arg)??true;input.onchange=updateCalculusPreview;label.append(input,document.createTextNode(arg));list.append(label);}list.dataset.arguments=key;}
 const op=$('calculusOperation').value,spec=CalculusEditor.operations[op];
 $('calculusOperationHelp').textContent=spec.help;$('calculusVariableLabel').hidden=!!spec.multi;$('calculusVariablesLabel').hidden=!spec.multi;$('calculusDirectionLabel').hidden=op!=='directional';
 $('calculusLowerLabel').hidden=!(spec.integral||spec.primitive);$('calculusUpperLabel').hidden=op!=='definite';$('calculusStepLabel').hidden=!!(spec.integral||spec.primitive);$('calculusAbsTolLabel').hidden=$('calculusRelTolLabel').hidden=!spec.integral;
 $('calculusPointHelp').textContent='Point coordinates follow: '+args.join(', ')+'. Use Evaluate at point to inspect the result before adding it.';
 $('calculusError').textContent='';
 try{const draft=calculusDraft();$('calculusNameLabel').hidden=$('calculusResultMode').value==='point'||!draft.remaining.length;renderMath($('calculusPreview'),draft.text);}catch(error){$('calculusPreview').replaceChildren();$('calculusError').textContent=error.message;}
}
function openCalculus(index=null){
 const info=index===null?null:results[index]?.function,params=info?.parameters||['x'];calculusSourceSlice=index===null?null:results[index]?.plot_slice;
 $('calculusArguments').value=params.join(', ');$('calculusExpression').value=info?`${info.name}(${params.join(', ')})`:'sin(x)';$('calculusOperation').value='first';$('calculusLower').value='0';$('calculusUpper').value='1';$('calculusResultMode').value='function';$('calculusPoint').value=params.map(p=>calculusSourceSlice?.fixed[p]??0).join(', ');$('calculusDirection').value=params.map((_,i)=>i===0?1:0).join(', ');$('calculusStep').value='';$('calculusAbsTol').value='1e-8';$('calculusRelTol').value='1e-7';$('calculusVariables').replaceChildren();delete $('calculusVariables').dataset.arguments;
 let name='result_1',n=1;while(results.some(r=>r.function?.name===name||r.name===name))name='result_'+(++n);$('calculusName').value=name;
 updateCalculusPreview();$('calculusDialog').showModal();$('calculusExpression').focus();
}
$('calculusBtn').onclick=()=>openCalculus();$('calculusGreekBtn').onclick=openGreek;
for(const id of ['calculusArguments','calculusExpression','calculusLower','calculusUpper','calculusName','calculusPoint','calculusDirection','calculusStep','calculusAbsTol','calculusRelTol'])$(id).addEventListener('input',updateCalculusPreview);
for(const id of ['calculusOperation','calculusVariable','calculusResultMode'])$(id).onchange=updateCalculusPreview;
function calculusSlice(draft){
 if(!calculusSourceSlice||$('calculusResultMode').value==='point'||!draft.remaining.length)return null;
 let axes=calculusSourceSlice.axes.filter(a=>draft.remaining.includes(a));if(!axes.length)axes=draft.remaining.slice(0,2);
 return {axes,fixed:Object.fromEntries(draft.remaining.filter(p=>!axes.includes(p)).map(p=>[p,calculusSourceSlice.fixed[p]??0]))};
}
async function calculateDraft(text,slice=null){
 if(text.length>1200)throw Error('Result exceeds 1200 characters.');
 if(rows.length>=40)throw Error('Maximum 40 expressions; remove a row before calculating a new result.');
 const res=await fetch('/api/evaluate',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({datasets,expressions:[...rows.map(r=>({text:r.text,plot_slice:r.plotSlice})),{text,plot_slice:slice}],bounds})});const data=await res.json();if(!res.ok)throw Error(data.error||'Could not calculate.');const result=data.results.at(-1);if(result.error)throw Error(result.error);return result;
}
$('calculusPreviewBtn').onclick=async()=>{
 const button=$('calculusPreviewBtn'),revision=calculusRevision;button.disabled=true;
 try{const draft=calculusDraft();if(!$('calculusPoint').value.trim())throw Error('Enter point coordinates.');const result=await calculateDraft(draft.pointText);if(revision!==calculusRevision)return;if(!['scalar','vector','matrix'].includes(result.kind))throw Error('Point coordinates must resolve to scalar values; define every symbol used in them.');
 const box=$('calculusComputed');box.replaceChildren();const value=document.createElement('pre');value.textContent=result.kind==='matrix'?result.value.map(r=>'['+r.map(fmt).join(', ')+']').join('\n'):result.kind==='vector'?'['+result.value.map(fmt).join(', ')+']':fmt(result.value);box.append(value);
 const info=result.calculus?.at(-1);if(info){const note=document.createElement('div');note.textContent=`Estimated error: ${info.error_estimate===null?'unavailable':Number(info.error_estimate).toExponential(3)}${info.evaluations?' · '+info.evaluations+' evaluations':''}`;box.append(note);}box.hidden=false;$('calculusError').textContent='';
 }catch(error){if(revision===calculusRevision)$('calculusError').textContent=error.message;}finally{button.disabled=false;}
};
$('calculusForm').onsubmit=async e=>{
 e.preventDefault();const button=e.submitter||$('calculusForm').querySelector('button[type=submit]'),revision=calculusRevision;button.disabled=true;
 try{const draft=calculusDraft(),slice=calculusSlice(draft),result=await calculateDraft(draft.text,slice);if(revision!==calculusRevision)return;if($('calculusResultMode').value==='point'&&!['scalar','vector','matrix'].includes(result.kind))throw Error('Point coordinates must resolve to scalar values.');
 const row=newRow(draft.text);row.plotSlice=slice;rows.push(row);if(result.kind==='surface'){view='surface';component='real';selectedMatrix=row.id;}else if(['curve','complex_curve'].includes(result.kind))view='graph';else if(result.kind==='matrix'){view='heatmap';component='real';selectedMatrix=row.id;}
 $('calculusDialog').close();renderRows();schedule(0);
 }catch(error){if(revision===calculusRevision)$('calculusError').textContent=error.message;}finally{button.disabled=false;}
};
$('differentiateFormula').onclick=()=>{const arg=$('functionCalcVariable').value.trim()||functionArguments()[0],body=$('functionBody').value.trim();$('functionBody').value=`d/d${arg}(${body})`;updateFunctionPreview();$('functionBody').focus();};
$('integrateFormula').onclick=()=>{const arg=$('functionCalcVariable').value.trim()||functionArguments()[0],body=$('functionBody').value.trim(),lower=$('functionIntegralLower').value.trim()||'0',upper=$('functionIntegralUpper').value.trim()||functionArguments()[0];$('functionBody').value=`∫_{${lower}}^{${upper}} (${body}) d${arg}`;updateFunctionPreview();$('functionBody').focus();};

function plotTheme(){const css=getComputedStyle(document.documentElement);return {paper:css.getPropertyValue('--surface').trim(),text:css.getPropertyValue('--muted').trim(),ink:css.getPropertyValue('--ink').trim(),grid:css.getPropertyValue('--plot-grid').trim(),axis:css.getPropertyValue('--plot-axis').trim()};}
function applyPlotTheme(layout){
 const t=plotTheme();layout.paper_bgcolor=t.paper;layout.plot_bgcolor=t.paper;layout.font={...layout.font,color:t.text};layout.hoverlabel={bgcolor:t.paper,bordercolor:t.axis,font:{color:t.ink}};
 for(const name of ['xaxis','yaxis'])if(layout[name])Object.assign(layout[name],{gridcolor:t.grid,zerolinecolor:t.axis,tickcolor:t.axis,linecolor:t.axis});
 if(layout.scene)for(const name of ['xaxis','yaxis','zaxis'])Object.assign(layout.scene[name],{backgroundcolor:t.paper,gridcolor:t.grid,zerolinecolor:t.axis,color:t.text,showbackground:true});
}
$('themeSelect').value=document.documentElement.dataset.theme||'light';
$('themeSelect').onchange=e=>{document.documentElement.dataset.theme=e.target.value;try{localStorage.setItem('matrix-graph-theme',e.target.value);}catch{}if($('plot').data)drawPlot();};

function moveRow(id,destination){
 const source=rows.findIndex(row=>row.id===id);if(source<0)return;
 destination=Math.max(0,Math.min(rows.length-1,destination));
 if(source===destination)return;
 const [row]=rows.splice(source,1);rows.splice(destination,0,row);
 renderRows();renderResults();schedule(0);
 const handle=document.querySelector(`.expression[data-id="${id}"] .drag-handle`);handle?.focus({preventScroll:true});handle?.scrollIntoView({block:'nearest'});
 $('reorderAnnouncement').textContent=`Equation moved to position ${destination+1} of ${rows.length}.`;
}
function beginRowDrag(event,id,handle){
 if(event.button!==0||!event.isPrimary||rows.length<2)return;
 event.preventDefault();handle.focus({preventScroll:true});
 dragState={id,handle,pointerId:event.pointerId,startX:event.clientX,startY:event.clientY,x:event.clientX,y:event.clientY,active:false,beforeId:undefined};
 handle.setPointerCapture(event.pointerId);
 handle.onpointermove=e=>{if(!dragState||e.pointerId!==dragState.pointerId)return;dragState.x=e.clientX;dragState.y=e.clientY;if(!dragState.active&&Math.hypot(e.clientX-dragState.startX,e.clientY-dragState.startY)>5){dragState.active=true;handle.closest('.expression').classList.add('dragging');document.body.classList.add('reordering');const ghost=document.createElement('div');ghost.className='drag-ghost';ghost.textContent=rows.find(r=>r.id===id)?.text.slice(0,90)||'Empty equation';document.body.append(ghost);dragState.ghost=ghost;dragFrame=requestAnimationFrame(rowDragFrame);}};
 handle.onpointerup=e=>finishRowDrag(e,false);
 handle.onpointercancel=e=>finishRowDrag(e,true);
 handle.onlostpointercapture=e=>{if(dragState)finishRowDrag(e,true);};
}
function clearDropMarkers(){document.querySelectorAll('.drop-before,.drop-after').forEach(el=>el.classList.remove('drop-before','drop-after'));}
function rowDragFrame(){
 const drag=dragState;if(!drag?.active)return;
 drag.ghost.style.left=(drag.x+15)+'px';drag.ghost.style.top=(drag.y+12)+'px';
 const list=$('expressions'),rect=list.getBoundingClientRect();clearDropMarkers();drag.beforeId=undefined;
 if(drag.x>=rect.left&&drag.x<=rect.right&&drag.y>=rect.top-20&&drag.y<=rect.bottom+20){
  const edge=44;if(drag.y<rect.top+edge)list.scrollTop-=Math.min(16,(rect.top+edge-drag.y)/3);else if(drag.y>rect.bottom-edge)list.scrollTop+=Math.min(16,(drag.y-(rect.bottom-edge))/3);
  const targets=[...list.querySelectorAll('.expression')].filter(el=>el.dataset.id!==drag.id);
  const before=targets.find(el=>{const box=el.getBoundingClientRect();return drag.y<box.top+box.height/2;});
  drag.beforeId=before?.dataset.id??null;
  if(before)before.classList.add('drop-before');else targets.at(-1)?.classList.add('drop-after');
 }
 dragFrame=requestAnimationFrame(rowDragFrame);
}
function finishRowDrag(event,cancelled){
 const drag=dragState;if(!drag||event.pointerId!==drag.pointerId)return;
 // Resolve the final pointer position even if release precedes the next frame.
 if(drag.active&&!cancelled){cancelAnimationFrame(dragFrame);drag.x=event.clientX;drag.y=event.clientY;rowDragFrame();}
 dragState=null;cancelAnimationFrame(dragFrame);drag.ghost?.remove();document.body.classList.remove('reordering');clearDropMarkers();drag.handle.closest('.expression')?.classList.remove('dragging');
 if(drag.handle.hasPointerCapture(drag.pointerId))drag.handle.releasePointerCapture(drag.pointerId);
 drag.handle.onpointermove=drag.handle.onpointerup=drag.handle.onpointercancel=drag.handle.onlostpointercapture=null;
 if(!cancelled&&drag.active&&drag.beforeId!==undefined){const remaining=rows.filter(row=>row.id!==drag.id);const destination=drag.beforeId===null?remaining.length:remaining.findIndex(row=>row.id===drag.beforeId);if(destination>=0)moveRow(drag.id,destination);}
}
document.addEventListener('keydown',event=>{if(event.key==='Escape'&&dragState){event.preventDefault();finishRowDrag({pointerId:dragState.pointerId},true);}});

function buildQuantumPlot(q,color){
 const t=plotTheme(),single=q.bloch!==null;
 const data=[{type:'bar',x:q.basis.map(s=>'|'+s+'⟩'),y:q.probabilities,marker:{color},hovertemplate:'%{x}<br>P = %{y:.6f}<extra></extra>',text:q.dimension<=8?q.probabilities.map(p=>(100*p).toFixed(1)+'%'):undefined,textposition:'auto'}];
 const layout={margin:{l:45,r:25,t:30,b:55},showlegend:false,xaxis:{domain:single?[.73,1]:[0,1],type:'category',title:{text:'Measurement outcome'}},yaxis:{domain:single?[.12,.85]:[0,1],range:[0,1.08],title:{text:'Probability'},anchor:'x'},uirevision:'quantum-'+selectedMatrix};
 if(single){
  const u=Array.from({length:49},(_,k)=>2*Math.PI*k/48),v=Array.from({length:25},(_,k)=>Math.PI*k/24);
  data.push({type:'surface',x:v.map(a=>u.map(b=>Math.sin(a)*Math.cos(b))),y:v.map(a=>u.map(b=>Math.sin(a)*Math.sin(b))),z:v.map(a=>u.map(()=>Math.cos(a))),colorscale:[[0,'#6c9fdc'],[1,'#6c9fdc']],opacity:.12,showscale:false,hoverinfo:'skip'});
  for(let axis=0;axis<3;axis++){const points=u.map(a=>{const p=[0,0,0];p[(axis+1)%3]=Math.cos(a);p[(axis+2)%3]=Math.sin(a);return p;});data.push({type:'scatter3d',mode:'lines',x:points.map(p=>p[0]),y:points.map(p=>p[1]),z:points.map(p=>p[2]),line:{color:t.axis,width:2},hoverinfo:'skip'});}
  const b=q.bloch;data.push({type:'scatter3d',mode:'lines+markers',x:[0,b[0]],y:[0,b[1]],z:[0,b[2]],line:{color,width:7},marker:{color,size:[3,6]},hovertemplate:'X: %{x:.5f}<br>Y: %{y:.5f}<br>Z: %{z:.5f}<extra></extra>'});
  data.push({type:'scatter3d',mode:'text',x:[0,0,1.14,0],y:[0,0,0,1.14],z:[1.15,-1.15,0,0],text:['|0⟩','|1⟩','+X','+Y'],textfont:{color:t.ink,size:14},hoverinfo:'skip'});
  layout.scene={domain:{x:[0,.66],y:[0,1]},xaxis:{title:{text:'X'},range:[-1.2,1.2]},yaxis:{title:{text:'Y'},range:[-1.2,1.2]},zaxis:{title:{text:'Z'},range:[-1.2,1.2]},aspectmode:'cube'};
 }
 const stats=$('quantumStats');const summary=document.createElement('span');summary.textContent=`${q.qubits} qubit${q.qubits===1?'':'s'} · purity ${fmt(q.purity)} · entropy ${fmt(Math.max(0,q.entropy))} bits`;stats.append(summary);
 const detail=document.createElement('span');detail.textContent=single?`Bloch vector [${q.bloch.map(fmt).join(', ')}]`:'To inspect one qubit, enter reduced(state, 0) or another index. Leftmost qubit is 0.';stats.append(detail);
 return {data,layout};
}
function qubitDraft(){
 const name=$('qubitName').value.trim();
 if($('qubitMode').value==='amplitudes')return [`${name} = qubit(${$('qubitAlpha').value.trim()}, ${$('qubitBeta').value.trim()})`];
 return [`${$('qubitForm').dataset.thetaName} = ${$('qubitTheta').value}`,`${$('qubitForm').dataset.phiName} = ${$('qubitPhi').value}`,`${name} = blochstate(${$('qubitForm').dataset.thetaName}, ${$('qubitForm').dataset.phiName})`];
}
function updateQubitPreview(){const angle=$('qubitMode').value==='angles';$('qubitAngles').hidden=!angle;$('qubitAmplitudes').hidden=angle;renderMath($('qubitPreview'),qubitDraft().join('\n'));$('qubitError').textContent='';}
function openQubit(){
 const used=new Set(results.flatMap(r=>[r.name,r.function?.name]).filter(Boolean));let n=1;while(['ψ_','θ_','φ_'].some(prefix=>used.has(prefix+n)))n++;
 $('qubitName').value='ψ_'+n;$('qubitForm').dataset.thetaName='θ_'+n;$('qubitForm').dataset.phiName='φ_'+n;updateQubitPreview();$('qubitDialog').showModal();$('qubitName').focus();
}
$('qubitBtn').onclick=openQubit;$('qubitGreekBtn').onclick=openGreek;$('qubitMode').onchange=updateQubitPreview;
for(const id of ['qubitName','qubitTheta','qubitPhi','qubitAlpha','qubitBeta'])$(id).oninput=updateQubitPreview;
$('qubitForm').onsubmit=async e=>{
 e.preventDefault();const expressions=qubitDraft();if(rows.length+expressions.length>40){$('qubitError').textContent='This would exceed 40 worksheet rows.';return;}
 const button=e.submitter||$('qubitForm').querySelector('button[type=submit]');button.disabled=true;
 try{
  const res=await fetch('/api/evaluate',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({datasets,expressions:[...rows.map(r=>({text:r.text})),...expressions.map(text=>({text}))],bounds})});const data=await res.json();if(!res.ok)throw Error(data.error||'Could not create state.');const added=data.results.slice(-expressions.length);const error=added.find(r=>r.error);if(error)throw Error(error.error);if(added.at(-1).quantum?.qubits!==1)throw Error('Enter a valid one-qubit state.');
  const fresh=expressions.map((text,i)=>newRow(text,rows.length+i));if(fresh.length===3){fresh[0].min=0;fresh[0].max=Math.PI;fresh[1].min=0;fresh[1].max=2*Math.PI;}rows.push(...fresh);selectedMatrix=rows.at(-1).id;view='quantum';$('qubitDialog').close();renderRows();schedule(0);
 }catch(error){$('qubitError').textContent=error.message;}finally{button.disabled=false;}
};

function entryLabel(shape,k){return shape.length===1?`[${k}]`:`[${Math.floor(k/shape[1])}, ${k%shape[1]}]`;}
$('functionTemplate').onchange=e=>{
 const args=functionArguments(),a=args[0]||'t',b=args[1]||'';if(!args[0])$('functionArgs').value=a;
 const v=b?`[${a}, ${b}, ${a} * ${b}]`:`[cos(${a}), sin(${a})]`;
 const m=b?`[[${a}, ${b}], [-${b}, ${a}]]`:`[[cos(${a}), -sin(${a})], [sin(${a}), cos(${a})]]`;
 if(e.target.value)$('functionBody').value=e.target.value==='vector'?v:e.target.value==='matrix'?m:b?`sin(${a}) * cos(${b})`:`sin(${a})`;
 e.target.value='';updateFunctionPreview();$('functionBody').focus();
};
// The desktop pane width is a browser preference independent of a worksheet.
(() => {
 const divider=$('paneDivider'),root=document.documentElement;
 let preferred=390,drag=null;
 try{const saved=Number(localStorage.getItem('matrix-graph-pane-width'));if(saved>=280&&saved<=900)preferred=saved;}catch{}
 const limits=()=>({min:280,max:Math.max(280,Math.min(900,window.innerWidth-328))});
 const apply=(width,persist=false)=>{
  const {min,max}=limits(),value=Math.round(Math.max(min,Math.min(max,width)));
  root.style.setProperty('--equation-pane-width',value+'px');
  divider.setAttribute('aria-valuemin',min);divider.setAttribute('aria-valuemax',max);divider.setAttribute('aria-valuenow',value);divider.setAttribute('aria-valuetext',value+' pixels');
  if(persist){preferred=value;try{localStorage.setItem('matrix-graph-pane-width',String(value));}catch{}}
  return value;
 };
 divider.onpointerdown=e=>{if(e.button!==0)return;e.preventDefault();divider.focus();drag={id:e.pointerId,start:e.clientX,width:$('equationPane').getBoundingClientRect().width};divider.setPointerCapture(e.pointerId);document.body.classList.add('resizing-pane');};
 divider.onpointermove=e=>{if(drag?.id===e.pointerId)apply(drag.width+e.clientX-drag.start);};
 const finish=cancel=>{if(!drag)return;const prior=drag;drag=null;apply(cancel?prior.width:Number(divider.getAttribute('aria-valuenow')),true);document.body.classList.remove('resizing-pane');if(divider.hasPointerCapture(prior.id))divider.releasePointerCapture(prior.id);};
 divider.onpointerup=()=>finish(false);divider.onpointercancel=()=>finish(true);divider.onlostpointercapture=()=>finish(true);
 divider.onkeydown=e=>{const {min,max}=limits();let width=Number(divider.getAttribute('aria-valuenow'));if(e.key==='ArrowLeft')width-=24;else if(e.key==='ArrowRight')width+=24;else if(e.key==='Home')width=min;else if(e.key==='End')width=max;else return;e.preventDefault();apply(width,true);};
 document.addEventListener('keydown',e=>{if(e.key==='Escape'&&drag){e.preventDefault();finish(true);}});
 divider.ondblclick=()=>apply(390,true);window.addEventListener('resize',()=>apply(preferred));apply(preferred);
})();

function validPlotSlice(value){
 return !!value&&Array.isArray(value.axes)&&value.axes.length>=1&&value.axes.length<=2&&value.axes.every(a=>typeof a==='string')&&new Set(value.axes).size===value.axes.length&&value.fixed&&typeof value.fixed==='object'&&!Array.isArray(value.fixed)&&Object.values(value.fixed).every(v=>typeof v==='number'&&Number.isFinite(v)&&Math.abs(v)<=1e6);
}
function renderSliceControls(box,row,result){
 const params=result.function.parameters,config=result.plot_slice||(validPlotSlice(row.plotSlice)?row.plotSlice:{axes:params.slice(0,2),fixed:Object.fromEntries(params.slice(2).map(p=>[p,0]))});
 const panel=document.createElement('details');panel.className='slice-controls';panel.open=!!row.sliceOpen;panel.ontoggle=()=>{row.sliceOpen=panel.open;};
 const summary=document.createElement('summary');summary.textContent='Plot inputs: '+config.axes.join(', ')+(Object.keys(config.fixed).length?' · '+Object.entries(config.fixed).map(([p,v])=>`${p}=${fmt(v)}`).join(', '):'');panel.append(summary);
 const fields=document.createElement('div');fields.className='slice-fields';
 const makeAxis=(title,current,allowNone)=>{const label=document.createElement('label');label.textContent=title;const select=document.createElement('select');if(allowNone){const opt=document.createElement('option');opt.value='';opt.textContent='None — curve / domain';select.append(opt);}for(const p of params){const opt=document.createElement('option');opt.value=p;opt.textContent=p;select.append(opt);}select.value=current||'';label.append(select);fields.append(label);return select;};
 const first=makeAxis('First plot input',config.axes[0],false),second=makeAxis('Second plot input',config.axes[1],true);
 const applyAxes=()=>{if(second.value===first.value)second.value='';const axes=[first.value,second.value].filter(Boolean);row.plotSlice={axes,fixed:Object.fromEntries(params.filter(p=>!axes.includes(p)).map(p=>[p,config.fixed[p]??0]))};if(view==='surface'&&axes.length===1)view='graph';else if(axes.length===2&&['complex','domain'].includes(view))view='surface';schedule(0);};
 first.onchange=second.onchange=applyAxes;
 for(const p of params.filter(p=>!config.axes.includes(p))){const label=document.createElement('label');label.textContent='Hold '+p+' at';const input=document.createElement('input');input.type='number';input.step='any';input.min=-1e6;input.max=1e6;input.value=config.fixed[p]??0;input.onchange=()=>{const value=Number(input.value);if(!input.value.trim()||!Number.isFinite(value)||Math.abs(value)>1e6){input.setCustomValidity('Use a finite real number within ±1,000,000.');input.reportValidity();return;}input.setCustomValidity('');row.plotSlice={axes:[...config.axes],fixed:{...config.fixed,[p]:value}};schedule(0);};label.append(input);fields.append(label);}
 const note=document.createElement('p');note.className='muted';note.textContent='Choose one input for a curve or complex domain, or two for a surface. Other inputs stay at the values above.';panel.append(fields,note);box.append(panel);
}
// Convert before field-specific input handlers run; defer words still being typed.
(() => {
 const selector='#waveletSource, #waveletTime, #waveletOutputName, #probabilityParameters input, #probabilityName, #probabilitySource, #probabilityArg, #probabilityArg2, #graphFields textarea, #graphParameter, .expression textarea, #matrixGrid input, #matrixName, #functionName, #functionArgs, #functionBody, #functionCalcVariable, #functionIntegralLower, #functionIntegralUpper, #linearMatrix, #linearRhs, #calculusArguments, #calculusExpression, #calculusLower, #calculusUpper, #calculusName, #calculusPoint, #calculusDirection, #calculusStep, #calculusAbsTol, #calculusRelTol, #qubitAlpha, #qubitBeta, #qubitName';
 document.addEventListener('input',e=>{if(e.target.matches(selector)&&!e.isComposing)GreekInput.apply(e.target,e.inputType==='insertFromPaste');},true);
 const finish=e=>{if(e.target.matches(selector)&&GreekInput.apply(e.target,true))e.target.dispatchEvent(new Event('input',{bubbles:true}));};
 document.addEventListener('focusout',finish);document.addEventListener('compositionend',finish);
})();

let datasetDraft=null,datasetRevision=0;
function renderDatasets(){
 $('datasetsPanel').hidden=!datasets.length;$('datasetsSummary').textContent=`Datasets (${datasets.length})`;$('datasetsList').replaceChildren();
 datasets.forEach(d=>{
  const card=document.createElement('article');card.className='dataset-card';
  const title=document.createElement('strong');title.textContent=d.name+' · '+d.columns[0].values.length+' rows';card.append(title);
  const actions=document.createElement('div');actions.className='dataset-actions';
  const toggle=document.createElement('button');toggle.textContent=d.visible?'Hide plot':'Show plot';toggle.onclick=()=>{d.visible=!d.visible;renderDatasets();saveLocal();drawPlot();};actions.append(toggle);
  const fit=document.createElement('button');fit.textContent='Fit plot';fit.onclick=()=>{try{bounds=DatasetTools.fit([{...d,visible:true}]);d.visible=true;view='graph';renderDatasets();schedule(0);}catch(error){toast(error.message);}};actions.append(fit);
  const wavelet=document.createElement('button');wavelet.textContent='Wavelets';wavelet.onclick=()=>openWavelets(d.name+'_'+d.y[0],d.x?d.name+'_'+d.x:'');actions.append(wavelet);
  const remove=document.createElement('button');remove.textContent='Remove';remove.onclick=()=>{datasets=datasets.filter(v=>v.id!==d.id);renderDatasets();schedule(0);};actions.append(remove);card.append(actions);
  const xLabel=document.createElement('label');xLabel.textContent='X ';const xSelect=document.createElement('select');const index=document.createElement('option');index.value='';index.textContent='Row index';xSelect.append(index);for(const c of d.columns){const opt=document.createElement('option');opt.value=c.name;opt.textContent=c.label;xSelect.append(opt);}xSelect.value=d.x??'';xSelect.onchange=()=>{d.x=xSelect.value||null;saveLocal();drawPlot();};xLabel.append(xSelect);card.append(xLabel);
  const style=document.createElement('select');style.setAttribute('aria-label','Dataset plot style');for(const [value,label] of [['markers','Points'],['lines','Lines'],['lines+markers','Lines & points']]){const opt=document.createElement('option');opt.value=value;opt.textContent=label;style.append(opt);}style.value=d.style;style.onchange=()=>{d.style=style.value;saveLocal();drawPlot();};card.append(style);
  const note=document.createElement('p');note.className='muted';note.textContent='Choose Y columns; click a variable to add an equation.';card.append(note);
  for(const c of d.columns){const line=document.createElement('div');line.className='dataset-column';const check=document.createElement('input');check.type='checkbox';check.checked=d.y.includes(c.name);check.setAttribute('aria-label','Plot '+c.label);check.onchange=()=>{const next=check.checked?[...d.y,c.name]:d.y.filter(k=>k!==c.name);if(!next.length||next.length>8){check.checked=!check.checked;toast('Choose 1–8 Y columns.');return;}d.y=next;saveLocal();drawPlot();};const button=document.createElement('button');button.textContent=d.name+'_'+c.name;button.title='Add column expression';button.onclick=()=>addExpression(d.name+'_'+c.name);line.append(check,button);card.append(line);}
  $('datasetsList').append(card);
 });
}
function invalidateDataset(){datasetRevision++;datasetDraft=null;$('datasetPreviewArea').hidden=true;$('datasetAddBtn').disabled=true;$('datasetImportError').textContent='';}
$('dataImportBtn').onclick=()=>{invalidateDataset();$('datasetText').value='';$('datasetFile').value='';$('datasetHeader').checked=true;$('datasetDelimiter').value='auto';$('datasetDecimal').value='.';let n=1;while(datasets.some(d=>d.name==='data_'+n))n++;$('datasetName').value='data_'+n;$('datasetDialog').showModal();};
$('datasetFile').onchange=async e=>{const file=e.target.files[0];if(!file)return;invalidateDataset();const revision=datasetRevision;try{if(file.size>DatasetTools.limits.bytes)throw Error('Choose a CSV or TSV file up to 1 MB.');const text=await file.text();if(revision!==datasetRevision)return;$('datasetText').value=text;await previewDataset();}catch(error){if(revision===datasetRevision)$('datasetImportError').textContent=error.message;}};
$('datasetText').oninput=invalidateDataset;for(const id of ['datasetDelimiter','datasetDecimal','datasetHeader'])$(id).onchange=invalidateDataset;
function datasetSelections(){return [...$('datasetColumns').querySelectorAll('.dataset-import-column')].filter(el=>el.querySelector('input[type=checkbox]').checked).map(el=>({index:Number(el.dataset.index),name:el.querySelector('input[type=text]').value}));}
function updateDatasetAxes(){
 const selected=datasetSelections(),hadAxes=$('datasetX').options.length>0,oldX=$('datasetX').value,oldY=[...$('datasetY').querySelectorAll('input:checked')].map(el=>el.value);$('datasetX').replaceChildren();$('datasetY').replaceChildren();const index=document.createElement('option');index.value='';index.textContent='Row index (0, 1, 2, …)';$('datasetX').append(index);
 for(const c of selected){const opt=document.createElement('option');opt.value=c.index;opt.textContent=c.name;$('datasetX').append(opt);const label=document.createElement('label'),check=document.createElement('input');check.type='checkbox';check.value=c.index;check.checked=oldY.includes(String(c.index));label.append(check,document.createTextNode(c.name));$('datasetY').append(label);}
 $('datasetX').value=hadAxes&&oldX===''?'':selected.some(c=>String(c.index)===oldX)?oldX:selected.length>1?String(selected[0].index):'';
 if(!$('datasetY').querySelector('input:checked')&&selected.length)$('datasetY').querySelectorAll('input')[selected.length>1?1:0].checked=true;
 $('datasetAddBtn').disabled=!selected.length;
}
async function previewDataset(){
 invalidateDataset();const revision=datasetRevision,button=$('datasetPreviewBtn');button.disabled=true;
 try{const delimiter=$('datasetDelimiter').value;const res=await fetch('/api/datasets/preview',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({text:$('datasetText').value,delimiter:delimiter==='tab'?'\t':delimiter,decimal:$('datasetDecimal').value,header:$('datasetHeader').checked})});const data=await res.json();if(revision!==datasetRevision)return;if(!res.ok)throw Error(data.error||'Could not read the table.');datasetDraft=data;
 $('datasetPreviewSummary').textContent=`${data.rows} rows · ${data.columns.length} columns · preview of first ${data.preview.length} rows. Non-numeric columns are disabled.`;
 const table=document.createElement('table'),head=document.createElement('tr');for(const c of data.columns){const th=document.createElement('th');th.textContent=c.label;head.append(th);}table.append(head);for(const row of data.preview){const tr=document.createElement('tr');for(const cell of row){const td=document.createElement('td');td.textContent=cell||'—';tr.append(td);}table.append(tr);}$('datasetTable').replaceChildren(table);
 $('datasetColumns').replaceChildren();data.columns.forEach((c,i)=>{const line=document.createElement('label');line.className='dataset-import-column';line.dataset.index=i;const check=document.createElement('input');check.type='checkbox';check.checked=c.numeric;check.disabled=!c.numeric;check.onchange=updateDatasetAxes;const name=document.createElement('input');name.type='text';name.value=c.name;name.maxLength=60;name.disabled=!c.numeric;name.setAttribute('aria-label','Variable name for '+c.label);name.oninput=updateDatasetAxes;const note=document.createElement('span');note.textContent=c.invalid?c.invalid+' nonnumeric cells':c.numeric?c.missing+' missing cells':'No numeric values';line.append(check,name,note);$('datasetColumns').append(line);});
 $('datasetPreviewArea').hidden=false;$('datasetX').replaceChildren();$('datasetY').replaceChildren();updateDatasetAxes();
 }catch(error){if(revision===datasetRevision)$('datasetImportError').textContent=error.message;}finally{button.disabled=false;}
}
$('datasetPreviewBtn').onclick=previewDataset;
$('datasetForm').onsubmit=async e=>{
 e.preventDefault();if(!datasetDraft)return;const button=$('datasetAddBtn'),revision=datasetRevision;button.disabled=true;
 try{const selected=datasetSelections(),names=new Map(selected.map(c=>[String(c.index),c.name]));const item={id:uid(),name:$('datasetName').value,columns:selected.map(c=>({name:c.name,label:datasetDraft.columns[c.index].label,values:datasetDraft.columns[c.index].values})),x:$('datasetX').value===''?null:names.get($('datasetX').value),y:[...$('datasetY').querySelectorAll('input:checked')].map(el=>names.get(el.value)),style:$('datasetStyle').value,visible:true};
 const proposed=DatasetTools.validate([...datasets,item]);const res=await fetch('/api/evaluate',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({datasets:proposed,expressions:rows.map(r=>({text:r.text})),bounds})});const data=await res.json();if(!res.ok)throw Error(data.error||'Could not import dataset.');const addedBindings=proposed.at(-1).columns.map(c=>proposed.at(-1).name+'_'+c.name);const duplicate=data.results.find(r=>addedBindings.some(name=>r.error===`Name ${name} is reserved or already defined.`));if(duplicate)throw Error('A dataset column conflicts with a worksheet definition. Choose another dataset or column name.');if(revision!==datasetRevision)return;
 datasets=proposed;view='graph';try{bounds=DatasetTools.fit([datasets.at(-1)]);}catch(error){toast(error.message);}renderDatasets();$('datasetsPanel').open=true;$('datasetDialog').close();schedule(0);
 }catch(error){if(revision===datasetRevision)$('datasetImportError').textContent=error.message;}finally{button.disabled=!datasetDraft;}
};

$('datasetForm').addEventListener('input',e=>{if(e.target.matches('#datasetName, #datasetColumns input, #datasetX, #datasetY input, #datasetStyle')){datasetRevision++;$('datasetImportError').textContent='';}});

document.querySelectorAll('[data-calculus-insert]').forEach(button=>button.onclick=()=>{
 let target=symbolTarget;if(!target?.matches('.expression textarea, #functionBody, #calculusExpression')){if(!rows.length)addExpression();target=$('expressions').querySelector('textarea');}
 const start=target.selectionStart??target.value.length,end=target.selectionEnd??start,selected=target.value.slice(start,end);
 const text=button.dataset.calculusInsert==='derivative'?`d/dx(${selected||'f(x)'})`:`∫_{0}^{x} (${selected||'f(t)'}) dt`;
 target.setRangeText(text,start,end,'end');target.dispatchEvent(new Event('input',{bubbles:true}));target.focus();
});

let linearReport=null,linearRevision=0;
function openLinearAlgebra(index=null){
 const matrices=results.map((r,i)=>({r,i})).filter(({r})=>r.kind==='matrix'&&!r.error&&!r.empty_basis),chosen=index===null?matrices[0]:{r:results[index],i:index};
 $('linearMatrix').value=chosen?(chosen.r.name||rows[chosen.i].text):'[[2,1],[1,3]]';$('linearRhs').value='';$('linearOperation').value='overview';invalidateLinear();$('linearDialog').showModal();analyzeLinear();
}
function invalidateLinear(){linearRevision++;linearReport=null;$('linearOutput').replaceChildren();$('linearError').textContent='';}
function linearValue(parent,title,packed,expression){
 const section=document.createElement('section');section.className='linear-value';const heading=document.createElement('h3');heading.textContent=title;section.append(heading);
 if(packed.shape.includes(0)){const note=document.createElement('p');note.textContent='Empty basis: this subspace has dimension zero.';section.append(note);}
 else if(packed.shape.length===2){const table=document.createElement('table');for(const row of packed.value){const tr=document.createElement('tr');for(const value of row){const td=document.createElement('td');td.textContent=value===null?'undefined':fmt(value);tr.append(td);}table.append(tr);}section.append(table);}
 else{const text=document.createElement('div');text.className='result-value';text.textContent=Array.isArray(packed.value)?'['+packed.value.map(fmt).join(', ')+']':packed.value===null?'undefined (non-finite)':fmt(packed.value);section.append(text);}
 if(expression){const button=document.createElement('button');button.type='button';button.textContent='Add to worksheet';button.onclick=()=>{if(rows.length>=40){toast('Maximum 40 expressions.');return;}addExpression(expression);};section.append(button);}parent.append(section);
}
function renderLinear(){
 const output=$('linearOutput');output.replaceChildren();if(!linearReport)return;
 const {analysis:a,expression,rhs}=linearReport,operation=$('linearOperation').value;
 const note=text=>{const p=document.createElement('p');p.className='muted';p.textContent=text;output.append(p);};
 const value=(title,packed,call)=>linearValue(output,title,packed,call?`${call}(${expression})`:null);
 if(operation==='overview'){
  note(`${a.shape[0]} × ${a.shape[1]} · rank ${a.rank} · nullity ${a.nullity} · Frobenius norm ${fmt(a.norm)} · condition ${a.condition===null?'∞ (rank deficient)':fmt(a.condition)}`);
  if(a.hermitian!==undefined)note(`Hermitian: ${a.hermitian?'yes':'no'} · unitary: ${a.unitary?'yes':'no'}`);
  if(a.determinant){value('Determinant',a.determinant,'det');value('Trace',a.trace,'trace');}value('Singular values',a.singular_values,'singular_values');
 }else if(operation==='eigen'){
  if(!a.eigen){note('Eigenvalues and eigenvectors require a square matrix. Use SVD for a rectangular matrix.');return;}
  value('Eigenvalues λ',a.eigen.values,'eigvals');value('Eigenvectors V (one eigenvector per column)',a.eigen.vectors,'eigvecs');
  note(`Columns correspond to eigenvalues in the displayed order: A V = V diag(λ). Scaled residual ${a.eigen.residual.toExponential(3)}. Eigenvector basis rank ${a.eigen.basis_rank}.`);
  note(a.eigen.diagonalizable?`A complete eigenvector basis was found numerically; its condition number is ${fmt(a.eigen.condition)}. Repeated eigenvalues can have different valid bases.`:'The eigenvector matrix is rank deficient numerically; these vectors do not form a diagonalizing basis. SVD remains available.');
 }else if(['svd','qr','lu'].includes(operation)){
  const spec={svd:{identity:'A = U S V† (economy SVD)',parts:[['U','svdU'],['S','svdS'],['Vh','svdVh']]},qr:{identity:'A = Q R (reduced QR)',parts:[['Q','qrQ'],['R','qrR']]},lu:{identity:'A = P L U',parts:[['P','luP'],['L','luL'],['U','luU']]}}[operation];note(spec.identity);
  for(const [part,call] of spec.parts)value(part,a[operation][part],call);note('Scaled reconstruction residual: '+a[operation].residual.toExponential(3));
 }else if(operation==='cholesky'){
  if(!a.cholesky||a.cholesky.error){note(a.cholesky?.error||'Cholesky requires a square Hermitian positive-definite matrix.');return;}
  note('A = L L†');value('Lower-triangular factor L',a.cholesky.L,'cholesky');note('Scaled reconstruction residual: '+a.cholesky.residual.toExponential(3));
 }else if(operation==='spaces'){
  value('Orthonormal column-space basis',a.column_basis,'orth');value('Orthonormal null-space basis',a.null_basis,'nullspace');note('Basis vectors occupy columns. Rank and nullity use a floating-point singular-value tolerance. An empty null-space basis means only the zero vector solves A v = 0.');
 }else if(operation==='solve'){
  if(!a.solution){note('Enter a right-hand side b above, then choose Analyze.');return;}
  linearValue(output,'Least-squares solution x',a.solution.x,`lstsq(${expression}, ${rhs})`);note(`Residual ‖A x − b‖: ${a.solution.residual.toExponential(3)}. ${a.solution.exact_within_tolerance?'Consistent within numerical tolerance.':'No exact fit at numerical tolerance; this is the least-squares fit.'} Rank-deficient or underdetermined systems use the minimum-norm solution.`);
 }
}
async function analyzeLinear(){
 const revision=linearRevision,button=$('linearAnalyzeBtn'),expression=GreekInput.normalize($('linearMatrix').value.trim()),rhs=GreekInput.normalize($('linearRhs').value.trim());button.disabled=true;
 try{const res=await fetch('/api/linear-algebra',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({matrix:expression,rhs,expressions:rows.map(r=>({text:r.text})),datasets})});const data=await res.json();if(revision!==linearRevision)return;if(!res.ok)throw Error(data.error||'Could not analyze matrix.');linearReport={analysis:data.analysis,expression,rhs};$('linearError').textContent='';renderLinear();}catch(error){if(revision===linearRevision)$('linearError').textContent=error.message;}finally{button.disabled=false;}
}
$('linearBtn').onclick=()=>openLinearAlgebra();$('linearAnalyzeBtn').onclick=analyzeLinear;$('linearOperation').onchange=renderLinear;
$('linearMatrix').oninput=$('linearRhs').oninput=invalidateLinear;

// Named graph collection. Specifications share the worksheet's definitions and data.
function renderGraphs(){
 const list=$('graphsList');list.replaceChildren();$('graphsPanel').hidden=!graphs.length;$('graphsSummary').textContent=`My graphs · ${graphs.length}`;
 const selector=$('graphSelection');selector.replaceChildren();
 for(const [value,label] of [['2d','All 2D graphs'],['3d','All 3D graphs'],...graphs.map(g=>[g.id,g.name])]){const o=document.createElement('option');o.value=value;o.textContent=label;selector.append(o);}
 if(!['2d','3d',...graphs.map(g=>g.id)].includes(graphSelection))graphSelection='2d';selector.value=graphSelection;
 for(const g of graphs){
  const card=document.createElement('article');card.className='saved-graph';card.style.setProperty('--graph-color',g.color);
  const top=document.createElement('div');top.className='saved-graph-actions';
  const visible=document.createElement('input');visible.type='checkbox';visible.checked=g.visible;visible.setAttribute('aria-label',`Show ${g.name}`);visible.onchange=()=>{g.visible=visible.checked;renderGraphs();drawPlot();schedule(0);};
  const name=document.createElement('button');name.className='saved-graph-name';name.textContent=g.name;name.title='Display this graph';name.onclick=()=>{graphSelection=g.id;selectView('created');renderGraphs();};
  const edit=document.createElement('button');edit.textContent='Edit';edit.onclick=()=>openGraph(g.id);
  const remove=document.createElement('button');remove.textContent='×';remove.setAttribute('aria-label',`Delete graph ${g.name}`);remove.onclick=()=>{graphs=graphs.filter(v=>v.id!==g.id);graphResults=graphResults.filter(v=>v.id!==g.id);renderGraphs();schedule(0);};const rename=document.createElement('button');rename.textContent='Rename';rename.onclick=()=>openGraphRename(g.id);top.append(visible,name,rename,edit,remove);card.append(top);
  const detail=document.createElement('p');detail.className='muted';detail.textContent=GraphTools.types[g.type].label;card.append(detail);
  const r=graphResults.find(r=>r.id===g.id);
  if(r?.error){const error=document.createElement('p');error.className='error';error.textContent=r.error;card.append(error);}
  else if(r&&(r.gaps||r.omitted)){const note=document.createElement('p');note.className='muted';note.textContent=`${r.gaps||r.omitted} undefined or missing ${r.gaps?'samples':'observations'} omitted.`;card.append(note);}
  list.append(card);
 }
}
function populateGraph(g){
 const config=GraphTools.types[g.type];$('graphType').value=g.type;$('graphName').value=g.name;$('graphColor').value=g.color;
 $('graphParameter').value=g.parameter;$('graphMin').value=g.range[0];$('graphMax').value=g.range[1];$('graphYMin').value=g.yrange[0];$('graphYMax').value=g.yrange[1];$('graphSamples').value=g.samples;$('graphBins').value=g.bins;$('graphProbabilityMode').value=g.probability_mode||'density';
 const fields=$('graphFields');fields.replaceChildren();
 for(const [key,title] of Object.entries(config.fields)){
  const label=document.createElement('label');label.className='body-label';label.textContent=title;const input=document.createElement('textarea');input.id='graphField_'+key;input.dataset.field=key;input.rows=2;input.maxLength=1200;input.spellcheck=false;input.value=g[key];input.required=!(config.data&&key==='x');input.oninput=updateGraphPreview;label.append(input);fields.append(label);
 }
 $('graphRangeFields').hidden=!!config.data;$('graphYRangeFields').hidden=!config.grid;$('graphParameterLabel').hidden=!!config.grid||g.type==='function';$('graphSamplesLabel').hidden=!!config.grid;$('graphBinsLabel').hidden=g.type!=='histogram';$('graphProbabilityLabel').hidden=g.type!=='probability';if(g.type==='probability'){$('graphParameterLabel').hidden=true;$('graphSamplesLabel').hidden=true;}
 for(const id of ['graphMin','graphMax'])$(id).required=!config.data;
 for(const id of ['graphYMin','graphYMax'])$(id).required=!!config.grid;
 $('graphSamples').required=!config.data&&!config.grid;$('graphBins').required=g.type==='histogram';
 $('graphRangeLabel').textContent=config.grid||g.type==='function'?'x minimum':'Parameter minimum';
 $('graphDescription').textContent=config.data?'Enter numeric vectors or imported column names. Paired charts preserve missing-value alignment and input order.':config.grid?'Sample a real x/y grid. Implicit curves trace the zero level; surfaces and contours show the formula value.':'Enter coordinate formulas and a sampling interval. Polar angles use radians; coordinate formulas can call your worksheet functions.';
 updateGraphPreview();
}
function openGraph(id=null){
 if(id===null&&graphs.length>=12){toast('Maximum 12 saved graphs.');return;}
 graphEdit=id;graphRevision++;$('graphDialogTitle').textContent=id?'Edit graph':'Create graph';$('graphApplyBtn').textContent=id?'Apply changes':'Create graph';
 populateGraph(id?graphs.find(g=>g.id===id):GraphTools.fresh('function',uid(),colors[graphs.length%colors.length]));$('graphDialog').showModal();
}
function updateGraphPreview(){
 graphRevision++;$('graphError').textContent='';const fields=[...$('graphFields').querySelectorAll('textarea')];
 const source=fields.length===1?fields[0].value:'['+fields.map(input=>input.value).join(', ')+']';renderMath($('graphFormulaPreview'),source);
}
function graphDraft(){
 const type=$('graphType').value,g=GraphTools.fresh(type,graphEdit||uid(),$('graphColor').value),existing=graphs.find(g=>g.id===graphEdit);
 g.visible=existing?.visible??true;g.name=$('graphName').value.trim();g.parameter=GreekInput.normalize($('graphParameter').value.trim());
 g.range=[Number($('graphMin').value),Number($('graphMax').value)];g.yrange=[Number($('graphYMin').value),Number($('graphYMax').value)];g.samples=Number($('graphSamples').value);g.bins=Number($('graphBins').value);g.probability_mode=$('graphProbabilityMode').value;
 for(const input of $('graphFields').querySelectorAll('textarea'))g[input.dataset.field]=GreekInput.normalize(input.value.trim());
 return GraphTools.validate([g])[0];
}
for(const [value,config] of Object.entries(GraphTools.types)){const option=document.createElement('option');option.value=value;option.textContent=config.label;$('graphType').append(option);}
$('createGraphBtn').onclick=()=>openGraph();
$('graphType').onchange=()=>{const color=$('graphColor').value;populateGraph(GraphTools.fresh($('graphType').value,graphEdit||uid(),color));};
$('graphForm').addEventListener('input',()=>{graphRevision++;$('graphError').textContent='';});
$('graphDialog').addEventListener('close',()=>graphRevision++);
$('graphSelection').onchange=e=>{graphSelection=e.target.value;saveLocal();drawPlot();};
$('graphForm').onsubmit=async e=>{
 e.preventDefault();const revision=graphRevision,worksheetRevision=requestId,button=$('graphApplyBtn');button.disabled=true;
 try{
  const g=graphDraft();const res=await fetch('/api/graphs',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({graphs:[{...g,visible:true}],expressions:rows.map(r=>({text:r.text})),datasets})});const data=await res.json();
  if(revision!==graphRevision)return;
  if(worksheetRevision!==requestId)throw Error('The worksheet changed during validation. Apply the graph again to use the latest definitions.');
  if(!res.ok)throw Error(data.error||'Could not create graph.');if(data.results[0].error)throw Error(data.results[0].error);
  if(graphEdit){const index=graphs.findIndex(v=>v.id===graphEdit);if(index<0)throw Error('This graph was removed. Create a new graph.');graphs[index]=g;}else{if(graphs.length>=12)throw Error('Maximum 12 saved graphs.');graphs.push(g);}
  graphResults=graphResults.filter(v=>v.id!==g.id);graphResults.push(data.results[0]);graphSelection=GraphTools.is3d(g)?'3d':'2d';view='created';$('graphDialog').close();renderGraphs();drawPlot();schedule(0);
 }catch(error){if(revision===graphRevision)$('graphError').textContent=error.message;}finally{button.disabled=false;}
};

const probabilityFamilies={
 normal:{fields:[['Mean μ','0'],['Standard deviation σ','1']],hint:'A continuous normal distribution. σ is the standard deviation, not the variance.'},
 boltzmann:{fields:[['Energy levels','[0,1,2]'],['Temperature T','1']],hint:'Finite states k = 0, 1, … with P(k) proportional to exp(−E[k]/T), using k_B = 1. Repeated energy levels represent distinct states.'},
 poisson:{fields:[['Rate λ','4']],hint:'Nonnegative integer event counts with mean and variance λ.'},
 binomial:{fields:[['Trials n','10'],['Success probability p','0.5']],hint:'Number of successes in n independent trials, each with probability p.'},
 uniform:{fields:[['Lower bound a','0'],['Upper bound b','1']],hint:'A continuous uniform distribution on [a,b].'},
 exponential:{fields:[['Rate λ','1']],hint:'A continuous waiting time with mean 1/λ. The parameter is the rate.'},
 geometric:{fields:[['Success probability p','0.5']],hint:'Trial number of the first success: support 1, 2, 3, … .'}
};
let probabilityEdit=null,probabilityRevision=0,probabilityReport=null;
function invalidateProbability(){probabilityRevision++;probabilityReport=null;$('probabilityDensityGraph').disabled=$('probabilityCdfGraph').disabled=true;$('probabilityError').textContent='';$('probabilitySummary').replaceChildren();if(window.Plotly)Plotly.purge('probabilityPlot');renderMath($('probabilityPreview'),$('probabilitySource').value);}
function probabilityFromFields(){
 $('probabilitySource').value=$('probabilityFamily').value+'('+[...$('probabilityParameters').querySelectorAll('input')].map(input=>GreekInput.normalize(input.value.trim())).join(', ')+')';invalidateProbability();
}
function populateProbability(family,parameters=null){
 $('probabilityFamily').value=family;const config=probabilityFamilies[family],container=$('probabilityParameters');container.replaceChildren();
 config.fields.forEach(([title,value],i)=>{const label=document.createElement('label');label.textContent=title;const input=document.createElement('input');input.maxLength=1000;input.value=parameters?(Array.isArray(parameters[i])?'['+parameters[i].join(',')+']':parameters[i]):value;input.oninput=probabilityFromFields;label.append(input);container.append(label);});$('probabilityFamilyHint').textContent=config.hint;probabilityFromFields();
}
function openProbability(index=null){
 probabilityEdit=index===null?null:rows[index].id;const d=index===null?null:results[index]?.distribution;
 populateProbability(d?.family||'normal',d?.parameters||null);
 if(index!==null){$('probabilitySource').value=rows[index].text.includes('=')?rows[index].text.slice(rows[index].text.indexOf('=')+1).trim():rows[index].text;$('probabilityName').value=results[index].name||'D';}
 else{let name='D',i=1;while(rows.some(r=>r.text.match(new RegExp('^\\s*'+name+'\\s*='))))name='D_'+i++;$('probabilityName').value=name;}
 $('probabilityApply').textContent=index===null?'Add definition':'Apply definition';$('probabilityMin').value=$('probabilityMax').value='';$('probabilityOperation').value='cdf';$('probabilityArg').value='0';$('probabilityArg2').value='1';probabilityQueryFields();invalidateProbability();$('probabilityDialog').showModal();analyzeProbability();
}
function probabilityQueryFields(){const op=$('probabilityOperation').value;$('probabilityArgLabel').textContent=op==='prob'?'Lower bound a':op==='quantile'?'Probability q':'x';$('probabilityArg2Label').hidden=op!=='prob';invalidateProbability();}
function probabilityPayload(){
 const source=GreekInput.normalize($('probabilitySource').value.trim()),lo=$('probabilityMin').value,hi=$('probabilityMax').value;
 if((lo==='')!==(hi===''))throw Error('Enter both plot bounds or leave both blank.');
 return {distribution:source,expressions:rows.map(r=>({text:r.text})),datasets,...(lo!==''?{range:[Number(lo),Number(hi)]}:{})};
}
async function analyzeProbability(){
 const revision=probabilityRevision,worksheetRevision=requestId,button=$('probabilityAnalyze');button.disabled=true;
 try{
  const payload=probabilityPayload(),operation=$('probabilityOperation').value,args=[GreekInput.normalize($('probabilityArg').value.trim())];if(operation==='prob')args.push(GreekInput.normalize($('probabilityArg2').value.trim()));
  // Determine continuous/discrete density from the evaluated distribution, including named references.
  const request=async body=>{const res=await fetch('/api/probability',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(body)});const data=await res.json();if(!res.ok)throw Error(data.error||'Could not calculate probability.');return data.analysis;};
  let report;if(operation==='density'){report=await request(payload);report=await request({...payload,query:{operation:report.discrete?'pmf':'pdf',arguments:args}});}else report=await request({...payload,query:{operation,arguments:args}});
  if(revision!==probabilityRevision||worksheetRevision!==requestId)return;
  probabilityReport={report,source:payload.distribution,worksheetRevision};const summary=$('probabilitySummary');summary.replaceChildren();
  const answer=document.createElement('p');answer.className='probability-answer';answer.textContent='Result: '+(report.query.nonfinite?'non-finite (endpoint quantiles may be infinite)':fmt(report.query.value));summary.append(answer);
  const stats=document.createElement('p');stats.textContent=`${report.family} · mean ${fmt(report.mean)} · variance ${fmt(report.variance)} · standard deviation ${fmt(report.std)} · entropy ${fmt(report.entropy)} nats`;summary.append(stats);
  if(report.family==='boltzmann'){const note=document.createElement('p');note.textContent=`Mean energy ${fmt(report.expected_energy)} · state probabilities [${report.probabilities.map(fmt).join(', ')}]. Mean and variance above refer to the state index.`;summary.append(note);}
  const layout={margin:{l:50,r:20,t:20,b:40},xaxis:{title:{text:report.discrete?'Outcome / state index':'x'}},yaxis:{title:{text:report.discrete?'Probability mass':'Density'}},showlegend:false};applyPlotTheme(layout);
  await Plotly.react('probabilityPlot',[{type:report.discrete?'bar':'scatter',mode:'lines',x:report.plot.x,y:report.plot.y,marker:{color:'#2864d7'},line:{color:'#2864d7'},connectgaps:false}],layout,{responsive:true,displayModeBar:false});
  if(revision===probabilityRevision){$('probabilityDensityGraph').disabled=$('probabilityCdfGraph').disabled=false;}
 }catch(error){if(revision===probabilityRevision)$('probabilityError').textContent=error.message;}finally{button.disabled=false;}
}
$('probabilityBtn').onclick=()=>openProbability();$('probabilityFamily').onchange=()=>populateProbability($('probabilityFamily').value);
$('probabilitySource').oninput=invalidateProbability;$('probabilityOperation').onchange=probabilityQueryFields;
for(const id of ['probabilityArg','probabilityArg2','probabilityMin','probabilityMax','probabilityName'])$(id).oninput=invalidateProbability;
$('probabilityDialog').addEventListener('close',()=>{probabilityRevision++;});$('probabilityAnalyze').onclick=analyzeProbability;
$('probabilityApply').onclick=async()=>{
 const revision=probabilityRevision,worksheetRevision=requestId,button=$('probabilityApply');button.disabled=true;
 try{
  const text=GreekInput.normalize($('probabilityName').value.trim())+' = '+GreekInput.normalize($('probabilitySource').value.trim());
  const index=probabilityEdit===null?rows.length:rows.findIndex(r=>r.id===probabilityEdit);if(index<0)throw Error('The source row was removed.');if(index===rows.length&&rows.length>=40)throw Error('Maximum 40 expressions.');
  const candidate=rows.map(r=>({text:r.text}));candidate[index]={text};
  const res=await fetch('/api/evaluate',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({expressions:candidate,datasets,bounds})});const data=await res.json();
  if(revision!==probabilityRevision)return;if(worksheetRevision!==requestId)throw Error('The worksheet changed. Apply the definition again.');if(!res.ok)throw Error(data.error||'Could not add distribution.');const result=data.results[index];if(result.error||result.kind!=='distribution')throw Error(result.error||'Enter a valid named distribution.');
  if(index===rows.length)rows.push(newRow(text));else rows[index].text=text;$('probabilityDialog').close();renderRows();schedule(0);
 }catch(error){if(revision===probabilityRevision)$('probabilityError').textContent=error.message;}finally{button.disabled=false;}
};
function saveProbabilityGraph(mode){
 try{
  if(!probabilityReport)throw Error('Calculate the distribution first.');if(probabilityReport.worksheetRevision!==requestId)throw Error('The worksheet changed. Calculate again before saving the graph.');if(graphs.length>=12)throw Error('Maximum 12 saved graphs.');
  const {report,source}=probabilityReport,g=GraphTools.fresh('probability',uid(),colors[graphs.length%colors.length]);g.name=$('probabilityName').value.trim()+' · '+(mode==='cdf'?'CDF':report.discrete?'PMF':'PDF');g.expression=source;g.range=report.plot.range;g.probability_mode=mode;
  const validated=GraphTools.validate([g])[0];graphs.push(validated);graphSelection='2d';view='created';$('probabilityDialog').close();renderGraphs();schedule(0);
 }catch(error){$('probabilityError').textContent=error.message;}
}
$('probabilityDensityGraph').onclick=()=>saveProbabilityGraph('density');$('probabilityCdfGraph').onclick=()=>saveProbabilityGraph('cdf');

let waveletRevision=0,waveletReport=null,waveletContextId=0,waveletInputLabel='Pasted samples';
const waveletFields={source:'waveletSource',time:'waveletTime',dt:'waveletDt',unit:'waveletUnit',missing:'waveletMissing',resample:'waveletResample',detrend:'waveletDetrend',cwt_wavelet:'waveletCwt',dwt_wavelet:'waveletDwt',level:'waveletLevel',boundary:'waveletBoundary',strength:'waveletStrength',threshold_mode:'waveletThresholdMode',min_scale:'waveletScaleMin',max_scale:'waveletScaleMax',scale_count:'waveletScaleCount'};
function invalidateWavelets(){waveletRevision++;waveletReport=null;$('waveletResults').hidden=true;$('waveletError').textContent='';}
function fillWaveletSettings(s){for(const [key,id] of Object.entries(waveletFields)){if(key==='resample')$(id).checked=s[key];else $(id).value=s[key]??'';}}
function readWaveletSettings(){const s={};for(const [key,id] of Object.entries(waveletFields)){if(key==='resample')s[key]=$(id).checked;else if(['dt','level','strength','min_scale','max_scale','scale_count'].includes(key))s[key]=['level','max_scale'].includes(key)&&$(id).value===''?null:Number($(id).value);else s[key]=$(id).value.trim();}s.source=GreekInput.normalize(s.source);s.time=GreekInput.normalize(s.time);return WaveletTools.settings(s);}
function openWavelets(source=null,time=null){
 invalidateWavelets();const selector=$('waveletColumn');selector.replaceChildren();const blank=document.createElement('option');blank.value='';blank.textContent='Custom expression or pasted values';selector.append(blank);
 for(const d of datasets)for(const c of d.columns){const option=document.createElement('option');option.value=d.name+'_'+c.name;option.dataset.time=d.x&&d.x!==c.name?d.name+'_'+d.x:'';option.textContent=option.value+' · '+c.values.length+' samples';selector.append(option);}
 const s=WaveletTools.settings(waveletSettings);if(source!==null){s.source=source;s.time=time||'';}fillWaveletSettings(s);selector.value=s.source;$('waveletPaste').value='';waveletInputLabel='Pasted samples';
 let n=1;while(datasets.some(d=>d.name==='wavelet_'+n))n++;$('waveletOutputName').value='wavelet_'+n;$('waveletDialog').showModal();
}
function waveletUnits(){const u=waveletReport?.settings.unit||'seconds';return {time:u==='samples'?'Sample index':u==='days'?'Time (days)':'Time (seconds)',frequency:u==='samples'?'Frequency (cycles/sample)':u==='days'?'Frequency (cycles/day)':'Frequency (Hz)'};}
async function plotWaveletPower(){
 if(!waveletReport)return;const r=waveletReport.analysis,unit=waveletUnits(),log=$('waveletLogPower').checked;
 const layout={margin:{l:65,r:70,t:15,b:45},xaxis:{title:{text:unit.time}},yaxis:{type:'log',title:{text:unit.frequency}},showlegend:false};applyPlotTheme(layout);
 await Plotly.react('waveletPowerPlot',[{type:'heatmap',x:r.cwt.time,y:r.cwt.frequency,z:WaveletTools.power(r,log),colorscale:'Viridis',connectgaps:false,colorbar:{title:{text:log?'log₁₀ |W|²':'|W|²'},thickness:12},hovertemplate:'Time: %{x:.6g}<br>Frequency: %{y:.6g}<br>Power: %{z:.5g}<extra></extra>'},...WaveletTools.edgeLines(r)],layout,{responsive:true,displayModeBar:false});
}
async function plotWaveletBand(){
 if(!waveletReport)return;const r=waveletReport.analysis,band=r.dwt.bands.find(b=>b.name===$('waveletBand').value)||r.dwt.bands[0],unit=waveletUnits();
 const layout={margin:{l:55,r:20,t:15,b:40},xaxis:{title:{text:unit.time}},yaxis:{title:{text:band.name+' amplitude'}},showlegend:false};applyPlotTheme(layout);
 await Plotly.react('waveletBandPlot',[{type:'scatter',mode:'lines',x:r.time,y:band.values,line:{color:'#8a4dc2'},name:band.name}],layout,{responsive:true,displayModeBar:false});
}
async function renderWaveletAnalysis(){
 const r=waveletReport.analysis,unit=waveletUnits(),summary=$('waveletSummary');summary.replaceChildren();
 for(const text of [`${r.n} samples · Δt ${fmt(r.dt)} · sample rate ${fmt(r.sample_rate)} · Nyquist ${fmt(r.nyquist)}`,`${r.missing_count} missing values interpolated · ${r.resampled?'resampled to a uniform grid':'uniform time grid'} · trend removal: ${r.detrend}`,`DWT ${r.dwt.wavelet}, ${r.dwt.level} levels · reconstruction RMSE ${r.dwt.reconstruction_rmse.toExponential(3)} · threshold ${fmt(r.dwt.threshold)} · removed residual RMS ${fmt(r.dwt.residual_rms)}`,`CWT ${r.cwt.wavelet} · ${r.cwt.scales.length} scales · ${r.cwt.display_bins} display time bins (power averaged when compressed). Peak average raw power at ${r.cwt.dominant_frequency===null?'no nonzero frequency':fmt(r.cwt.dominant_frequency)}.`]){const p=document.createElement('p');p.textContent=text;summary.append(p);}
 const layout={margin:{l:55,r:20,t:15,b:45},xaxis:{title:{text:unit.time}},yaxis:{title:{text:'Signal amplitude'}},legend:{orientation:'h',y:-.2}};applyPlotTheme(layout);
 const traces=[{name:'Measured samples',x:r.raw_time,y:r.raw,line:{color:plotTheme().text,width:1},opacity:.6},{name:'Reconstruction',x:r.time,y:r.dwt.reconstruction,line:{color:'#169582',width:1,dash:'dot'}},{name:'Denoised (trend restored)',x:r.time,y:r.dwt.denoised,line:{color:'#2864d7',width:2}}].map(t=>({...t,type:'scatter',mode:'lines',connectgaps:false}));
 const spectrumLayout={margin:{l:60,r:20,t:15,b:45},xaxis:{type:'log',title:{text:unit.frequency}},yaxis:{title:{text:'Mean |W|²'}},legend:{orientation:'h',y:-.2}};applyPlotTheme(spectrumLayout);
 const select=$('waveletBand');select.replaceChildren();const output=$('waveletOutput');output.replaceChildren();
 for(const [key,label] of [['denoised','Denoised signal'],['prepared','Prepared signal'],['observed','Uniform signal'],['reconstruction','Reconstruction'],['residual','Removed residual'],...r.dwt.bands.map(b=>[b.name,b.name+' band'])]){if(key==='observed')continue;const option=document.createElement('option');option.value=key;option.textContent=label;output.append(option);}
 const table=document.createElement('table');const heading=document.createElement('tr');for(const label of ['Band','Approx. frequency range','Coefficient share']){const th=document.createElement('th');th.textContent=label;heading.append(th);}table.append(heading);
 for(const b of r.dwt.bands){const option=document.createElement('option');option.value=b.name;option.textContent=b.name;select.append(option);const row=document.createElement('tr');for(const label of [b.name,b.frequency_band.map(fmt).join(' – '),(100*b.coefficient_share).toFixed(2)+'%']){const cell=document.createElement('td');cell.textContent=label;row.append(cell);}table.append(row);}$('waveletBandTable').replaceChildren(table);
 $('waveletResults').hidden=false;
 await Promise.all([Plotly.react('waveletSignalPlot',traces,layout,{responsive:true,displayModeBar:false}),plotWaveletPower(),plotWaveletBand(),Plotly.react('waveletSpectrumPlot',[{type:'scatter',mode:'lines',x:r.cwt.frequency,y:r.cwt.global_power,name:'All times',line:{color:'#2864d7'}},{type:'scatter',mode:'lines',connectgaps:false,x:r.cwt.frequency,y:r.cwt.interior_power,name:'Interior only',line:{color:'#169582'}}],spectrumLayout,{responsive:true,displayModeBar:false})]);
}
$('waveletBtn').onclick=()=>openWavelets();
$('waveletImport').onclick=()=>{$('waveletDialog').close();$('dataImportBtn').click();};
$('waveletColumn').onchange=e=>{const option=e.target.selectedOptions[0];$('waveletSource').value=option.value;$('waveletTime').value=option.dataset.time||'';$('waveletPaste').value='';invalidateWavelets();};
$('waveletDemo').onclick=()=>{const demo=WaveletTools.demo();fillWaveletSettings({...WaveletTools.defaults,dt:1/128,source:'',time:''});$('waveletColumn').value='';$('waveletPaste').value=demo.values.join(', ');waveletInputLabel='Synthetic demo: 6 Hz to 20 Hz, a 2 Hz component, and seeded noise';$('waveletPastePanel').open=true;invalidateWavelets();toast('Synthetic demo: 6 Hz changes to 20 Hz, with a 2 Hz component and seeded noise.');};
$('waveletPaste').addEventListener('input',()=>{waveletInputLabel='Pasted samples';});
for(const id of [...Object.values(waveletFields),'waveletPaste'])$(id).addEventListener('input',invalidateWavelets);
$('waveletDialog').addEventListener('close',()=>{waveletRevision++;});$('waveletLogPower').onchange=plotWaveletPower;$('waveletBand').onchange=plotWaveletBand;
$('waveletAnalyze').onclick=async()=>{
 const revision=waveletRevision,context=requestId,button=$('waveletAnalyze');button.disabled=true;
 try{
  const settings=readWaveletSettings(),paste=$('waveletPaste').value.trim(),signal=paste?WaveletTools.parseValues(paste):settings.source;if(!signal.length)throw Error('Choose a signal column, enter an expression, or paste samples.');
  const res=await fetch('/api/wavelets',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({signal,time:settings.time||null,options:settings,expressions:rows.map(r=>({text:r.text})),datasets})});const data=await res.json();
  if(revision!==waveletRevision)return;if(context!==requestId)throw Error('The worksheet changed during analysis. Analyze again to use the current signal.');if(!res.ok)throw Error(data.error||'Could not analyze this signal.');
  waveletSettings=settings;saveLocal();waveletReport={analysis:data.analysis,settings,source:paste?waveletInputLabel:settings.source};waveletContextId=context;await renderWaveletAnalysis();
 }catch(error){if(revision===waveletRevision)$('waveletError').textContent=error.message;}finally{button.disabled=false;}
};
function currentWaveletReport(){if(!waveletReport)throw Error('Analyze a signal first.');if(waveletContextId!==requestId)throw Error('The worksheet changed. Analyze again before exporting or adding results.');return waveletReport;}
function waveletDownload(content,type,filename){const a=document.createElement('a');a.href=URL.createObjectURL(new Blob([content],{type}));a.download=filename;a.click();setTimeout(()=>URL.revokeObjectURL(a.href),1000);}
$('waveletCsv').onclick=()=>{try{waveletDownload(WaveletTools.csv(currentWaveletReport().analysis),'text/csv','NMGrapher-wavelet-signals.csv');}catch(e){$('waveletError').textContent=e.message;}};
$('waveletJson').onclick=()=>{try{waveletDownload(JSON.stringify(currentWaveletReport(),null,2),'application/json','NMGrapher-wavelet-analysis.json');}catch(e){$('waveletError').textContent=e.message;}};
$('waveletPng').onclick=()=>{try{currentWaveletReport();Plotly.downloadImage('waveletPowerPlot',{format:'png',filename:'NMGrapher-wavelet-power',scale:2});}catch(e){$('waveletError').textContent=e.message;}};
$('waveletSaveDataset').onclick=async()=>{
 const revision=waveletRevision,button=$('waveletSaveDataset');button.disabled=true;
 try{
  const report=currentWaveletReport(),context=requestId,name=DatasetTools.name($('waveletOutputName').value.trim()),item=WaveletTools.dataset(report.analysis,$('waveletOutput').value,name,uid()),proposed=DatasetTools.validate([...datasets,item]);
  const res=await fetch('/api/evaluate',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({datasets:proposed,expressions:rows.map(r=>({text:r.text})),bounds})});const data=await res.json();
  if(revision!==waveletRevision)return;if(context!==requestId)throw Error('The worksheet changed. Analyze again before adding results.');if(!res.ok)throw Error(data.error||'Could not add output dataset.');
  const bindings=item.columns.map(c=>name+'_'+c.name);if(data.results.some(r=>bindings.some(binding=>r.error===`Name ${binding} is reserved or already defined.`)))throw Error('Output name conflicts with a worksheet definition. Choose another dataset name.');
  datasets=proposed;renderDatasets();view='graph';try{bounds=DatasetTools.fit([item]);}catch{}$('waveletDialog').close();schedule(0);toast('Wavelet output added as a dataset. Save worksheet to keep it.');
 }catch(error){if(revision===waveletRevision)$('waveletError').textContent=error.message;}finally{button.disabled=false;}
};

let residentTarget=null;
const residentEditor='.expression textarea, #functionBody, #calculusExpression, #matrixGrid input, #graphFields textarea, #waveletSource, #probabilitySource';
document.addEventListener('focusin',e=>{if(e.target.matches(residentEditor))residentTarget=e.target;});
function openResident(){
 for(const [dialog,field] of [['functionDialog','functionBody'],['calculusDialog','calculusExpression'],['waveletDialog','waveletSource']])if($(dialog).open&&(!residentTarget?.isConnected||!$(dialog).contains(residentTarget)))residentTarget=$(field);
 if(!residentTarget?.isConnected){if(!rows.length)addExpression();residentTarget=$('expressions').querySelector('textarea');}
 $('residentSearch').value='';renderResident();$('residentDialog').showModal();$('residentSearch').focus();
}
function insertResident(entry){
 const target=residentTarget;if(!target?.isConnected){toast('Select an equation or formula field first.');return;}
 const start=target.selectionStart??target.value.length,end=target.selectionEnd??start,draft=FunctionCatalog.insertion(entry.template,target.value.slice(start,end));
 if(target.maxLength>0&&target.value.length-(end-start)+draft.text.length>target.maxLength){toast('This formula would exceed the field length limit.');return;}
 target.setRangeText(draft.text,start,end,'end');target.setSelectionRange(start+draft.start,start+draft.end);GreekInput.apply(target,true);target.dispatchEvent(new Event('input',{bubbles:true}));const selection=[target.selectionStart,target.selectionEnd];$('residentDialog').close();target.focus();target.setSelectionRange(...selection);
}
function renderResident(){
 const entries=FunctionCatalog.search($('residentSearch').value),container=$('residentFunctions');container.replaceChildren();$('residentEmpty').hidden=!!entries.length;
 for(const category of [...new Set(entries.map(e=>e.category))]){const section=document.createElement('section'),heading=document.createElement('h3'),grid=document.createElement('div');heading.textContent=category;grid.className='resident-grid';
  for(const entry of entries.filter(e=>e.category===category)){const b=document.createElement('button');b.type='button';b.textContent=entry.label;b.title=entry.description;b.setAttribute('aria-label',entry.label+'. '+entry.description);b.onclick=()=>insertResident(entry);grid.append(b);}section.append(heading,grid);container.append(section);}
}
for(const button of document.querySelectorAll('[data-resident-open]'))button.onclick=openResident;$('residentSearch').oninput=renderResident;

let graphRenameId=null;
function openGraphRename(id){const graph=graphs.find(g=>g.id===id);if(!graph)return;graphRenameId=id;$('graphRenameName').value=graph.name;$('graphRenameError').textContent='';$('graphRenameDialog').showModal();$('graphRenameName').focus();$('graphRenameName').select();}
$('graphRenameForm').onsubmit=e=>{e.preventDefault();try{const graph=graphs.find(g=>g.id===graphRenameId);if(!graph)throw Error('This graph was removed.');const name=$('graphRenameName').value.trim();if(!name||name.length>80)throw Error('Use a graph name of 1–80 characters.');graph.name=name;saveLocal();renderGraphs();drawPlot();$('graphRenameDialog').close();}catch(error){$('graphRenameError').textContent=error.message;}};
