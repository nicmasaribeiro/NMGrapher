"""Shared, bounded job state for Celery workers and multiple Flask processes.

All lifecycle mutations use one Redis Lua script: result delivery is idempotent,
late results cannot revive cancelled jobs, and admission/output bounds are atomic.
"""
import json
import os
import re
import time
import uuid
import redis
from async_compute import BackendUnavailable, JobCapacityError, JobNotFound, plan_tasks

_SCRIPT = r'''
local prefix, action, id = ARGV[1], ARGV[2], ARGV[3]
local args = cjson.decode(ARGV[4])
local now = tonumber(redis.call('TIME')[1])
local expiry, running, sizes = prefix..':expiry', prefix..':running', prefix..':sizes'
local function keys(j) return prefix..':job:'..j end
local function remove(j)
 local k=keys(j)
 redis.call('DEL',k,k..':payload',k..':events',k..':done')
 redis.call('ZREM',expiry,j); redis.call('ZREM',running,j); redis.call('ZREM',sizes,j)
end
local function finish(j,state,err)
 local k=keys(j)
 if redis.call('HGET',k,'state')~='running' then return end
 redis.call('HSET',k,'state',state,'error',err or '')
 redis.call('ZREM',running,j)
 local untiltime=now+tonumber(redis.call('HGET',k,'ttl'))
 redis.call('ZADD',expiry,untiltime,j)
 for _,suffix in ipairs({'',':payload',':events',':done'}) do redis.call('EXPIREAT',k..suffix,untiltime) end
end
for _,j in ipairs(redis.call('ZRANGEBYSCORE',expiry,'-inf',now)) do remove(j) end
for _,j in ipairs(redis.call('ZRANGEBYSCORE',running,'-inf',now)) do finish(j,'error','Computation deadline reached. Reduce plot detail or retry with more workers.') end
local k=keys(id)
local function bytes()
 local total=0
 local all=redis.call('ZRANGE',sizes,0,-1,'WITHSCORES')
 for i=2,#all,2 do total=total+tonumber(all[i]) end
 return total
end
if action=='create' then
 if redis.call('ZCARD',running)>=args.max_active then return {'capacity'} end
 if redis.call('ZCARD',expiry)>=args.max_jobs then
  for _,j in ipairs(redis.call('ZRANGE',expiry,0,-1)) do
   if not redis.call('ZSCORE',running,j) then remove(j);break end
  end
 end
 if redis.call('ZCARD',expiry)>=args.max_jobs or bytes()+args.size>args.max_retained then return {'capacity'} end
 local deadline=now+args.timeout
 redis.call('HSET',k,'state','running','total',args.total,'completed',#args.ready,'deadline',deadline,'ttl',args.ttl,'output',args.output,'max_output',args.max_output,'max_retained',args.max_retained,'error','')
 redis.call('SET',k..':payload',args.payload)
 for _,event in ipairs(args.ready) do redis.call('RPUSH',k..':events',event) end
 redis.call('ZADD',running,deadline,id);redis.call('ZADD',expiry,deadline+args.ttl,id);redis.call('ZADD',sizes,args.size,id)
 for _,suffix in ipairs({'',':payload',':events',':done'}) do redis.call('EXPIREAT',k..suffix,deadline+args.ttl) end
 if args.total==#args.ready then finish(id,'complete') end
 return {'ok'}
end
if redis.call('EXISTS',k)==0 then return {'missing'} end
if action=='append' then
 if redis.call('HGET',k,'state')~='running' or redis.call('SISMEMBER',k..':done',args.key)==1 then return {'ignored'} end
 if tonumber(redis.call('HGET',k,'output'))+args.size>tonumber(redis.call('HGET',k,'max_output')) or bytes()+args.size>tonumber(redis.call('HGET',k,'max_retained')) then
  finish(id,'error','Background results exceeded the memory limit. Reduce plot detail.');return {'limited'}
 end
 redis.call('SADD',k..':done',args.key);redis.call('RPUSH',k..':events',args.event)
 redis.call('HINCRBY',k,'output',args.size);local completed=redis.call('HINCRBY',k,'completed',1)
 redis.call('ZINCRBY',sizes,args.size,id)
 local untiltime=redis.call('ZSCORE',expiry,id)
 redis.call('EXPIREAT',k..':done',untiltime);redis.call('EXPIREAT',k..':events',untiltime)
 if completed==tonumber(redis.call('HGET',k,'total')) then finish(id,'complete') end
 return {'ok'}
elseif action=='finish' then
 finish(id,args.state,args.error);return {'ok'}
elseif action=='poll' then
 local cursor=redis.call('LLEN',k..':events')
 if args.after>cursor then return {'cursor'} end
 return {'ok',redis.call('HGETALL',k),tostring(cursor),redis.call('LRANGE',k..':events',args.after,-1)}
end
return {'invalid'}
'''


def encode(value):
    return json.dumps(value, separators=(',', ':'), allow_nan=False)


