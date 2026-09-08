"""Optional integration tests: install requirements-celery.txt and provide redis-server.

NMGRAPHER_TEST_REDIS_SERVER may name a binary; redislite is also supported in CI.
All tests use an isolated ephemeral Redis instance, never an existing database.
"""
import os
import shutil
import socket
import subprocess
import sys
import time
import uuid
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor

import pytest
redis=pytest.importorskip('redis')
pytest.importorskip('celery')
from async_compute import BackendUnavailable, JobCapacityError, JobNotFound
from celery_compute import RedisJobManager
from app import app, evaluation_payload


def wait_for(check,timeout=20):
    end=time.monotonic()+timeout
    while time.monotonic()<end:
        try:
            value=check()
            if value:return value
        except redis.ConnectionError:pass
        time.sleep(.05)
    raise AssertionError('Background service did not become ready.')


@pytest.fixture(scope='module')
def redis_server(tmp_path_factory):
    binary=os.environ.get('NMGRAPHER_TEST_REDIS_SERVER') or shutil.which('redis-server')
    if not binary:
        try:
            import redislite
            binary=str(Path(redislite.__file__).parent/'bin'/'redis-server')
        except ImportError:pytest.skip('redis-server required for Celery integration tests')
    with socket.socket() as sock:
        sock.bind(('127.0.0.1',0));port=sock.getsockname()[1]
    folder=tmp_path_factory.mktemp('redis')
    with (folder/'redis.log').open('w') as log:
        process=subprocess.Popen([binary,'--bind','127.0.0.1','--port',str(port),'--save','','--appendonly','no','--dir',str(folder)],stdout=log,stderr=log)
        url=f'redis://127.0.0.1:{port}'
        client=redis.Redis.from_url(url+'/1',decode_responses=True)
        try:
            wait_for(client.ping)
            yield url,client
        finally:
            process.terminate();process.wait(timeout=10)


def payload(*expressions):
    p=evaluation_payload({'expressions':[{'text':s} for s in expressions]})
    p['graphs']=[]
    return p


@pytest.fixture
def manager(redis_server):
    return RedisJobManager(client=redis_server[1],prefix='test_'+uuid.uuid4().hex,publisher=lambda *args:None)


def event(index=0):return dict(kind='row',index=index,result={'value':3})


def test_shared_state_deduplication_and_completion(manager,redis_server):
    job=manager.submit(payload('x','x^2'))
    other=RedisJobManager(client=redis_server[1],prefix=manager.prefix)
    with ThreadPoolExecutor(8) as pool:
        list(pool.map(lambda _:other.append(job['job_id'],event()),range(16)))
    snapshot=manager.poll(job['job_id'])
    assert snapshot['completed']==snapshot['cursor']==1
    assert snapshot['state']=='running'
    other.append(job['job_id'],event(1))
    final=manager.poll(job['job_id'],after=1)
    assert final['state']=='complete' and len(final['results'])==1
    assert final['mode']=='celery'
    manager.close()
    assert other.poll(job['job_id'])['state']=='complete'


def test_cancellation_ignores_late_results(manager):
    ident=manager.submit(payload('sin(x)'))['job_id']
    assert manager.cancel(ident)['state']=='cancelled'
    assert manager.append(ident,event())=='ignored'
    assert manager.read_work(ident) is None
    assert manager.poll(ident)['completed']==0


def test_deadline_and_cursor(manager,redis_server):
    ident=manager.submit(payload('x'))['job_id']
    with pytest.raises(ValueError):manager.poll(ident,1)
    for after in [-1,True,'0']:
        with pytest.raises(ValueError):manager.poll(ident,after)
    redis_server[1].zadd(manager.prefix+':running',{ident:0})
    assert manager.poll(ident)['state']=='error'
    assert manager.append(ident,event())=='ignored'
    with pytest.raises(JobNotFound):manager.poll('../bad')


def test_capacity_and_output_limits(manager):
    manager.options['max_active']=1
    first=manager.submit(payload('x'))['job_id']
    with pytest.raises(JobCapacityError):manager.submit(payload('y'))
    manager.cancel(first)
    manager.options['max_output']=5
    second=manager.submit(payload('x'))['job_id']
    assert manager.append(second,event())=='limited'
    assert manager.poll(second)['state']=='error'


