'use strict';
const assert=require('node:assert/strict');
const {ComputeClient}=require('../static/async-compute.js');
const response=data=>({ok:true,json:async()=>data});
const deferred=()=>{let resolve;const promise=new Promise(r=>resolve=r);return {promise,resolve};};
(async()=>{
 const calls=[],events=[],first=deferred(),second=deferred();let created=0;
 const client=new ComputeClient({delay:0,fetch:async(url,options={})=>{
  calls.push([url,options]);
  if(url==='/api/jobs'){created++;return response({job_id:'job'+created,total:2});}
  if(url.endsWith('/cancel'))return response({state:'cancelled'});
  if(url.includes('job1?'))return first.promise;
  if(url.includes('job2?after=0'))return response({state:'running',cursor:1,completed:1,total:2,results:[{kind:'row',index:1,result:{value:2}}]});
  if(url.includes('job2?after=1'))return second.promise;
  throw Error('Unexpected URL '+url);
 }});
 const old=client.run({}, {onResult:r=>events.push(['old',r])});
 await new Promise(r=>setTimeout(r,0));
 const current=client.run({}, {onResult:r=>events.push(['new',r]),onDone:()=>events.push(['done'])});
 await new Promise(r=>setTimeout(r,5));
 assert.equal(events.length,1,'first completed row is delivered before whole job completes');
 assert.equal(events[0][1].index,1);
 first.resolve(response({state:'complete',cursor:1,completed:1,total:1,results:[{kind:'row',index:0,result:{value:99}}]}));
 second.resolve(response({state:'complete',cursor:2,completed:2,total:2,results:[{kind:'row',index:0,result:{value:1}}]}));
 await Promise.all([old,current]);assert.deepEqual(events.map(e=>e[0]),['new','new','done']);
 assert.ok(calls.some(([url])=>url==='/api/jobs/job1/cancel'));
 assert.ok(calls.some(([url])=>url==='/api/jobs/job2?after=1'));
 // Cancel while POST is outstanding: the returned job must still be cancelled.
 const creation=deferred();const stopped=[];
 const slow=new ComputeClient({fetch:async url=>{if(url==='/api/jobs')return creation.promise;stopped.push(url);return response({});}});
 const pending=slow.run({}, {onResult:()=>assert.fail('cancelled creation delivered result')});slow.cancel();
 creation.resolve(response({job_id:'late',total:1}));await pending;
 assert.deepEqual(stopped,['/api/jobs/late/cancel']);
 let failures=0,error;
 const broken=new ComputeClient({delay:0,fetch:async url=>{if(url==='/api/jobs')return response({job_id:'bad'});if(url.endsWith('/cancel'))return response({});failures++;throw Error('offline');}});
 await broken.run({}, {onError:e=>error=e});assert.equal(failures,3);assert.equal(error.message,'offline');
 console.log('Async computations: incremental delivery, cursor order, superseded results, cancellation during creation, and bounded polling retries passed.');
})().catch(error=>{console.error(error);process.exitCode=1;});
