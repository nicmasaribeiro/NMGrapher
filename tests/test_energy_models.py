import json
import subprocess
import time
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor

import numpy as np
import pytest
from scipy.special import logsumexp, expit

import energy_models as em
from app import app
from async_compute import JobManager
from engine import Calculator, ComputationCancelled, parse


@pytest.mark.parametrize('temperature',[.05,.7,1,3,20])
def test_rbm_matches_exhaustive_joint_enumeration(temperature):
    m=em.rbm([[.5,-.7],[1.2,.4]],[.2,-.3],[.1,.6],temperature)
    V=em.states(2);H=em.states(2)
    E=np.array([[em.energy(m,v,h) for h in H] for v in V])
    joint=np.exp(-E/temperature-logsumexp(-E/temperature))
    np.testing.assert_allclose([em.free_energy(m,v) for v in V],-temperature*logsumexp(-E/temperature,axis=1))
    np.testing.assert_allclose([em.energy_probability(m,v) for v in V],joint.sum(axis=1))
    assert em.log_partition(m)==pytest.approx(logsumexp(-E/temperature))
    for k,v in enumerate(V):
        conditional=expit((v@m.W+m.b)/temperature)
        np.testing.assert_allclose(em.hidden_probabilities(m,v),joint[k]@H/joint[k].sum())
        np.testing.assert_allclose(em.reconstruct(m,v),expit((conditional@m.W.T+m.a)/temperature))
    report=em.analyze(m,count=5)
    assert report['expected_energy']==pytest.approx(np.sum(joint*E))
    assert sum(s['probability'] for s in report['top_states'])==pytest.approx(1)


def test_bm_normalization_energy_and_symmetric_gradient():
    m=em.boltzmann_machine([[0,1.3],[1.3,0]],[-.2,.4],.8)
    V=em.states(2);E=np.array([0,-.4,.2,-1.5])
    np.testing.assert_allclose([em.energy(m,v) for v in V],E)
    p=np.exp(-E/.8-logsumexp(-E/.8))
    np.testing.assert_allclose([em.energy_probability(m,v) for v in V],p)
    data=np.array([[1,1],[0,0],[1,1]],float)
    def nll(weight):
        mm=em.boltzmann_machine([[0,weight],[weight,0]],m.a,.8)
        return np.mean(em.scores(mm,data))/.8+em.log_partition(mm)
    eps=1e-5;gradient=(nll(1.3+eps)-nll(1.3-eps))/(2*eps)
    result=em.train(m,data,dict(epochs=1,rate=.01,decay=0,validation=0))
    assert result['model']['weights'][0][1]==pytest.approx(1.3-.01*gradient)
    fitted=em.unpack(result['model']);assert np.array_equal(fitted.W,fitted.W.T)
    assert not np.any(np.diag(fitted.W))
    np.testing.assert_array_equal(m.W,[[0,1.3],[1.3,0]])


def test_exact_training_improves_correlated_patterns():
    result=em.train(em.initialize('bm',2),[[0,0],[1,1]]*10,dict(epochs=300,rate=.2,validation=0))
    assert result['history'][-1]['train_nll']<result['history'][0]['train_nll']-.4
    assert {s['label'] for s in result['top_states'][:2]}=={'00','11'}


def test_cd_seed_reproducibility_and_learning():
    m=em.initialize('rbm',4,2);data=[[0,0,0,0],[1,1,1,1],[1,1,0,0],[0,0,1,1]]*2
    opts=dict(epochs=1000,rate=.1,seed=42,validation=0)
    first=em.train(m,data,opts);second=em.train(m,data,opts)
    assert first==second
    assert first['history'][-1]['train_nll']<first['history'][0]['train_nll']
    assert first['history'][-1]['train_reconstruction_mse']<first['history'][0]['train_reconstruction_mse']
    assert first['training']['algorithm']=='CD-1'
    assert not m.W.flags.writeable


