'use strict';
(() => {
 class ComputeClient {
  constructor({fetch:fetcher,delay=120}={}){this.fetch=fetcher||((...args)=>fetch(...args));this.delay=delay;this.current=null;}
  async json(url,options){const response=await this.fetch(url,options);const data=await response.json();if(!response.ok)throw Error(data.error||'Computation request failed.');return data;}
  stopRemote(job){if(!job.id||job.stopSent)return;job.stopSent=true;this.fetch(`/api/jobs/${encodeURIComponent(job.id)}/cancel`,{method:'POST',keepalive:true}).catch(()=>{});}
  cancel(){const job=this.current;if(!job)return;job.cancelled=true;job.controller.abort();this.stopRemote(job);this.current=null;}
  wait(signal){return new Promise((resolve,reject)=>{if(signal.aborted){reject(new DOMException('Cancelled','AbortError'));return;}const abort=()=>{clearTimeout(timer);reject(new DOMException('Cancelled','AbortError'));};const timer=setTimeout(()=>{signal.removeEventListener('abort',abort);resolve();},this.delay);signal.addEventListener('abort',abort,{once:true});});}
  async run(payload,callbacks={}){
   this.cancel();const job={id:null,cancelled:false,stopSent:false,controller:new AbortController()};this.current=job;
   const active=()=>this.current===job&&!job.cancelled;
   try{
    // Keep the creation response so cancellation can identify a job created mid-edit.
    const started=await this.json('/api/jobs',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(payload)});
    if(!started.job_id)throw Error('The server did not return a computation ID.');job.id=started.job_id;
    if(!active()){this.stopRemote(job);return;}
    callbacks.onStart?.(started);
    let cursor=0,failures=0;
    while(active()){
     let update;
     try{update=await this.json(`/api/jobs/${encodeURIComponent(job.id)}?after=${cursor}`,{signal:job.controller.signal});failures=0;}
     catch(error){if(!active()||error.name==='AbortError')return;if(++failures>2)throw error;await this.wait(job.controller.signal);continue;}
     if(!active())return;
     if(!['running','complete','cancelled','error'].includes(update.state)||!Number.isInteger(update.cursor)||update.cursor<cursor||!Array.isArray(update.results))throw Error('Invalid computation response.');
     for(const record of update.results){if(!active())return;callbacks.onResult?.(record);}
     cursor=update.cursor;callbacks.onProgress?.(update);
     if(update.state==='complete'){callbacks.onDone?.(update);return;}
     if(update.state==='cancelled'){callbacks.onCancelled?.(update);return;}
     if(update.state==='error')throw Error(update.error||'Could not complete the worksheet.');
     await this.wait(job.controller.signal);
    }
   }catch(error){if(active()&&error.name!=='AbortError'){this.stopRemote(job);callbacks.onError?.(error);}}
   finally{if(this.current===job)this.current=null;}
  }
 }
 const api={ComputeClient};if(typeof window!=='undefined')window.AsyncCompute=api;if(typeof module!=='undefined')module.exports=api;
})();
