import numpy as np
import pytest
from app import app
from engine import Calculator
from notation import normalize_notation
from symbols import GREEK_LETTERS


def run(*lines, slice=None, domain=False):
    rows=[{'text':line} for line in lines]
    if slice is not None:rows[0]['plot_slice']=slice
    return Calculator(rows).run([-2,2,-2,2],complex_domain=domain)


def test_many_arguments_default_slice_and_direct_composition():
    r=run('f(x,y,z,t)=x+2*y+3*z+4*t','f(1,2,3,4)','g(a,b,c,d)=f(d,c,b,a)','g(1,2,3,4)')
    assert not any('error' in a for a in r)
    assert r[0]['function']['parameters']==['x','y','z','t']
    assert r[0]['plot_slice']=={'axes':['x','y'],'fixed':{'z':0.0,'t':0.0}}
    x,y=np.meshgrid(r[0]['x'],r[0]['y'])
    np.testing.assert_allclose(r[0]['real'],x+2*y)
    assert r[1]['value']==30 and r[3]['value']==20


def test_no_small_argument_count_cap():
    args=[f'u_{i}' for i in range(100)]
    r=run('f('+','.join(args)+')=u_0+u_99','f('+','.join(str(i) for i in range(100))+')')
    assert len(r[0]['function']['parameters'])==100
    assert r[1]['value']==99


def test_arbitrary_surface_axes_with_fixed_inputs():
    r=run('f(a,b,c,d)=a+2*b+3*c+4*d',slice={'axes':['d','b'],'fixed':{'a':5,'c':7}})[0]
    assert r['parameters']==['d','b']
    d,b=np.meshgrid(r['x'],r['y'])
    np.testing.assert_allclose(r['real'],26+2*b+4*d)


def test_one_axis_slice_and_complex_domain():
    config={'axes':['c'],'fixed':{'a':2,'b':3}}
    r=run('f(a,b,c)=a+b*c^2',slice=config)[0]
    assert r['kind']=='curve'
    np.testing.assert_allclose(r['y'],2+3*np.array(r['x'])**2)
    r=run('f(a,b,c)=a+b*c^2',slice=config,domain=True)[0]
    assert r['kind']=='complex_field'
    x,y=np.meshgrid(r['x'],r['y'])
    np.testing.assert_allclose(r['magnitude'],np.abs(2+3*(x+1j*y)**2))


def test_nary_vector_matrix_functions_and_calculus():
    rows=[{'text':'v(a,b,c)=[a*c,b+c]','plot_slice':{'axes':['c'],'fixed':{'a':2,'b':3}}},
          {'text':'M(a,b,c)=[[a,b],[0,c]]'}, {'text':'M(2,3,4)*v(1,2,3)'},
          {'text':'d(a,b,c)=diff(v(a,b,c),c)','plot_slice':{'axes':['c'],'fixed':{'a':2,'b':3}}},
          {'text':'I(a,b,c)=integrate(a+b*s,s,0,c)','plot_slice':{'axes':['c'],'fixed':{'a':2,'b':3}}}]
    r=Calculator(rows).run([-2,2,-2,2])
    assert not any('error' in a for a in r),r
    c=np.array(r[0]['x'])
    np.testing.assert_allclose(r[0]['components'][0]['y'],2*c)
    assert r[1]['shape']==[2,2] and r[2]['value']==[21,20]
    np.testing.assert_allclose(r[3]['components'][0]['y'],2,atol=1e-8)
    np.testing.assert_allclose(r[3]['components'][1]['y'],1,atol=1e-8)
    np.testing.assert_allclose(r[4]['y'],2*c+1.5*c*c,atol=1e-8)


@pytest.mark.parametrize('call',['f(1,2)','f(1,2,3,4)'])
def test_arity_errors_are_explicit(call):
    r=run('f(a,b,c)=a+b+c',call)
    assert 'expects 3 argument(s)' in r[1]['error']


@pytest.mark.parametrize('config',[
    {'axes':[]}, {'axes':['a','b','c']}, {'axes':['a','a']}, {'axes':['missing']},
    {'axes':['a'],'fixed':{'a':2}}, {'axes':['a'],'fixed':{'b':'2'}},
    {'axes':['a'],'fixed':{'b':float('inf')}}, {'axes':['a'],'fixed':{'b':True}},
    {'axes':['a'],'fixed':{'b':1e7}}, {'axes':'a'}, {'fixed':[]}, [], {'unexpected':1},
])
def test_invalid_plot_slices_are_row_errors(config):
    r=run('f(a,b,c)=a+b+c','1+1',slice=config)
    assert 'error' in r[0] and r[1]['value']==2


@pytest.mark.parametrize('name,lower,upper',GREEK_LETTERS)
def test_all_greek_keywords_and_case_insensitivity(name,lower,upper):
    for word in (name,name.lower(),name.upper()):
        assert normalize_notation(word)==lower
        assert normalize_notation(word+'_1')==lower+'_1'
        assert normalize_notation(word+'₁')==lower+'_1'
    assert normalize_notation(upper)==upper


def test_keywords_in_parameters_definitions_calls_and_slice_names():
    r=run('omega(alpha,beta,gamma)=alpha+beta*gamma','ω(1,2,3)',
          slice={'axes':['Gamma'],'fixed':{'alpha':1,'β':2}})
    assert r[0]['function']['name']=='ω'
    assert r[0]['function']['parameters']==['α','β','γ']
    assert r[1]['value']==7
    np.testing.assert_allclose(r[0]['y'],1+2*np.array(r[0]['x']))
    r=run('lambda=2','alpha_1=3','λ+α₁','sin(pi/2)','Omega(t)=lambda*t')
    assert r[2]['value']==5 and r[3]['value']==pytest.approx(1)
    assert r[4]['function']['name']=='ω'


def test_keyword_alias_collisions_and_reserved_pi():
    assert 'already defined' in run('alpha=1','α=2')[1]['error']
    assert 'different names' in run('f(alpha,α,gamma)=1')[0]['error']
    assert 'reserved' in run('pi=2')[0]['error']
    assert 'reserved' in run('f(x,Pi,z)=x')[0]['error']


def test_keyword_boundaries_and_existing_identifiers():
    text='alphabet + betamax + alpha2 + my_alpha + exp + constructor + __proto__'
    assert normalize_notation(text)==text
    assert normalize_notation('alpha_rate + beta_{2} + gamma²')=='α_rate + β_2 + γ^(2)'


def test_api_nary_metadata_and_keywords_catalog():
    client=app.test_client()
    r=client.post('/api/evaluate',json={'expressions':[{'text':'f(a,b,c)=a+b+c','plot_slice':{'axes':['b'],'fixed':{'a':1,'c':3}}}]}).get_json()['results'][0]
    assert r['function']['parameters']==['a','b','c'] and r['kind']=='curve'
    keywords=client.get('/api/symbols').get_json()['keywords']
    assert len(keywords)==24 and keywords['lambda']=='λ'
