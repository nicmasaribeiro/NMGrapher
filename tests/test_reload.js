'use strict';
const assert=require('node:assert/strict');
const fs=require('node:fs');
const vm=require('node:vm');
const source=fs.readFileSync('static/app.js','utf8');
const functions=source.slice(source.indexOf('function saveLocal(){'),source.indexOf('function validateWorksheet('));
for(const storageFails of [false,true]){
 const calls=[],button={},worksheet={version:5,rows:[{text:'x'}],datasets:[{id:'sample'}],graphs:[{name:'My graph'}]};
 let saved;
 const context={document:{activeElement:{blur(){calls.push('blur');worksheet.rows[0].text='x^2';}}},
  localStorage:{setItem(key,value){calls.push('save');if(storageFails)throw Error('Quota exceeded');saved=JSON.parse(value);assert.equal(key,'matrix-graph-v1');}},
  worksheetData:()=>worksheet,toast:message=>calls.push(message),clearTimeout:()=>calls.push('cancel'),timer:123,requestId:7,
  window:{location:{reload(){calls.push('reload');}}},$:()=>button};
 vm.createContext(context);vm.runInContext(functions,context);
 const result=button.onclick();
 if(storageFails){assert.equal(result,false);assert.equal(context.requestId,7);assert.ok(!calls.includes('reload'));assert.ok(!calls.includes('cancel'));}
 else{assert.equal(result,true);assert.equal(context.requestId,8);assert.deepEqual(calls,['blur','save','cancel','reload']);assert.deepEqual(saved,worksheet);}
}
const startup=source.slice(source.indexOf('let restoredWorksheet=false;'),source.indexOf('new ResizeObserver('));
for(const data of [null,{rows:[]}]){
 const context={localStorage:{getItem:()=>JSON.stringify(data)},rows:[],bounds:[-1,1,-1,1],view:'graph',
  validateWorksheet:d=>d.rows,DatasetTools:{validate:()=>{}},GraphTools:{validate:()=>{}},WaveletTools:{settings:()=>{}},SurfaceTools:{settings:()=>{}},
  validBounds:()=>false,restoreViewOptions:()=>{},examples:{basics:['x']},newRow:text=>({text}),renderRows:()=>{},schedule:()=>{}};
 vm.createContext(context);vm.runInContext(startup,context);
 assert.equal(context.rows.length,data?0:1);
}
console.log('Reload: latest edits saved before refresh; storage failure stops reload; empty worksheets retained.');
