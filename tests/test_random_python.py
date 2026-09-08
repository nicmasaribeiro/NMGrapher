import ast
import json
import numpy as np
import pytest
from app import app
from engine import Calculator, parse
from random_math import random_vector, random_matrix, activate, random_gate, stochastic_matrix


def value(rows, expression):
    c=Calculator(rows+[{'text':expression}])
    r=c.run([-1,1,-1,1],indices=[len(rows)])[0]
    assert not r.get('error'),r
    return r


def test_random_reproducibility_and_activation():
    a=random_matrix(3,4,42)
    np.testing.assert_array_equal(a,random_matrix(3,4,42))
    assert not np.array_equal(a,random_matrix(3,4,43))
    np.testing.assert_array_equal(activate(a,0,42),np.zeros_like(a))
    np.testing.assert_array_equal(activate(a,1,42),a)
    assert np.all((activate(a,.5,42)==a)|(activate(a,.5,42)==0))
    gate=random_gate(a,.5,42)
    assert np.array_equal(gate,a) or not np.any(gate)
    np.testing.assert_allclose(stochastic_matrix(4,42).sum(axis=1),1)
    r=value([{'text':'A=random_matrix(2,2,42)'},{'text':'v=random_vector(2,42)'}],'A*v')
    np.testing.assert_allclose(r['value'],random_matrix(2,2,42)@random_vector(2,42))


@pytest.mark.parametrize('call', ['random_vector(0)','random_matrix(2,33)','random_vector(2,-1)','activate([1,2],1.1)','random_gate([1,2],-1)','random_vector(2,1.5)'])
def test_random_validation(call):
    assert Calculator([{'text':call}]).run([-1,1,-1,1])[0].get('error')


def test_python_exports_loops_branch_and_numpy():
    source='''import numpy as np
A = np.array([[1, 2], [3, 4]])
v = np.array([1, 0])
b = 2
b += 3
def f(t):
    total = 0
    for k in range(4):
        total += t ** k
    if t < 0:
        return 0
    return total
'''
    rows=[{'type':'python','text':source}]
    assert value(rows,'b')['value']==5
    assert value(rows,'f(2)')['value']==15
    assert value(rows,'f(-2)')['value']==0
    assert value(rows,'A*v')['value']==[1,3]
    assert value(rows,'integrate(f(x),x,0,1)')['value']==pytest.approx(1+1/2+1/3+1/4)
    result=Calculator(rows+[{'text':'f(x)'}]).run([-1,1,-1,1])
    assert result[0]['kind']=='python' and len(result[0]['exports'])==4
    assert result[1]['kind']=='curve'


@pytest.mark.parametrize('source', ["import os", "a = open(1)", "a = (1).__class__", "while True:\n    pass", "def f(t):\n    return __import__(t)", 'def f(t):\n    for k in range(100000):\n        t += k\n    return t', '@sin\ndef f(t):\n    return t', 'def f(t):\n    return [n for n in range(3)]'])
def test_python_rejects_unsupported(source):
    c=Calculator([{'type':'python','text':source}])
    # Unknown calls are rejected by the numeric evaluator, never executed.
    r=c.run([-1,1,-1,1])[0]
    if source=='a = open(1)':
        assert value_error(c,'a')
    else:assert r.get('error'),r


def value_error(c,text):
    try:c.evaluate(parse(text))
    except ValueError:return True
    return False


def test_python_duplicate_names_atomic_and_api_metadata():
    rows=[{'text':'A=2'},{'type':'python','text':'B = 3\nA = 4'}]
    c=Calculator(rows)
    assert 'B' not in c.definitions and c.items[1].get('error')
    rows=[{'type':'python','text':'def f(t):\n    a = sin(t)\n    return a ** 2'}]
    client=app.test_client()
    r=client.post('/api/evaluate',json={'expressions':rows,'validate_only':True})
    assert r.json['results'][0]['exports'][0]['name']=='f'
    r=client.post('/api/evaluate',json={'expressions':rows+[{'text':'f(0)'}],'indices':[1]})
    assert r.json['results'][0]['value']==0
    assert client.post('/api/evaluate',json={'expressions':[{'type':'bad','text':'1'}]}).status_code==400


