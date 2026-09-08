import numpy as np
import pytest
from engine import Calculator
from notation import normalize_notation
from math_preview import preview
from app import app


def run(*rows):return Calculator([{'text':s} for s in rows]).run([-2,2,-2,2])

def nodes(tree):
    yield tree
    for child in tree.get('children',[]):yield from nodes(child)


def test_screenshot_integral_function_and_derivative_operator():
    r=run('S_1(x)=x','Q_1(t,x,φ)=-t*x+i*φ','π_1(t,θ,φ)=∫_{0}^{θ} (S_1(x)*exp(Q_1(t,x,φ))) dx','π_1(0,2,0)','C(t)=t^3','d/dt(C(t))')
    assert not any(a.get('error') for a in r),[(a['text'],a.get('error')) for a in r]
    assert r[3]['value']==pytest.approx(2)
    assert r[5]['kind']=='curve'
    np.testing.assert_allclose(r[5]['y'],3*np.array(r[5]['x'])**2,atol=1e-7)
    assert r[2]['function']['parameters']==['t','θ','φ']


@pytest.mark.parametrize('text',[
    '∫_{0}^{2} (x^2) dx','∫_0^2 x^2 dx','∫_{0}^{1+1} (x^2) d x',
    r'\int_{0}^{2} (x^2) dx',
])
def test_integral_forms(text):assert run(text)[0]['value']==pytest.approx(8/3)


def test_nested_integrals_scope_and_external_addition():
    r=run('x_1=99','∫_0^1 (∫_0^x t dt) dx','∫_0^1 x dx + 2','∫_0^1 x_1 dx','x_1')
    assert r[1]['value']==pytest.approx(1/6) and r[2]['value']==pytest.approx(2.5)
    assert r[3]['value']==pytest.approx(99) and r[4]['value']==99


def test_primitive_is_anchored_and_allows_alternative_base():
    r=run('F(x)=∫ (x^2) dx','F(0)','F(2)','G(x)=antiderivative(1/x,x,1)','G(2)','d/dx(F(x))')
    assert r[1]['value']==0 and r[2]['value']==pytest.approx(8/3)
    assert r[4]['value']==pytest.approx(np.log(2))
    np.testing.assert_allclose(r[5]['y'],np.array(r[5]['x'])**2,atol=1e-7)


@pytest.mark.parametrize('operator',['d^2/dx^2','d²/dx²','d^{2}/dx^{2}'])
def test_second_derivative_forms(operator):
    r=run('x_1=3',f'D(x)={operator}(x^3)','D(2)')
    assert r[2]['value']==pytest.approx(12,abs=1e-6)


def test_greek_operator_and_pasted_fraction():
    assert normalize_notation('d/dtheta_1(theta_1^2)')=='diff(θ_1^2, θ_1)'
    assert normalize_notation(r'\frac{d}{dt}\left(C(t)\right)')=='diff(C(t), t)'
    assert run('θ_1=3','d/dθ₁(θ₁^2)')[1]['value']==pytest.approx(6,abs=1e-7)


@pytest.mark.parametrize('text',['d/dx','d²/dx(x)','∫_0 (x) dx','∫_0^1 x','∫_0^1 () dx','∫_{}^1 x dx'])
def test_incomplete_notation_fails_clearly(text):assert 'error' in run(text)[0]


def test_matrix_integral_and_derivative_functions():
    r=run('M(t)=[[t,0],[0,t^2]]','F(t)=∫_{0}^{t} (M(s)) ds','F(2)','D(t)=d/dt(M(t))','D(2)')
    assert not any(a.get('error') for a in r),[a.get('error') for a in r]
    np.testing.assert_allclose(r[2]['value'],[[2,0],[0,8/3]],atol=1e-8)
    np.testing.assert_allclose(r[4]['value'],[[1,0],[0,4]],atol=1e-7)


def test_preview_has_integral_limits_exponent_and_derivative_fraction():
    tree=preview('π_1(t,θ,φ)=∫_{0}^{θ} (S_1(x)*exp(Q_1(t,x,φ))) dx')['tree']
    tags=[n['tag'] for n in nodes(tree)]
    assert 'msubsup' in tags and 'msup' in tags and 'msub' in tags
    integral=next(n for n in nodes(tree) if n['tag']=='msubsup')
    assert integral['children'][0]['text']=='∫'
    assert integral['children'][1]['text']=='0' and integral['children'][2]['text']=='θ'
    tree=preview('d/dt(C(t))')['tree']
    fraction=next(n for n in nodes(tree) if n['tag']=='mfrac')
    assert fraction['children'][0]['text']=='d'
    assert [n.get('text') for n in nodes(fraction['children'][1]) if 'text' in n]==['d','t']


def test_preview_points_matrices_multiline_and_indexing():
    tree=preview('diff(x^2,x,2)')['tree']
    assert any(n.get('text')=='|' for n in nodes(tree))
    assert any(n['tag']=='mtable' for n in nodes(preview('[[1,i],[-i,2]]')['tree']))
    assert any(n['tag']=='msubsup' for n in nodes(preview('F(x)=integrate(\n t^2,t,0,x\n)')['tree']))
    text=[n.get('text') for n in nodes(preview('A[0,1]')['tree']) if 'text' in n]
    assert text==['A','[','0',',','1',']']


def test_preview_endpoint_is_non_evaluating_and_returns_per_row_errors():
    client=app.test_client()
    r=client.post('/api/preview',json={'expressions':['F(x)=integrate(unknown(t),t,0,x)','d/dx(',"__import__('os').system('bad')"]})
    assert r.status_code==200
    previews=r.get_json()['previews']
    assert 'tree' in previews[0] and 'error' in previews[1] and 'error' in previews[2]
    assert client.post('/api/preview',json={'expressions':['x']*61}).status_code==400
