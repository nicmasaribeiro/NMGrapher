import json
import time
from concurrent.futures import ThreadPoolExecutor
import numpy as np
import pytest
import trajectories as tr
from engine import Calculator,parse,ComputationCancelled
from app import app
from async_compute import JobManager


def test_gbm_exact_zero_volatility_and_initial_state():
    g=tr.gbm(100,.05,0,2,20,3,42)
    for p in g.values:np.testing.assert_allclose(p[:,0],100*np.exp(.05*g.time))
    r=tr.report(g);assert r['reference']['terminal_variance']==0
    np.testing.assert_allclose(r['reference']['lower'],r['reference']['upper'])
    assert np.all(g.values>0) and not g.values.flags.writeable


def test_gbm_innovations_seed_and_independent_streams():
    g=tr.gbm(100,.07,.3,2,1999,24,73);short=tr.gbm(100,.07,.3,2,1999,2,73)
    np.testing.assert_array_equal(g.values[:2],short.values)
    np.testing.assert_array_equal(g.values,tr.gbm(100,.07,.3,2,1999,24,73).values)
    dt=2/1999;z=(np.diff(np.log(g.values[:,:,0]),axis=1)-(.07-.3**2/2)*dt)/(.3*np.sqrt(dt))
    assert abs(z.mean())<.02 and abs(z.var()-1)<.025
    assert abs(np.corrcoef(z[0],z[1])[0,1])<.08
    assert not np.array_equal(g.values,tr.gbm(100,.07,.3,2,1999,24,74).values)
    r=tr.report(short)['reference'];assert r['mean'][-1]==pytest.approx(100*np.exp(.07*2))
    assert r['terminal_variance']==pytest.approx(10000*np.exp(2*.07*2)*np.expm1(.3*.3*2))
    assert r['lower'][-1]<r['median'][-1]<r['upper'][-1]


def test_sequence_uses_previous_state_and_correct_k_t_dt():
    c=Calculator([])
    g=tr.compute(c,dict(kind='sequence',initial=[1,2],start=3,horizon=1,steps=4,update='[s[0]+s[1],k+t+dt]'))
    expected=[[1,2]]
    for k in range(4):expected.append([sum(expected[-1]),k+3+k*.25+.25])
    np.testing.assert_allclose(g.values[0],expected);np.testing.assert_allclose(g.time,np.linspace(3,4,5))
    assert len(g.time)==5


def test_rotation_gradient_descent_and_markov_paths():
    c=Calculator([])
    g=tr.compute(c,dict(kind='sequence',initial=[1,0],horizon=2*np.pi,steps=200,update='[[cos(dt),-sin(dt)],[sin(dt),cos(dt)]]@s'))
    np.testing.assert_allclose(g.values[0,-1],[1,0],atol=1e-12)
    np.testing.assert_allclose(np.linalg.norm(g.values[0],axis=1),1,atol=1e-12)
    descent=tr.compute(c,dict(kind='sequence',initial=[3,2],horizon=3,steps=150,update='s-dt*[2*s[0],4*s[1]]'))
    energy=descent.values[0,:,0]**2+2*descent.values[0,:,1]**2
    assert np.all(np.diff(energy)<0)
    P=np.array([[.9,.08,.02],[.05,.9,.05],[.02,.08,.9]])
    m=tr.compute(c,dict(kind='sequence',initial=[1,0,0],horizon=50,steps=50,update='s@'+json.dumps(P.tolist())))
    np.testing.assert_allclose(m.values[0].sum(axis=1),1)
    np.testing.assert_allclose(m.values[0,-1],[1,0,0]@np.linalg.matrix_power(P,50))


def test_python_updates_and_named_worksheet_trajectories():
    rows=[{'type':'note','text':'Sequential algorithm'}, {'type':'python','text':'def update(s,k,t,dt):\n    next_state = s + dt * [-s[1], s[0]]\n    return next_state'},
          {'text':'G=iterate(update,[1,0],20,0.1)'},{'text':'trajectory_times(G)'},{'text':'trajectory_path(G,0,1)'},
          {'text':'r(t)=[cos(t),sin(t),t/4]'},{'text':'curve_path=trajectory(r,0,6,30)'},
          {'text':'M=gbm(100,.05,.2,1,50,2,42)'},{'text':'f(a)=gbm(a,.05,.2)'},
          {'text':'next(s,k,t,dt)=s + dt * [-s[1],s[0]]'}]
    c=Calculator(rows);out=c.run([0,1,0,1]);assert not any(r.get('error') for r in out),out
    assert out[2]['kind']==out[6]['kind']==out[7]['kind']=='trajectory'
    assert out[8]['kind']=='trajectory_function' and out[9]['kind']=='update_function'
    assert out[3]['kind']==out[4]['kind']=='series'
    g=c.evaluate(parse('G'));assert tr.trajectory_path(g,0,1).shape==(21,)
    np.testing.assert_allclose(out[6]['trajectory']['values'][0][-1],[np.cos(6),np.sin(6),1.5])


