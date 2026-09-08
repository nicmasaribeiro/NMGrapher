import ast
import json
import time
import numpy as np
import pytest
from engine import Calculator, parse
from graphing import graph_results, validate_graphs
from app import app,evaluation_payload


def calculator(*texts):return Calculator([{'text':t} for t in texts])
def evaluate(c,text):
    c.steps=0
    return c.evaluate(parse(text))

def graph(kind='vectorfield',**kwargs):
    return dict(id='field',type=kind,name='Force',color='#2864d7',visible=True,
                parameter='t',range=[-1,1],yrange=[-1,1],zrange=[-1,1],samples=100,
                density=3,expression='F([x,y])',**kwargs)


def test_position_vector_definition_and_coordinate_style():
    c=calculator('F(x)=[-x[1],x[0]]','G(x,y)=[-y,x]')
    r=c.run([-1,1,-1,1],indices=[0])[0]
    assert r['kind']=='field_function' and r['input_dimensions']==2 and not r.get('error')
    np.testing.assert_allclose(evaluate(c,'F([2,3])'),[-3,2])
    for name in ('F','G'):
        assert evaluate(c,f'field_divergence({name},[2,3])')==pytest.approx(0,abs=1e-7)
        assert evaluate(c,f'field_curl({name},[2,3])')==pytest.approx(2,abs=1e-7)
        np.testing.assert_allclose(evaluate(c,f'field_jacobian({name},[2,3])'),[[0,-1],[1,0]],atol=1e-7)
        np.testing.assert_allclose(evaluate(c,f'field_directional({name},[2,3],[2,0])'),[0,2],atol=1e-7)
        np.testing.assert_allclose(evaluate(c,f'field_convective({name},[2,3])'),[-2,-3],atol=1e-7)


def test_force_hessian_laplacian_and_chain():
    c=calculator('U(r)=dot(r,r)/2','F(r)=force(U,r)')
    assert all(r['kind']=='field_function' for r in c.run([-1,1,-1,1]))
    np.testing.assert_allclose(evaluate(c,'force(U,[1,2,3])'),[-1,-2,-3],atol=1e-7)
    np.testing.assert_allclose(evaluate(c,'field_hessian(U,[1,2,3])'),np.eye(3),atol=1e-5)
    np.testing.assert_allclose(evaluate(c,'field_gradient(U,[1,2,3])'),[1,2,3],atol=1e-7)
    assert evaluate(c,'field_laplacian(U,[1,2,3])')==pytest.approx(3,abs=1e-5)
    assert evaluate(c,'field_divergence(F,[1,2,3])')==pytest.approx(-3,abs=2e-4)


def test_three_dimensions_and_n_dimensions():
    c=calculator('F(r)=[-r[1],r[0],r[2]^2]','G(x,y,z)=[-y,x,z^2]', 'V(r)=[r[0],r[1],r[2],r[3]]')
    for name in ('F','G'):
        np.testing.assert_allclose(evaluate(c,f'field_curl({name},[1,2,3])'),[0,0,2],atol=1e-6)
        np.testing.assert_allclose(evaluate(c,f'field_laplacian({name},[1,2,3])'),[0,0,2],atol=1e-5)
        assert evaluate(c,f'field_divergence({name},[1,2,3])')==pytest.approx(6,abs=1e-6)
    assert evaluate(c,'field_divergence(V,[1,2,3,4])')==pytest.approx(4,abs=1e-6)


def test_work_orientation_and_potential_difference():
    c=calculator('F(r)=[-r[1],r[0]]','circle(t)=[cos(t),sin(t)]',
                 'U(r)=(r[0]^2+r[1]^2)/2','G(r)=force(U,r)','path(t)=[t,2*t]')
    assert evaluate(c,'work(F,circle,0,2*pi)')==pytest.approx(2*np.pi,abs=2e-6)
    assert evaluate(c,'work(F,circle,2*pi,0)')==pytest.approx(-2*np.pi,abs=2e-6)
    assert evaluate(c,'work(G,path,0,1)')==pytest.approx(-2.5,abs=2e-6)
    assert evaluate(c,'work(F,circle,0,0)')==pytest.approx(0,abs=1e-8)


