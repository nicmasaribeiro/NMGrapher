'use strict';
const assert=require('node:assert/strict');
const greek=require('../static/greek-input.js');
for(const [word,symbol] of Object.entries(greek.keywords)){
 for(const name of [word,word.toUpperCase(),word[0].toUpperCase()+word.slice(1)]){
  assert.equal(greek.normalize(name),symbol);
  assert.equal(greek.normalize(name+'_1'),symbol+'_1');
  assert.equal(greek.normalize(name+'₁'),symbol+'₁');
 }
}
assert.equal(greek.normalize('alphabet + betamax + alpha2 + my_alpha + constructor + __proto__'),'alphabet + betamax + alpha2 + my_alpha + constructor + __proto__');
assert.equal(greek.normalize('Phi(t)=alpha*cos(theta)+beta*i'),'φ(t)=α*cos(θ)+β*i');
assert.equal(greek.normalize('Φ+Π+Γ'),'Φ+Π+Γ');
assert.equal(greek.normalize('alpha',5),'alpha');
assert.equal(greek.normalize('alpha +',7),'α +');
assert.equal(greek.normalize('alpha_{1}+beta²'),'α_{1}+β²');
function field(value,start=value.length,end=start){return {value,selectionStart:start,selectionEnd:end,selectionDirection:'none',setSelectionRange(a,b){this.selectionStart=a;this.selectionEnd=b;}};}
let input=field('alpha+beta',10);greek.apply(input);assert.equal(input.value,'α+beta');assert.equal(input.selectionStart,6);
greek.apply(input,true);assert.equal(input.value,'α+β');assert.equal(input.selectionStart,3);
input=field('alpha + beta',8,12);greek.apply(input,true);assert.equal(input.value,'α + β');assert.equal(input.selectionStart,4);assert.equal(input.selectionEnd,5);
input=field('alphaX',5);greek.apply(input);assert.equal(input.value,'alphaX');
console.log('Greek conversion: all 24 keywords, case, boundaries, subscripts, deferred typing, and caret/selection checks passed.');
