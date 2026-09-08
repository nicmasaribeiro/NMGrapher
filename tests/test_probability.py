import numpy as np
import pytest
from app import app
from engine import Calculator
import probability as p


def run(*rows):
    result=Calculator([{'text':s} for s in rows]).run([-4,4,-1,1])
    assert not any(r.get('error') for r in result),result
    return result


def test_normal_density_cdf_intervals_and_tail_accuracy():
    d=p.FUNCTIONS['normal'](0,1)
    assert p.density(d,0)==pytest.approx(1/np.sqrt(2*np.pi))
    assert p.cumulative(d,0)==.5
    assert p.interval(d,-1,1)==pytest.approx(.6826894921370859)
    assert p.interval(d,9,10)>0  # subtracting CDFs would cancel to zero
    assert p.quantile(d,.975)==pytest.approx(1.959963984540054)


def test_binomial_and_poisson_mass_and_interval_endpoints():
    b=p.FUNCTIONS['binomial'](10,.5);n=p.FUNCTIONS['poisson'](4)
    assert p.mass(b,5)==pytest.approx(252/1024)
    assert p.interval(b,3,7)==pytest.approx(sum(p.mass(b,np.arange(3,8))))
    assert p.interval(b,3.2,6.9)==pytest.approx(sum(p.mass(b,[4,5,6])))
    assert p.interval(b,3.2,3.8)==0
    assert p.mass(n,2)==pytest.approx(8*np.exp(-4))
    assert p.mass(n,2.5)==0


def test_boltzmann_stability_repeated_states_and_energy_shift():
    a=p.boltzmann([0,1,1,2],.5);b=p.boltzmann([10000,10001,10001,10002],.5)
    np.testing.assert_allclose(a.weights,b.weights)
    assert sum(a.weights)==pytest.approx(1)
    assert a.weights[1]==a.weights[2]
    assert p.energy(a)==pytest.approx(np.dot([0,1,1,2],a.weights))
    assert p.boltzmann([0,1e100],1e-12).weights==(1,0)


@pytest.mark.parametrize('family,args,mean,variance',[
 ('uniform',(2,6),4,16/12),('exponential',(2,),.5,.25),('geometric',(.25,),4,12),
 ('poisson',(0,),0,0),('binomial',(0,.5),0,0),('binomial',(5,1),5,0)])
def test_other_families_and_degenerate_cases(family,args,mean,variance):
    d=p.FUNCTIONS[family](*args)
    assert d.rv.mean()==pytest.approx(mean) and d.rv.var()==pytest.approx(variance)
    assert p.plot(d)['x']


def test_seeded_samples_do_not_change_global_rng():
    d=p.FUNCTIONS['normal']();np.random.seed(7);first=np.random.get_state()
    a=p.draw(d,100,42);np.testing.assert_array_equal(a,p.draw(d,100,42))
    assert not np.array_equal(a,p.draw(d,100,43))
    np.testing.assert_array_equal(first[1],np.random.get_state()[1])


def test_named_distributions_statistics_calculus_and_existing_quantum():
    r=run('D=normal(0,1)','mean(D)','variance(D)','std(D)','median(D)','entropy(D)','pdf(D,x)','cdf(D,x)','integrate(pdf(D,t),t,-1,1)','mean([1,2,3])','entropy(qubit(1,0))','probabilities(qubit(1,0))','Q=boltzmann([0,1],1)','probabilities(Q)','sample(D,100,42)')
    assert r[0]['kind']=='distribution' and r[1]['value']==0 and r[2]['value']==1
    assert r[6]['kind']=='curve' and r[7]['kind']=='curve'
    assert r[8]['value']==pytest.approx(.6826894921370859)
    assert r[9]['value']==2 and r[10]['value']==0
    assert r[-1]['kind']=='series' and r[-1]['count']==100


@pytest.mark.parametrize('source',['normal(0,0)','poisson(-1)','binomial(2.5,0.5)','binomial(2,2)','boltzmann([0,i],1)','boltzmann([0,1],0)','uniform(2,1)','geometric(0)','pdf(poisson(2),1)','pmf(normal(),1)','quantile(normal(),1.1)','sample(normal(),10001,0)'])
def test_invalid_distributions_and_queries(source):
    result=Calculator([{'text':source}]).run([-1,1,-1,1])[0]
    assert result.get('error'),result


def test_probability_api_queries_context_and_plot_limits():
    c=app.test_client();payload={'distribution':'D','expressions':[{'text':'D=normal(0,1)'}],'query':{'operation':'cdf','arguments':['0']}}
    r=c.post('/api/probability',json=payload)
    assert r.status_code==200 and r.json['analysis']['query']['value']==.5
    payload['query']={'operation':'quantile','arguments':['1']};r=c.post('/api/probability',json=payload)
    assert r.json['analysis']['query']=={'value':None,'nonfinite':True}
    assert c.post('/api/probability',json={'distribution':'poisson(1)','range':[0,3000]}).status_code==400
    assert c.post('/api/probability',json={'distribution':'[1,2]'}).status_code==400


def test_distributions_with_function_dependent_parameters():
    r=run('f(t)=pdf(normal(t,1),0)','f(2)','g(x,y)=pdf(normal(x,1),y)')
    assert r[0]['kind']=='curve'
    assert r[1]['value']==pytest.approx(np.exp(-2)/np.sqrt(2*np.pi))
    assert r[2]['kind']=='surface'
