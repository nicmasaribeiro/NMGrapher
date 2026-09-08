import numpy as np
import pytest
from engine import Calculator
from app import app
from calculus import multivariable


def calc(text):
    r=Calculator([{'text':text}]).run([-2,2,-2,2])[0]
    assert 'error' not in r,r.get('error')
    return r


@pytest.mark.parametrize('operator,expected',[
    ('grad',[4,9,18]), ('gradient',[4,9,18]),
    ('hessian',[[2,1,0],[1,4,0],[0,0,6]]), ('laplacian',12),
])
def test_energy_derivatives(operator,expected):
    r=calc(f'{operator}(x^2+2*y^2+3*z^2+x*y,[x,y,z],[1,2,3])')
    np.testing.assert_allclose(r['real'],expected,atol=2e-7)
    info=r['calculus'][-1]
    assert info['variables']==['x','y','z'] and info['evaluations']>0
    assert info['undefined_samples']==0 and info['error_estimate'] is not None


@pytest.mark.parametrize('operator,expected',[
    ('jacobian',[[2,1,0],[0,3,2],[3,0,1]]),
    ('divergence',6), ('curl',[-2,-3,-1]),
])
def test_vector_field_operators(operator,expected):
    r=calc(f'{operator}([x*y,y*z,z*x],[x,y,z],[1,2,3])')
    np.testing.assert_allclose(r['real'],expected,atol=1e-8)


def test_mixed_derivative_and_hessian_cross_terms():
    np.testing.assert_allclose(calc('hessian(x^3*y^2,[x,y],[2,3])')['real'],[[108,72],[72,16]],atol=2e-6)
    assert calc('mixed_diff(x^3*y^2,[x,y],[2,3])')['value']==pytest.approx(72,abs=2e-6)


def test_complex_gradient_and_directional_scaling():
    r=calc('grad(y*exp(i*x),[x,y],[1,2])')
    actual=np.array(r['real'])+1j*np.array(r['imag'])
    np.testing.assert_allclose(actual,[2j*np.exp(1j),np.exp(1j)],atol=1e-8)
    assert calc('directional(x^2+y^2,[x,y],[2,0],[3,4])')['value']==pytest.approx(12,abs=1e-8)
    r=calc('directional([[x,y],[x*y,x^2]],[x,y],[1,2],[3,4])')
    np.testing.assert_allclose(r['real'],[[1,2],[10,6]],atol=1e-8)


def test_matrix_output_jacobian_flattening_and_laplacian():
    r=calc('jacobian([[x,y],[x*y,x^2]],[x,y],[2,3])')
    assert r['shape']==[4,2]
    np.testing.assert_allclose(r['real'],[[1,0],[0,1],[3,2],[4,0]],atol=1e-8)
    r=calc('laplacian([[x^2,x*y],[sin(x),y^2]],[x,y],[1,2])')
    np.testing.assert_allclose(r['real'],[[2,0],[-np.sin(1),2]],atol=1e-7)
    r=calc('jacobian(x*y,[x,y],[2,3])')
    assert r['shape']==[1,2]


def test_at_binds_all_parameters_and_preserves_algebraic_types():
    r=calc('at(grad(a*x^2+b*y,[x,y]),[a,b,x,y],[2,3,4,5])')
    np.testing.assert_allclose(r['real'],[16,3],atol=1e-8)
    r=calc('at(hessian(x^2+y^2,[x,y]),[x,y],[1,2]) * [3,4]')
    np.testing.assert_allclose(r['real'],[6,8],atol=1e-7)
    assert calc('at(diff(floor(x),x),[x],[2.4])')['value']==pytest.approx(0,abs=1e-9)
    assert calc('at(diff(diff(x^2,x),x),[x],[1])')['value']==pytest.approx(2,abs=1e-5)


