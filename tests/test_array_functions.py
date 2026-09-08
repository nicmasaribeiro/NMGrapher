import numpy as np
import pytest
from engine import Calculator
from app import app


def run(*lines, domain=False, selected=None):
    rows=[{'text':line} for line in lines]
    if selected is not None: rows[-1]['plot_component']=selected
    result=Calculator(rows).run([-2,2,-2,2],complex_domain=domain)
    assert not any(r.get('error') for r in result), [(r['text'],r.get('error')) for r in result]
    return result


def test_screenshot_vector_times_complex_scalar_function():
    r=run('φ_1=[1,i]','w(t)=exp(i*t)','Φ_1(t)=φ_1*w(t)','Φ_1(0)')
    f=r[2];x=np.array(f['x'])
    assert f['shape']==[2] and len(f['components'])==2
    np.testing.assert_allclose(f['components'][0]['y'],np.cos(x),atol=1e-12)
    np.testing.assert_allclose(f['components'][1]['y'],-np.sin(x),atol=1e-12)
    np.testing.assert_allclose(f['components'][1]['imag'],np.cos(x),atol=1e-12)
    assert r[3]['value']==[1.0,'0+1i']


def test_vector_and_matrix_literals_with_mixed_constant_entries():
    r=run('v(t)=[t,1]','M(t)=[[t,0],[2,t^2]]','q(t)=M(t)*v(t)','q(2)','p(t)=M(t)@v(t)','h(t)=q(t)[1]')
    assert r[1]['shape']==[2,2]
    assert r[3]['value']==[4,8]
    x=np.array(r[2]['x'])
    np.testing.assert_allclose(r[2]['components'][0]['y'],x*x)
    np.testing.assert_allclose(r[2]['components'][1]['y'],2*x+x*x)
    np.testing.assert_allclose(r[4]['components'][1]['y'],r[2]['components'][1]['y'])
    assert 'components' not in r[5]
    np.testing.assert_allclose(r[5]['y'],2*x+x*x)


def test_matrix_power_and_exponential_at_sampled_inputs():
    r=run('A=[[0,1],[0,0]]','E(t)=expm(t*A)','P(t)=[[t,1],[0,t]]^2','E(2)')
    assert r[3]['value']==[[1,2],[0,1]]
    np.testing.assert_allclose(r[1]['components'][1]['y'],r[1]['x'],atol=1e-12)
    np.testing.assert_allclose(r[2]['components'][1]['y'],2*np.array(r[2]['x']))


@pytest.mark.parametrize('formula,shape,index,expected',[
    ('v(s,t)=[s,t,s*t]',[3],2,lambda a,b:a*b),
    ('M(s,t)=[[s,0],[t,s+t]]',[2,2],3,lambda a,b:a+b),
])
def test_two_variable_component_surfaces(formula,shape,index,expected):
    r=run(formula,selected=index)[0]
    assert r['kind']=='surface' and r['shape']==shape
    assert r['components'][0]['index']==index
    a,b=np.meshgrid(r['x'],r['y'])
    np.testing.assert_allclose(r['real'],expected(a,b),atol=1e-12)


def test_complex_domain_array_output():
    r=run('v(z)=[z,z^2]',domain=True,selected=1)[0]
    assert r['kind']=='complex_field' and len(r['components'])==1
    a,b=np.meshgrid(r['x'],r['y'])
    np.testing.assert_allclose(r['magnitude'],np.abs((a+1j*b)**2),atol=1e-12)


def test_large_matrix_selects_any_entry_without_plotting_all_entries():
    r=run('M(t)=t*eye(32)',selected=1023)[0]
    assert r['shape']==[32,32] and r['component_count']==1024
    assert len(r['components'])==1 and r['components'][0]['label']=='[31, 31]'
    np.testing.assert_allclose(r['y'],r['x'])
    default=run('M(t)=t*eye(4)')[0]
    assert len(default['components'])==8


def test_quantum_expectation_and_vector_calculus():
    r=run('ψ(t)=Ry(t)@ket0()','z(t)=expect(pauliZ(),ψ(t))','v(t)=[t^2,sin(t)]','d(t)=diff(v(t),t)','I(t)=integrate(v(s),s,0,t)')
    x=np.array(r[1]['x'])
    np.testing.assert_allclose(r[1]['y'],np.cos(x),atol=1e-10)
    np.testing.assert_allclose(r[3]['components'][0]['y'],2*x,atol=1e-8)
    np.testing.assert_allclose(r[3]['components'][1]['y'],np.cos(x),atol=1e-8)
    np.testing.assert_allclose(r[4]['components'][0]['y'],x**3/3,atol=1e-8)
    np.testing.assert_allclose(r[4]['components'][1]['y'],1-np.cos(x),atol=1e-8)


def test_scalar_contraction_of_vector_function_and_bare_calls():
    r=run('v(t)=[t,2]','f(t)=inner(v(t),v(t))','v(x)','v(x+y)')
    assert 'components' not in r[1]
    np.testing.assert_allclose(r[1]['y'],np.array(r[1]['x'])**2+4)
    assert r[2]['shape']==[2] and r[3]['kind']=='surface'


def test_shape_changes_and_bad_products_are_clear_errors():
    r=Calculator([{'text':'v(t)=roots(1,where(t<0,2,3))'},{'text':'q(t)=[[t,0],[0,t]]@[1,2,3]'}]).run([-2,2,-2,2])
    assert 'shape changes' in r[0]['error']
    assert 'inner dimensions' in r[1]['error']


@pytest.mark.parametrize('selection',[False,-1,1024,'bad',[],None])
def test_api_rejects_invalid_entry_selection(selection):
    res=app.test_client().post('/api/evaluate',json={'expressions':[{'text':'v(t)=[t,1]','plot_component':selection}]})
    assert res.status_code==400


def test_api_serializes_array_function_and_resizable_pane_markup():
    client=app.test_client()
    response=client.post('/api/evaluate',json={'expressions':[{'text':'M(t)=[[t,i*t],[0,1]]','plot_component':1}]})
    assert response.status_code==200
    r=response.get_json()['results'][0]
    assert r['selected_component']==1 and len(r['components'])==1
    html=client.get('/').get_data(as_text=True)
    assert 'id="paneDivider" role="separator" tabindex="0"' in html
    assert 'aria-controls="equationPane"' in html and 'id="functionTemplate"' in html