@pytest.mark.parametrize('kind',['bm','rbm'])
def test_validation_rows_do_not_affect_updates(kind):
    m=em.initialize(kind,2,2);data=np.array([[0,0],[1,1],[1,0],[0,1]],float)
    seed=7;heldout=np.random.default_rng(seed).permutation(4)[:2]
    changed=data.copy();changed[heldout]=1-changed[heldout]
    opts=dict(epochs=12,seed=seed,validation=.5)
    a=em.train(m,data,opts);b=em.train(m,changed,opts)
    assert a['model']==b['model']
    assert a['training']['train_rows']==a['training']['validation_rows']==2
    assert 'validation_nll' in a['history'][-1]


@pytest.mark.parametrize('kind',['bm','rbm'])
def test_seeded_binary_sampling_uniform_model(kind):
    m=em.rbm([[0,0],[0,0]],[0,0],[0,0]) if kind=='rbm' else em.boltzmann_machine([[0,0],[0,0]],[0,0])
    a=em.sample(m,512,42);assert np.array_equal(a,em.sample(m,512,42))
    assert a.shape==(512,2) and set(a.ravel())=={0,1}
    np.testing.assert_allclose(a.mean(axis=0),[.5,.5],atol=.07)
    assert em.analyze(m,count=1)['visible_entropy_bits']==pytest.approx(2)
    np.testing.assert_array_equal(em.energy_state(6,4),[0,1,1,0])


def test_large_rbm_sampling_without_claiming_exact_probabilities():
    m=em.initialize('rbm',13,2)
    report=em.train(m,[[0]*13,[1]*13],dict(epochs=2))
    assert not report['exact_available'] and 'top_states' not in report
    assert 'train_nll' not in report['history'][0]
    with pytest.raises(em.EnergyError,match='12 visible'):em.energy_probability(m,[0]*13)


@pytest.mark.parametrize('bad',[True,'4',None,2.2,float('nan'),float('inf'),-1])
def test_invalid_unit_counts(bad):
    with pytest.raises(em.EnergyError):em.initialize(visible=bad)


def test_model_data_and_work_limits():
    for W in ([[1,0],[0,0]],[[0,1],[0,0]],[[0]]):
        with pytest.raises(em.EnergyError):em.boltzmann_machine(W,[0,0])
    with pytest.raises(em.EnergyError):em.rbm([[1j]],[0],[0])
    with pytest.raises(em.EnergyError):em.rbm([[101]],[0],[0])
    with pytest.raises(em.EnergyError):em.rbm([[1]],[0],[0],0)
    for data in ([[.1,.7]],[[0]],[[float('nan'),1]],[],[[0,1]]*2049):
        with pytest.raises(em.EnergyError):em.training_data(data,2)
    np.testing.assert_array_equal(em.training_data([[.49,.5]],2,True,.5),[[0,1]])
    m=em.initialize('rbm',16,16)
    with pytest.raises(em.EnergyError,match='too large'):em.options(dict(epochs=2000,k=20),m,2048)
    with pytest.raises(em.EnergyError,match='binary'):em.energy_probability(em.initialize('rbm',2,2),[.2,.7])


def test_training_and_sampling_honor_cancellation():
    def stop():raise ComputationCancelled()
    m=em.initialize('rbm',2,2)
    with pytest.raises(ComputationCancelled):em.train(m,[[0,0]],dict(epochs=10),check=stop)
    with pytest.raises(ComputationCancelled):em.sample(m,check=stop)


