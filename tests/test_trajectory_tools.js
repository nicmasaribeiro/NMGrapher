'use strict';
const assert=require('node:assert/strict'),T=require('../static/trajectory-tools.js');
const report={kind:'sequence',time:[0,1,2,3],frames:4,dimensions:3,paths:1,values:[[[1,0,0],[0,1,1],[-1,0,2],[0,-1,3]]]};
const options={display:'3d',coordinates:'0,1,2',name:'Helix'};
const plan=T.config(report,options),data=T.frame(report,plan,2,2);
assert.deepEqual(data[0].x,[0,-1]);assert.deepEqual(data[1].z,[2]);assert.equal(data[0].type,'scatter3d');
assert.deepEqual(T.frame(report,plan,0)[0].x,[1]);assert.deepEqual(T.frame(report,plan,99)[0].x,[1,0,-1,0]);
const time=T.config(report,{display:'time',coordinates:'2'});assert.deepEqual(T.frame(report,time,3)[0].y,[0,1,2,3]);
assert.throws(()=>T.config(report,{display:'2d',coordinates:'0,0'}));assert.throws(()=>T.config(report,{display:'3d',coordinates:'0,1,4'}));
const dataset=T.dataset(report,'path_data','d1');assert.equal(dataset.columns.length,4);assert.deepEqual(dataset.columns[3].values,[0,1,2,3]);assert.equal(dataset.x,'time');
assert(T.csv(report).startsWith('time,path_1_state_0,path_1_state_1,path_1_state_2\n0,1,0,0\n'));
assert.deepEqual(T.settings(JSON.parse(JSON.stringify(T.defaults))),T.defaults);assert.throws(()=>T.settings({steps:NaN}));
let raf,cancelled=0,painted=[],pending=[];global.requestAnimationFrame=fn=>{raf=fn;return 1;};global.cancelAnimationFrame=()=>cancelled++;
global.Plotly={react(plot,data){painted.push(data);return new Promise(resolve=>pending.push(resolve));}};
const flush=()=>new Promise(resolve=>setImmediate(resolve));
(async()=>{
 const p=new T.Player('plot',report,{...options,speed:1});await flush();assert.equal(painted.length,1);
 p.seek(1);p.seek(2);await flush();assert.equal(painted.length,1); // one Plotly update in flight
 pending.shift()();await flush();assert.equal(painted.length,2);assert.deepEqual(painted[1][1].z,[2]);
 pending.shift()();await flush();p.seek(0);await flush();pending.shift()();await flush();
 p.play();raf(0);raf(5000);assert.equal(p.index,1);p.options.speed=2;raf(7500);assert.equal(p.index,3);assert.equal(p.playing,false);
 p.dispose();const count=painted.length;while(pending.length)pending.shift()();await flush();assert.equal(painted.length,count);assert(cancelled>0);
 console.log('Trajectory playback: coordinate projection, trails, CSV, persistence, timing, pause and serialized rendering passed.');
})().catch(e=>{console.error(e);process.exitCode=1;});