def test_variable_binding_greek_and_argument_order():
    r=calc('grad(alpha^2+3*beta^2,[beta,alpha],[2,3])')
    np.testing.assert_allclose(r['real'],[12,6],atol=1e-8)
    r=calc('at(mixed_diff(alpha*beta,[alpha,beta]),[alpha,beta],[2,3])')
    assert r['kind']=='scalar' and r['value']==pytest.approx(1,abs=1e-7)


def test_multivariable_fields_and_user_function_dependencies():
    rows=[{'text':'E(x,y,z)=x^2+y^2+z^2'},
          {'text':'g(x,y,z)=grad(E(x,y,z),[x,y,z])','plot_slice':{'axes':['x','y'],'fixed':{'z':3}}},
          {'text':'h(x,y,z)=hessian(E(x,y,z),[x,y,z])','plot_slice':{'axes':['x'],'fixed':{'y':2,'z':3}}}]
    r=Calculator(rows).run([-2,2,-2,2])
    assert not any(a.get('error') for a in r),[a.get('error') for a in r]
    assert r[1]['shape']==[3] and len(r[1]['x'])==32
    x,y=np.meshgrid(r[1]['x'],r[1]['y'])
    np.testing.assert_allclose(r[1]['real'],2*x,atol=1e-8)
    assert r[2]['shape']==[3,3]
    np.testing.assert_allclose(r[2]['y'],2,atol=2e-6)


def test_integral_tolerances_and_complex_matrix_outputs():
    r=calc('integrate([[t^2,i*t],[0,sin(t)]],t,0,1,1e-10,1e-9)')
    np.testing.assert_allclose(r['real'],[[1/3,0],[0,1-np.cos(1)]],atol=1e-10)
    np.testing.assert_allclose(r['imag'],[[0,.5],[0,0]],atol=1e-10)
    assert r['calculus'][-1]['absolute_tolerance']==1e-10
    assert calc('integrate(t^2,t,1,0,1e-10)')['value']==pytest.approx(-1/3)


@pytest.mark.parametrize('text',[
    'grad([x,y],[x,y],[1,2])','hessian([x,y],[x,y],[1,2])',
    'divergence([x,y],[x,y,z],[1,2,3])','curl([x,y],[x,y],[1,2])',
    'jacobian(eye(6)*x,[x],[1])','grad(x,[],[])','grad(x,[x,x],[1,2])',
    'grad(x,[pi],[1])','grad(x,[x],[1,2])','grad(x,[x],[1],-1)',
    'grad(x,[x],[1],1e-300)','directional(x,[x],[i],[1])','directional(x,[x],[1,2],[1])',
    'mixed_diff(x,[x],[1])','at(x,[x])','at(x,[x],[1,2])',
    'integrate(x,x,0,1,-1)','integrate(x,x,0,1,1e-9,-1)',
    'integrate(x,x,0,1,1e-14)','grad(abs(x),[x],[0])',
])
def test_invalid_shapes_points_options_and_nonsmooth_points(text):
    r=Calculator([{'text':text},{'text':'1+1'}]).run([-2,2,-2,2])
    assert 'error' in r[0],text
    assert r[1]['value']==2


def test_undefined_point_has_diagnostics_and_api_roundtrip():
    r=app.test_client().post('/api/evaluate',json={'expressions':[{'text':'grad(abs(x),[x],[0])'}]}).get_json()['results'][0]
    assert 'error' in r and r['calculus'][-1]['undefined_samples']==1
    r=app.test_client().post('/api/evaluate',json={'expressions':[{'text':'at(curl([-y,x,z],[x,y,z]),[x,y,z],[1,2,3])'}]}).get_json()['results'][0]
    np.testing.assert_allclose(r['real'],[0,0,2],atol=1e-8)


def test_kernel_rejects_changing_shapes():
    with pytest.raises(ValueError,match='shape changes'):
        multivariable(lambda p:np.array([p[0]]) if p[0]<=0 else np.array([p[0],1]),[0],'jacobian')
