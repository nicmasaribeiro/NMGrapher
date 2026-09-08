'use strict';
const assert=require('node:assert/strict');
class Element{
 constructor(tag){this.tag=tag;this.children=[];this.attrs={};this.isConnected=true;this.classList={add(){},remove(){}};}
 append(child){this.children.push(child);}setAttribute(k,v){this.attrs[k]=v;}removeAttribute(k){delete this.attrs[k];}replaceChildren(...children){this.children=children;}
}
global.document={createElementNS(namespace,tag){assert.equal(namespace,'http://www.w3.org/1998/Math/MathML');return new Element(tag);}};
let callback;
global.setTimeout=fn=>{callback=fn;return 1;};global.clearTimeout=()=>{};
const pending=[];
global.fetch=()=>new Promise(resolve=>pending.push(resolve));
const {build,render}=require('../static/math-preview.js');
const result=build({tag:'mfrac',children:[{tag:'mi',text:'d'},{tag:'mrow',children:[{tag:'mi',text:'d',attrs:{mathvariant:'normal',onclick:'bad'}},{tag:'mi',text:'x'}]}]});
assert.equal(result.children[1].children[0].attrs.onclick,undefined);
assert.equal(build({tag:'mi',text:'<img src=x>'}).textContent,'<img src=x>');
assert.throws(()=>build({tag:'script',text:'bad'}),/Invalid/);
(async()=>{
 const container=new Element('div');render(container,'old');const oldRequest=callback();render(container,'new');const newRequest=callback();
 pending[1]({ok:true,json:async()=>({previews:[{tree:{tag:'mi',text:'new'}}]})});await newRequest;
 pending[0]({ok:true,json:async()=>({previews:[{tree:{tag:'mi',text:'old'}}]})});await oldRequest;
 assert.equal(container.children[0].children[0].textContent,'new');
 console.log('Math preview: MathML node/attribute safety, literal text, and stale-response protection passed.');
})().catch(error=>{console.error(error);process.exitCode=1;});