def test_worksheet_models_parameterized_models_derivatives_and_export():
    texts=['M=rbm([[.5,-.7],[1.2,.4]],[.2,-.3],[.1,.6])','M([1,0])',
           'energy(M,[1,0],[0,1])','R(t)=rbm([[t]],[0],[0])','R(2)',
           'energy_probability(R(2),[1])','U(r)=free_energy(M,r)','F(r)=force(U,r)','F([.2,.7])',
           'energy_weights(M)','energy_bias(M)','hidden_bias(M)','energy_sample(M,3,42)','log_partition(M)']
    c=Calculator([{'text':t} for t in texts]);rows=c.run([-1,1,-1,1])
    assert not any(r.get('error') for r in rows),rows
    assert rows[0]['kind']=='energy_model' and rows[3]['kind']=='energy_model_function'
    assert rows[4]['kind']=='energy_model'
    m=c.evaluate(parse('M'));r=np.array([.2,.7])
    assert rows[-1]['value']==pytest.approx(em.log_partition(m))
    expected=m.a+m.W@em.hidden_probabilities(m,r)
    np.testing.assert_allclose(c.evaluate(parse('F([.2,.7])')),expected,rtol=1e-5)
    # Full-precision large matrices must survive row-chunked worksheet export.
    m=em.initialize('rbm',16,16);root=Path(__file__).resolve().parents[1]
    js="const e=require('./static/energy-tools.js');let s='';process.stdin.on('data',x=>s+=x);process.stdin.on('end',()=>process.stdout.write(JSON.stringify(e.definitions(JSON.parse(s),'RBM_1'))));"
    texts=json.loads(subprocess.check_output(['node','-e',js],input=json.dumps(em.pack(m)).encode(),cwd=root))
    assert len(texts)<=40 and max(map(len,texts))<=1200
    restored=Calculator([{'text':t} for t in texts]).evaluate(parse('RBM_1'))
    assert em.pack(restored)==em.pack(m)


def wait_for(manager,ident):
    deadline=time.monotonic()+40
    while time.monotonic()<deadline:
        report=manager.poll(ident)
        if report['state']!='running':return report
        time.sleep(.01)
    pytest.fail('Energy training did not complete')


def test_energy_api_data_sources_and_background_training(monkeypatch):
    import async_compute
    manager=JobManager(workers=2,executor_factory=lambda n:ThreadPoolExecutor(n))
    monkeypatch.setattr(async_compute,'manager',manager)
    try:
        client=app.test_client()
        initialized=client.post('/api/energy',json=dict(action='initialize',kind='bm',visible=2))
        assert initialized.status_code==200
        model=initialized.json['analysis']['model']
        data=dict(model=model,options=dict(epochs=5,validation=0))
        expressions=[{'text':'D=[[0,0],[1,1]]'},{'text':'M=boltzmann_machine([[0,0],[0,0]],[0,0])'}]
        dataset={'id':'d1','name':'patterns','columns':[{'name':'a','values':[0,1]},{'name':'b','values':[0,1]}],'x':'a','y':['b'],'style':'markers','visible':True}
        sources=[dict(data=[[0,0],[1,1]]),dict(data=[[.1,.3],[.8,.9]],binarize=True),dict(expressions=expressions,data_expression='D'),dict(datasets=[dataset],data_columns=['patterns_a','patterns_b'])]
        for source in sources:
            r=client.post('/api/energy/jobs',json={**data,**source});assert r.status_code==202,r.json
            result=wait_for(manager,r.json['job_id']);assert result['state']=='complete'
            event=result['results'][0];assert event['kind']=='energy'
            assert event['result']['training']['train_rows']==2,event
            assert client.get('/api/jobs/'+r.json['job_id']).status_code==200
        loaded=client.post('/api/energy',json=dict(source='M',expressions=expressions))
        assert loaded.status_code==200 and loaded.json['analysis']['visible']==2
        for bad in ([],dict(data=data),{**data,'data':[[.5,1]]},{**data,'data_columns':['missing']},{**data,'options':{'epochs':True}}):
            assert client.post('/api/energy/jobs',json=bad).status_code==400
        page=client.get('/').text
        assert 'id="energyBtn"' in page and 'energy-tools.js' in page
    finally:manager.close(wait=True)


def test_energy_training_in_spawned_process():
    manager=JobManager(workers=1)
    try:
        payload=dict(expressions=[],datasets=[],graphs=[],bounds=[-1,1,-1,1],energy_task=dict(model=em.pack(em.initialize('rbm',2,2)),data=[[0,0],[1,1]],options=dict(epochs=20)))
        job=manager.submit(payload);result=wait_for(manager,job['job_id'])
        assert result['state']=='complete' and result['mode']=='process',result
        assert result['results'][0]['result']['history'][-1]['epoch']==20,result
    finally:manager.close(wait=True)
