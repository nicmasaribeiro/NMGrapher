import numpy as np
import pytest
from app import app
from graphing import graph_results, validate_graphs


def spec(kind='function', **kwargs):
    return dict(id='g1', type=kind, name='Test', color='#2864d7', visible=True,
                parameter='t', range=[0, 2*np.pi], yrange=[-2,2], samples=101, **kwargs)


def run(g, rows=(), datasets=()):
    result=graph_results([g],[{'text':s} for s in rows],list(datasets))[0]
    assert 'error' not in result, result
    return result


def test_cartesian_and_vector_function_coordinates():
    g=spec('function',y='f(x)');r=run(g,['a=2','f(t)=a*sin(t)'])
    np.testing.assert_allclose(r['y'],2*np.sin(r['x']),atol=1e-12)
    r=run(spec('parametric',x='v(t)[0]',y='v(t)[1]'),['v(t)=[cos(t),sin(t)]'])
    np.testing.assert_allclose(np.array(r['x'])**2+np.array(r['y'])**2,1,atol=1e-12)


def test_polar_negative_radius_and_greek_parameter():
    g=spec('polar',r='-2*cos(theta)');g['parameter']='theta'
    r=run(g);t=np.array(r['parameter'])
    np.testing.assert_allclose(r['x'],-2*np.cos(t)**2,atol=1e-12)
    np.testing.assert_allclose(r['y'],-2*np.cos(t)*np.sin(t),atol=1e-12)


def test_helix_coordinates():
    r=run(spec('parametric3d',x='cos(t)',y='sin(t)',z='t/4'))
    assert r['dimension']==3
    np.testing.assert_allclose(r['z'],np.array(r['parameter'])/4)


@pytest.mark.parametrize('kind',['surface','contour','implicit'])
def test_grid_orientation_and_zero_level(kind):
    g=spec(kind,z='x+2*y',expression='x+2*y=3');r=run(g)
    x,y=np.meshgrid(r['x'],r['y'])
    np.testing.assert_allclose(r['z'],x+2*y-(3 if kind=='implicit' else 0))


def test_missing_pairs_and_histogram_counts():
    dataset={'id':'data','name':'data_1','columns':[{'name':'x','values':[1,None,3,4]},{'name':'y','values':[2,4,None,8]}],'x':'x','y':['y'],'style':'lines','visible':True}
    for kind in ['scatter','line','bar']:
        r=run(spec(kind,x='data_1_x',y='data_1_y'),datasets=[dataset])
        assert r['x']==[1,None,None,4] and r['y']==[2,None,None,8] and r['omitted']==2
    r=run(spec('histogram',values='data_1_y',bins=3),datasets=[dataset])
    assert sum(r['y'])==3 and r['omitted']==1
    r=run(spec('line',y='[4,2,8]'))
    assert r['x']==[0,1,2]


def test_complex_and_singular_gaps_align_coordinates():
    g=spec('parametric',x='1/t',y='sqrt(t-1)');r=run(g)
    assert r['x'][0] is None and r['y'][0] is None
    assert r['gaps']>0
    result=graph_results([spec(y='[x,2*x]')],[],[])[0]
    assert 'scalar' in result['error']


def test_invalid_graph_isolated_and_hidden_not_evaluated():
    a=spec(y='unknown(x)');b={**spec(y='sin(x)'), 'id':'g2'}
    r=graph_results([a,b],[],[])
    assert 'error' in r[0] and 'error' not in r[1]
    a['visible']=False
    assert graph_results([a],[],[])[0]['hidden']


@pytest.mark.parametrize('change',[{'samples':10001},{'range':[0,0]},{'range':[0,float('inf')]},{'parameter':'i'},{'type':[]},{'visible':'yes'},{'color':'red'}])
def test_spec_validation(change):
    with pytest.raises(ValueError):validate_graphs([{**spec(y='x'),**change}])


def test_graph_api_context_and_limits():
    c=app.test_client()
    r=c.post('/api/graphs',json={'graphs':[spec(y='a*x')],'expressions':[{'text':'a=3'}]})
    assert r.status_code==200
    np.testing.assert_allclose(r.json['results'][0]['y'],3*np.array(r.json['results'][0]['x']))
    assert c.post('/api/graphs',json={'graphs':[spec(y='x')]*13}).status_code==400
    assert c.post('/api/graphs',json={'graphs':[spec(y="__import__('os')")]}).json['results'][0]['error']
    assert c.post('/api/graphs',json={'graphs':[spec('scatter',x='[1]',y='[1,2]')]}).json['results'][0]['error']


def test_distribution_graph_mass_and_cdf():
    g=spec('probability',expression='B');g['range']=[0,10]
    r=run(g,['B=binomial(10,0.5)']);assert sum(r['y'])==pytest.approx(1)
    g['probability_mode']='cdf';r=run(g,['B=binomial(10,0.5)'])
    assert r['discrete'] and r['y'][-1]==1
