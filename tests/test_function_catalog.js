const assert=require('node:assert/strict'),catalog=require('../static/function-catalog.js');
for(const label of ['exp','ln','log','logₐ','d/dx','f′','∫','∑','∏','mean','median','min','max','quartile','quantile','stdev','stdevp','var','varp','cov','covp','mad','corr','spearman','stats','count','total','sinh','cosh','tanh','csch','sech','coth','DWT','CWT','Inverse DWT'])assert(catalog.entries.some(e=>e.label===label),label);
const a=catalog.insertion('mean({{[1,2,3]}})','data_1_signal');assert.equal(a.text,'mean(data_1_signal)');assert.equal(a.text.slice(a.start,a.end),'data_1_signal');
const b=catalog.insertion('∑_{k=1}^{10} ({{k^2}})');assert.equal(b.text,'∑_{k=1}^{10} (k^2)');assert.equal(b.text.slice(b.start,b.end),'k^2');
assert(catalog.search('wavelet').length>=15);assert(catalog.search('nosuchfunction').length===0);
for(const label of ['|0⟩','|ψ⟩','Define ket','⟨ψ|','⟨φ|ψ⟩','|ψ⟩⟨φ|','⟨ψ|A|ψ⟩','Tensor kets','Bell ket'])assert(catalog.entries.some(e=>e.category==='Quantum / Dirac notation'&&e.label===label),label);
const ket=catalog.insertion(catalog.entries.find(e=>e.label==='|ψ⟩').template,'φ_1(t)');assert.equal(ket.text,'|φ_1(t)⟩');assert.equal(ket.text.slice(ket.start,ket.end),'φ_1(t)');
const tensor=catalog.insertion(catalog.entries.find(e=>e.label==='Tensor kets').template);assert.equal(tensor.text,'|0⟩ ⊗ |1⟩');
console.log('Resident palette: screenshot coverage, wavelet entries, insertion selections, and search passed.');