def test_batched_multiple_integrals_dependent_bounds_and_vectors():
    rows=[{'text':'F(x,y)=sin(x)*cos(y)'}]
    r=value(rows,'integrate(F(x,y),[y,x],[0,0],[x,1])')
    assert r['value']==pytest.approx(0.5-np.sin(2)/4,rel=1e-7)
    r=value([],'integrate([x,y],[y,x],[0,0],[x,1])')
    np.testing.assert_allclose(r['value'],[1/3,1/6])


def test_seeded_python_exports_in_spawned_workers():
    import time
    from async_compute import JobManager
    from app import evaluation_payload
    rows=[{'type':'python','text':'A = random_matrix(2, 2, 42)\ndef response(t):\n    return A @ [t, 1]'},
          {'text':'response(2)'},{'text':'A @ [2,1]'}]
    manager=JobManager(workers=2)
    try:
        payload=evaluation_payload({'expressions':rows});payload['graphs']=[]
        job=manager.submit(payload)
        deadline=time.monotonic()+35
        while time.monotonic()<deadline:
            snapshot=manager.poll(job['job_id'])
            if snapshot['state']!='running':break
            time.sleep(.02)
        assert snapshot['state']=='complete',snapshot
        results={event['index']:event['result'] for event in snapshot['results']}
        assert results[0]['kind']=='python'
        assert results[1]['value']==results[2]['value']
    finally:manager.close(wait=True)


def test_reported_integral_values_against_independent_quadrature():
    from scipy.integrate import quad
    rows=[{'text':t} for t in [
        'f_0(x)=(1-x^2)*exp(-x^2/2)',
        'f_1(x)=(1-(x^3-3x^2*(1-x))^2)*exp(-(x^3-3x^2*(1-x))^2/2)',
        'F(x,y)=f_0(x)*f_1(y)',
        'g(θ,φ)=∫_{0}^{θ} ∫_{0}^{φ} F(x,y) dydx',
        'N(x)=normaldist(0,1).pdf(x)',
        'i_0(t)=∫_{0}^{t} N(x) log10(N(x)/f_0(x)) dx',
        'i_1(t)=∫_{0}^{t} N(x) log10(N(x)/f_1(x)) dx']]
    c=Calculator(rows)
    f0=lambda x:(1-x*x)*np.exp(-x*x/2)
    f1=lambda x:f0(x**3-3*x*x*(1-x))
    expected=quad(f0,0,1)[0]*quad(f1,0,1)[0]
    assert c.evaluate(parse('g(1,1)'))==pytest.approx(expected,abs=1e-7)
    for name,denominator in [('i_0',f0),('i_1',f1)]:
        def integrand(x):
            normal=np.exp(-x*x/2)/np.sqrt(2*np.pi)
            return normal*np.emath.log10(normal/denominator(x))
        reference=quad(lambda x:integrand(x).real,0,1.5,points=[1])[0]+1j*quad(lambda x:integrand(x).imag,0,1.5,points=[1])[0]
        c.steps=0
        assert c.evaluate(parse(name+'(1.5)'))==pytest.approx(reference,abs=2e-7)


def test_python_boolean_short_circuit():
    rows=[{'type':'python','text':'def f(t):\n    if t != 0 and 1/t > 0:\n        return True\n    return False'}]
    assert value(rows,'f(0)')['value']==0
    assert value(rows,'f(2)')['value']==1


def test_multiple_integral_work_limit_retains_other_coordinates(monkeypatch):
    from engine import EvaluationLimit
    c=Calculator([{'text':'f(t)=integrate(x*y,[y,x],[0,0],[t,t])'}])
    original=c.evaluate
    root=c.items[0]['tree']
    def evaluate(node,local=None,stack=()):
        if node is root and local and local.get('t',0)>0.5:
            raise EvaluationLimit('Evaluation limit reached; simplify the expression.')
        return original(node,local,stack)
    monkeypatch.setattr(c,'evaluate',evaluate)
    result=c.run([-1,1,-1,1])[0]
    assert not result.get('error')
    assert result['x'][0]==-1 and result['x'][-1]==1
    assert any(v is None for v in result['y'])
    assert any(v is not None for v in result['y'])
    assert 'per-point work limit' in result['sampling']['notice']