def test_retention_and_initial_ready_results(manager,redis_server):
    manager.options['max_jobs']=1
    first=manager.submit(payload(''))
    assert first['state']=='complete' and first['completed']==1
    second=manager.submit(payload('x'))
    with pytest.raises(JobNotFound):manager.poll(first['job_id'])
    manager.cancel(second['job_id'])
    redis_server[1].zadd(manager.prefix+':expiry',{second['job_id']:0})
    with pytest.raises(JobNotFound):manager.poll(second['job_id'])
    assert not redis_server[1].exists(manager.prefix+':sizes')


def test_broker_failure_finalizes_admitted_job(manager):
    def fail(*args):raise ConnectionError('not connected')
    manager.publisher=fail
    with pytest.raises(BackendUnavailable):manager.submit(payload('x'))
    ident=manager.client.zrange(manager.prefix+':expiry',0,-1)[0]
    assert manager.poll(ident)['state']=='error'


def test_unavailable_backend_http_error(monkeypatch):
    import async_compute
    class Unavailable:
        def submit(self,*args):raise BackendUnavailable('Redis unavailable')
    monkeypatch.setattr(async_compute,'manager',Unavailable())
    response=app.test_client().post('/api/jobs',json={'expressions':[{'text':'x'}]})
    assert response.status_code==503
    assert response.json['error']=='Redis unavailable'


def test_two_real_celery_nodes_and_cross_process_jobs(redis_server,monkeypatch,tmp_path):
    from celery_app import celery_app
    import async_compute
    url,client=redis_server
    prefix='live_'+uuid.uuid4().hex
    monkeypatch.setenv('NMGRAPHER_REDIS_URL',url+'/1')
    monkeypatch.setenv('NMGRAPHER_REDIS_PREFIX',prefix)
    monkeypatch.setenv('NMGRAPHER_CELERY_BROKER_URL',url+'/0')
    monkeypatch.setenv('NMGRAPHER_COMPUTE_BACKEND','celery')
    old_broker=celery_app.conf.broker_url
    celery_app.conf.broker_url=url+'/0'
    processes=[];logs=[]
    try:
        for n in range(2):
            log=(tmp_path/f'worker{n}.log').open('w');logs.append(log)
            processes.append(subprocess.Popen([sys.executable,'-m','celery','-A','celery_app:celery_app','worker','--loglevel=WARNING','--concurrency=3',f'--hostname=test{n}@%h','--queues=nmgrapher','--without-gossip','--without-mingle'],cwd=Path(__file__).resolve().parents[1],stdout=log,stderr=log))
        nodes=wait_for(lambda:(s if len(s:=celery_app.control.inspect(timeout=.4).stats() or {})==2 else None),30)
        assert sum(n['pool']['max-concurrency'] for n in nodes.values())==6
        distributed=RedisJobManager(client=client,prefix=prefix)
        monkeypatch.setattr(async_compute,'manager',distributed)
        http=app.test_client()
        response=http.post('/api/jobs',json={'expressions':[{'text':s} for s in ['a=2','f(x)=sin(x)+a','g(x,y)=x^2+y^2','D=normal(0,1)','I(t)=integrate(D(x),x,0,t)']]})
        assert response.status_code==202,response.json
        ident=response.json['job_id']
        # A separately constructed manager reads everything without Flask-local state.
        other=RedisJobManager(client=client,prefix=prefix)
        final=wait_for(lambda:(j if (j:=other.poll(ident))['state']!='running' else None),30)
        assert final['state']=='complete',final
        assert final['completed']==5
        assert all('error' not in e['result'] for e in final['results']),final
        kinds={e['result']['kind'] for e in final['results']}
        assert 'surface' in kinds and 'curve' in kinds
        assert http.get('/api/compute/status').json['workers']==6
        # A queued job cancelled before delivery cannot publish any later results.
        paused=RedisJobManager(client=client,prefix=prefix,publisher=lambda *args:None)
        cancelled=paused.submit(payload('sin(x)'))['job_id']
        paused.cancel(cancelled)
        from celery_app import compute
        compute.apply_async(args=(cancelled,'row',0),retry=False)
        assert other.poll(cancelled)['state']=='cancelled'
    finally:
        for process in processes:process.terminate()
        for process in processes:
            try:process.wait(timeout=15)
            except subprocess.TimeoutExpired:process.kill();process.wait()
        for log in logs:log.close()
        celery_app.conf.broker_url=old_broker