class RedisJobManager:
    mode = 'celery'
    workers = None

    def __init__(self, *, client=None, publisher=None, prefix=None, max_active=16,
                 max_jobs=32, ttl=300, timeout=180, max_output_bytes=64*1024*1024,
                 max_retained_bytes=128*1024*1024):
        self.client = client or redis.Redis.from_url(
            os.environ.get('NMGRAPHER_REDIS_URL', 'redis://127.0.0.1:6379/1'),
            decode_responses=True, socket_connect_timeout=2, socket_timeout=3)
        self.prefix = prefix or os.environ.get('NMGRAPHER_REDIS_PREFIX', 'nmgrapher')
        if not re.fullmatch(r'[A-Za-z0-9_-]{1,60}', self.prefix):
            raise ValueError('Redis prefix must contain 1–60 letters, digits, underscores or hyphens.')
        self.publisher = publisher
        self.options = dict(max_active=max_active, max_jobs=max_jobs, ttl=ttl, timeout=timeout,
                            max_output=max_output_bytes, max_retained=max_retained_bytes)
        self.script = self.client.register_script(_SCRIPT)

    def _call(self, action, ident, **args):
        if not re.fullmatch(r'[a-f0-9]{32}', ident):raise JobNotFound(ident)
        try:
            result = self.script(args=[self.prefix, action, ident, encode(args)])
        except redis.RedisError as exc:
            raise BackendUnavailable('The shared computation service is unavailable. Check Redis and retry.') from exc
        if result[0]=='missing':raise JobNotFound(ident)
        if result[0]=='capacity':raise JobCapacityError('The computation queue is full. Wait for a job to finish or cancel it.')
        if result[0]=='cursor':raise ValueError('Invalid result cursor.')
        return result

    def submit(self, payload, calculator=None):
        from engine import Calculator
        snapshot=encode(payload)
        payload=json.loads(snapshot)
        ready,ranked=plan_tasks(payload,calculator or Calculator(payload['expressions'],payload['datasets']))
        encoded=[encode(event) for event in ready]
        output=sum(len(event.encode()) for event in encoded)
        if output>self.options['max_output']:raise JobCapacityError('Initial results exceed the memory limit.')
        ident=uuid.uuid4().hex
        self._call('create',ident,**self.options,payload=snapshot,ready=encoded,
                   total=len(ready)+len(ranked),output=output,size=len(snapshot.encode())+output)
        try:
            if ranked:
                from celery_app import compute
                publish=self.publisher or (lambda job,kind,index: compute.apply_async(
                    args=(job,kind,index),expires=self.options['timeout'],retry=False))
                for _,kind,index in ranked:publish(ident,kind,index)
        except Exception as exc:
            self.finish(ident,'error','Could not queue calculations. Check the Celery broker and workers.')
            raise BackendUnavailable('Could not queue calculations. Check the Celery broker and workers.') from exc
        return self.poll(ident)

    def poll(self, ident, after=0):
        if isinstance(after,bool) or not isinstance(after,int) or after<0:raise ValueError('Invalid result cursor.')
        _,flat,cursor,events=self._call('poll',ident,after=after)
        meta=dict(zip(flat[::2],flat[1::2]))
        result=dict(job_id=ident,state=meta['state'],completed=int(meta['completed']),
                    total=int(meta['total']),workers=None,mode='celery',cursor=int(cursor),
                    results=[json.loads(event) for event in events])
        if meta['error']:result['error']=meta['error']
        return result

    def cancel(self, ident):
        self.finish(ident,'cancelled')
        return self.poll(ident)

    def finish(self, ident, state, error=''):
        if state not in ('cancelled','error'):raise ValueError('Invalid terminal state.')
        self._call('finish',ident,state=state,error=error)

    def append(self, ident, event):
        serialized=encode(event)
        return self._call('append',ident,key=f"{event['kind']}:{event['index']}",
                          event=serialized,size=len(serialized.encode()))[0]

    def read_work(self, ident):
        # Poll first enforces the server-side deadline.
        if self.poll(ident)['state']!='running':return None
        try:
            key=f'{self.prefix}:job:{ident}'
            deadline,payload,server_time=self.client.pipeline().hget(key,'deadline').get(key+':payload').time().execute()
        except redis.RedisError as exc:raise BackendUnavailable('Shared computation state is unavailable.') from exc
        # Convert the Redis clock to a local monotonic budget, avoiding host clock skew.
        remaining=max(0,float(deadline)-server_time[0]-server_time[1]/1e6) if deadline else 0
        return (json.loads(payload),time.monotonic()+remaining) if payload and deadline else None

    def status(self):
        try:
            self.client.ping()
            from celery_app import celery_app
            inspector=celery_app.control.inspect(timeout=0.7)
            stats=inspector.stats() or {}
            queues=inspector.active_queues() or {}
            nodes={name:node for name,node in stats.items() if any(q.get('name')=='nmgrapher' for q in queues.get(name,[]))}
        except Exception as exc:raise BackendUnavailable('Celery status is unavailable. Check Redis and the broker.') from exc
        return dict(mode='celery',available=bool(nodes),nodes=len(nodes),
                    workers=sum(int(n.get('pool',{}).get('max-concurrency',0)) for n in nodes.values()),
                    notice='' if nodes else 'No Celery workers responded. Start workers on the nmgrapher queue.')

    def close(self):pass


class RedisCancellationToken:
    def __init__(self, manager, ident, deadline):
        self.manager,self.ident,self.deadline=manager,ident,deadline
        self.next_check=0

    def __call__(self):
        now=time.monotonic()
        if now>=self.deadline:return True
        if now<self.next_check:return False
        self.next_check=now+0.1
        try:
            state=self.manager.client.hget(f'{self.manager.prefix}:job:{self.ident}','state')
        except redis.RedisError as exc:raise BackendUnavailable('Shared computation state is unavailable.') from exc
        return state!='running'