@pytest.mark.parametrize('settings',[
    dict(kind='gbm',initial=0),dict(kind='gbm',volatility=-1),dict(kind='gbm',steps=True),dict(kind='gbm',steps=2000),
    dict(kind='gbm',paths=25),dict(kind='gbm',seed=-1),dict(kind='gbm',horizon=101),dict(kind='gbm',initial=float('nan')),
    dict(kind='sequence',initial=[1],update='[s[0],1]',steps=2),dict(kind='sequence',initial=[1],update='[1/0]'),
    dict(kind='sequence',initial=[1],update='[s[0]*1e100]',steps=3),dict(kind='parametric',expression='sqrt(-1)'),
    dict(kind='parametric',expression='[1,2] if t<0.5 else [1]',steps=4),dict(kind='sequence',initial=[1j],update='s')])
def test_invalid_and_divergent_paths(settings):
    with pytest.raises((ValueError,ArithmeticError)):tr.compute(Calculator([]),settings)


def test_cancellation_and_state_component_bounds():
    c=Calculator([],cancel_check=lambda:True)
    with pytest.raises(ComputationCancelled):tr.compute(c,dict(kind='sequence',initial=[1],update='s',steps=1999))
    g=tr.gbm(100,.05,.2)
    for idx,comp in [(24,0),(0,1),(-1,0)]:
        with pytest.raises(ValueError):tr.trajectory_path(g,idx,comp)
    values=tr.trajectory_path(g);values[0]=-1;assert g.values[0,0,0]>0


def finished(manager,ident):
    deadline=time.monotonic()+30
    while time.monotonic()<deadline:
        out=manager.poll(ident)
        if out['state']!='running':return out
        time.sleep(.01)
    pytest.fail('Trajectory job did not finish')


def test_background_api_uses_full_context_but_only_computes_trajectory(monkeypatch):
    import async_compute
    manager=JobManager(workers=2,executor_factory=lambda n:ThreadPoolExecutor(n));monkeypatch.setattr(async_compute,'manager',manager)
    try:
        client=app.test_client();payload={'expressions':[{'text':'a=2'},{'text':'G(s,k,t,dt)=s + dt*[a,1]'}, {'type':'note','text':'snapshot'}], 'trajectory':{'kind':'sequence','initial':[0,0],'update':'G(s,k,t,dt)','steps':10,'horizon':1}}
        r=client.post('/api/trajectories/jobs',json=payload);assert r.status_code==202,r.json
        result=finished(manager,r.json['job_id']);assert result['state']=='complete' and result['total']==1,result
        assert result['results'][0]['kind']=='trajectory'
        np.testing.assert_allclose(result['results'][0]['result']['values'][0][-1],[2,1])
        r=client.post('/api/trajectories/jobs',json={'trajectory':{'kind':'gbm','seed':True}});assert r.status_code==400
    finally:manager.close(wait=True)


def test_spawned_worker_generates_paths():
    manager=JobManager(workers=1)
    try:
        payload=dict(expressions=[],datasets=[],graphs=[],bounds=[-1,1,-1,1],trajectory_task=dict(kind='gbm',steps=20,paths=2))
        job=manager.submit(payload);out=finished(manager,job['job_id'])
        assert out['state']=='complete' and out['mode']=='process',out
        assert out['results'][0]['result']['frames']==21
    finally:manager.close(wait=True)


def test_offline_animation_export_preserves_data_and_escapes_names():
    client=app.test_client();g=tr.report(tr.gbm(100,.05,.2,1,10,2,42))
    r=client.post('/api/trajectories/export',json=dict(trajectory=g,options={'name':'</script><img src=x onerror=alert(1)>'}))
    assert r.status_code==200 and r.mimetype=='text/html'
    assert '<img src=x onerror=alert(1)>' not in r.text
    assert 'new TrajectoryTools.Player' in r.text and 'cdn.plot.ly' not in r.text[:1000]
    assert 'src="/static/' not in r.text
    assert '100.0' in r.text or '99.999' in r.text
    bad={**g,'time':[0,1]};assert client.post('/api/trajectories/export',json=dict(trajectory=bad)).status_code==400
    assert client.post('/api/trajectories/export',json=dict(trajectory=g,options={'speed':0})).status_code==400