def test_existing_symbolic_calculus_and_position_expressions():
    c=calculator('F(r)=[-r[1],r[0]]')
    assert evaluate(c,'divergence(F([x,y]),[x,y],[1,2])')==pytest.approx(0,abs=1e-7)
    assert c.evaluate(ast.parse('at(x+y,[x,y],[1,2] if 1<2 else [3,4])',mode='eval').body)==pytest.approx(3)
    np.testing.assert_allclose(evaluate(c,'jacobian(F([x,y]),[x,y],[1,2])'),[[0,-1],[1,0]],atol=1e-7)


@pytest.mark.parametrize('expression',[
    'field_divergence(F,[1])','field_divergence(F,[1,2,3])',
    'field_gradient(F,[1,2])','force(F,[1,2])','field_curl(S,[1,2])',
    'field_jacobian(F,[1,i])','field_jacobian(F,[1,2],-1)',
    'field_directional(F,[1,2],[1,2,3])','field_divergence(unknown,[1,2])',
    'work(F,path,0,1)','work(F,F,0,1)','field_divergence(F,1)',
    'field_divergence(F,[1,2],1,2)'])
def test_invalid_field_operations(expression):
    c=calculator('F(r)=[-r[1],r[0]]','S(r)=r[0]^2','path(t)=[t,t,t]')
    with pytest.raises((ValueError,IndexError,TypeError)):evaluate(c,expression)


def test_field_grids_and_real_vector_validation():
    for kind,expression,body,dimensions in [('vectorfield','F([x,y])','[-r[1],r[0]]',2),('vectorfield3d','F([x,y,z])','[-r[1],r[0],-r[2]]',3)]:
        g=graph(kind);g['expression']=expression
        r=graph_results([g],[{'text':f'F(r)={body}'}],[])[0]
        assert not r.get('error'),r
        assert len(r['positions'])==3**dimensions and r['dimension']==dimensions
        np.testing.assert_allclose(np.asarray(r['vectors'])[:,0],-np.asarray(r['positions'])[:,1])
        assert r['magnitudes'][len(r['magnitudes'])//2]==0
    g=graph();g['expression']='[1/x,y]'
    r=graph_results([g],[],[])[0];assert r['gaps']==3 and len(r['positions'])==6
    for expression in ('[i*x,y]','[x,y,1]','x+y'):
        g['expression']=expression
        assert graph_results([g],[],[])[0].get('error')
    g['expression']='[1e100,1e100]';r=graph_results([g],[],[])[0]
    assert np.all(np.isfinite(r['magnitudes']))


@pytest.mark.parametrize('changes',[{'density':26},{'density':True},{'arrow_scale':0},{'normalize':1},{'zrange':[2,1]},{'type':'vectorfield3d','density':12}])
def test_graph_option_limits(changes):
    g=graph();g.update(changes)
    with pytest.raises(ValueError):validate_graphs([g])


def test_field_api_python_and_spawned_graph():
    from async_compute import JobManager
    rows=[{'type':'python','text':'def F(r):\n    return [-r[1], r[0]]'}, {'text':'field_curl(F,[1,2])'}]
    c=app.test_client()
    result=c.post('/api/evaluate',json={'expressions':rows,'indices':[1]})
    assert result.status_code==200 and result.json['results'][0]['value']==pytest.approx(2,abs=1e-6)
    payload=evaluation_payload({'expressions':rows});payload['graphs']=validate_graphs([graph()])
    manager=JobManager(workers=2)
    try:
        job=manager.submit(payload);deadline=time.monotonic()+35
        while time.monotonic()<deadline:
            snapshot=manager.poll(job['job_id'])
            if snapshot['state']!='running':break
            time.sleep(.02)
        assert snapshot['state']=='complete',snapshot
        event=next(e for e in snapshot['results'] if e['kind']=='graph')
        assert not event['result'].get('error') and len(event['result']['vectors'])==9
    finally:manager.close(wait=True)


def test_shorthand_field_operators_and_previews():
    from math_preview import preview
    c=calculator('F(r)=[-r[1],r[0]]','U(r)=dot(r,r)/2')
    assert evaluate(c,'curl(F,[1,2])')==pytest.approx(2,abs=1e-6)
    assert evaluate(c,'divergence(F,[1,2])')==pytest.approx(0,abs=1e-6)
    np.testing.assert_allclose(evaluate(c,'grad(U,[1,2])'),[1,2],atol=1e-6)
    assert c.free_names(parse('jacobian(F,[x,y])'))=={'x','y'}
    assert '∇' in json.dumps(preview('force(U,[1,2])'),ensure_ascii=False)
    assert '∫' in json.dumps(preview('work(F,r,0,2*pi)'),ensure_ascii=False)
