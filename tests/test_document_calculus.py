import json
from pathlib import Path
import numpy as np
import pytest
from scipy.integrate import quad
from scipy.stats import norm
from engine import Calculator, parse
from notation import normalize_notation
from math_preview import preview
from app import app

DEMO=json.loads((Path(__file__).parents[1]/'examples/desmos_demo.json').read_text())


def value(text, rows=()):
    c=Calculator([{'text':s} for s in rows]);c.steps=0
    return c.evaluate(parse(text)),c


def test_all_twelve_document_lines_render_and_evaluate():
    r=Calculator(DEMO['rows']).run(DEMO['bounds'],curve_range=DEMO['curve_range'])
    assert not any(v.get('error') for v in r),[(i+1,v.get('error')) for i,v in enumerate(r)]
    assert r[3]['kind']=='surface'
    assert r[8]['kind']=='surface' and r[9]['kind']=='curve'
    assert r[11]['value']==pytest.approx(1)
    x=np.array(r[9]['x'])
    np.testing.assert_allclose(r[9]['y'],3*(x**3-3*x)*np.exp(-x*x/2),atol=1e-7)
    x,y=np.meshgrid(r[8]['x'],r[8]['y'])
    np.testing.assert_allclose(r[8]['real'],np.ones_like(x)) # empty products below N=1


def test_pdf_formulas_against_independent_quadrature():
    rows=[v['text'] for v in DEMO['rows']]
    f0=lambda x:(1-x*x)*np.exp(-x*x/2)
    f1=lambda x:f0(x**3-3*x*x*(1-x))
    v,c=value('g(1,1)',rows)
    expected=quad(f0,0,1)[0]*quad(f1,0,1)[0]
    assert v==pytest.approx(expected,abs=1e-8)
    assert c.calculus_diagnostics[-1]['dimensions']==2
    for name,f in [('i_0',f0),('i_1',f1)]:
        v,_=value(f'{name}(0.5)',rows)
        expected=quad(lambda x:norm.pdf(x)*np.log10(norm.pdf(x)/f(x)),0,.5)[0]
        assert v==pytest.approx(expected,abs=1e-8)
    v,_=value('p_t(0.2,3)',rows)
    assert v==pytest.approx(f0(.2)**3)


@pytest.mark.parametrize('expr,expected',[
    ('∫_0^1 ∫_0^y (x+y) dxdy',.5),
    ('integrate(x+y,[x,y],[0,0],[y,1])',.5),
    ('∫_0^1 ∫_0^1 ∫_0^1 (x+y+z) dzdydx',1.5),
    ('integrate(1,[x,y,z],[0,0,0],[y,z,1])',1/6),
    ('integrate(x+y,[x,y],[1,0],[0,1])',-1),
    ('∫_0^1 ∫_0^x x dx dx',1/6),
    ('integrate(x+y,[x,y],[0,0],[0,1])',0),
    ('∫_0^1 ∫_0^1 (x+i*y) dydx',.5+.5j),
    ('∫_0^1 ∫_0^1 (x*y) d y d x',.25),
])
def test_multiple_integral_scoping_and_bound_order(expr,expected):
    v,c=value(expr,['x=99','y=88'])
    assert v==pytest.approx(expected,abs=1e-9)
    assert c.calculus_depth==0


def test_multiple_integral_preserves_vector_matrix_shape():
    for expr,expected in [('integrate([x,y],[x,y],[0,0],[1,1])',[.5,.5]),
                          ('integrate([[x,i*y],[1,x*y]],[x,y],[0,0],[1,1])',[[.5,.5j],[1,.25]])]:
        v,_=value(expr);np.testing.assert_allclose(v,expected,atol=1e-10)


@pytest.mark.parametrize('expr',[
    'integrate(x,[x,x],[0,0],[1,1])',
    'integrate(x,[x,y],[0],[1,1])',
    'integrate(x,[x,y,z,t],[0,0,0,0],[1,1,1,1])',
    'integrate(x,[i,y],[0,0],[1,1])',
    'integrate(x+y,[x,y],[0,0],[1,i])',
    'integrate(x+y,[x,y],[0,0],[1,1],-1)',
    'integrate(x+y,[x,y],[0,0],[1,x])', # outer bound cannot use an unbound inner coordinate
])
def test_invalid_regions_and_tolerances(expr):
    with pytest.raises(ValueError):value(expr)


def test_distribution_aliases_methods_calls_and_composition():
    rows=['D=normaldist(0,1)','N(x)=D.pdf(x)','B=binomialdist(4,0.5)',
          'family(m,s)=normaldist(m,s)','f(x)=normaldist(0,1).pdf(x)']
    cases={'D(0)':norm.pdf(0),'N(0)':norm.pdf(0),'family(0,1).pdf(0)':norm.pdf(0),
           'normaldist(0,1)(0)':norm.pdf(0),'D.cdf(-1,1)':norm.cdf(1)-norm.cdf(-1),
           'D.inversecdf(.5)':0,'D.mean':0,'D.var':1,'D.stdev()':1,
           'B(2)':.375,'B(2.2)':0,'B.pdf(2.2)':.375,'B.pmf(2.2)':0,
           '∫_0^1 D(x) dx':norm.cdf(1)-.5,'at(d/dx f(x),[x],[0])':0}
    for expr,expected in cases.items():
        v,_=value(expr,rows+['x=0']);assert v==pytest.approx(expected,abs=1e-8),expr
    c=Calculator([{'text':s} for s in ['D=normaldist(0,1)','D(x)','D.pdf(x)']])
    r=c.run([-1,1,-1,1]);assert not any(v.get('error') for v in r)
    np.testing.assert_allclose(r[1]['y'],norm.pdf(r[1]['x']))


@pytest.mark.parametrize('expr',[
    'normaldist(0,1).__class__','normaldist(0,1).rv.pdf(0)',
    'normaldist(0,1).pdf.__globals__','normaldist(0,1).pdf(x=0)',
    'normaldist(0,1).rvs(1000000000)','sin(0).pdf(0)','D(0)',
])
def test_distribution_access_remains_restricted(expr):
    with pytest.raises((ValueError,TypeError)):value(expr,['D=3'])


def test_parameterized_reductions_real_bounds_binding_and_derivative():
    rows=['n=99','f_0(t)=(1-t^2)*exp(-t^2/2)','p_t(t,N)=∏_{n=1}^{N} f_0(t)']
    for bound,count in [(0,0),(.9,0),(1,1),(2.9,2),(3,3)]:
        v,_=value(f'p_t(.2,{bound})',rows)
        assert v==pytest.approx(((1-.2**2)*np.exp(-.2**2/2))**count)
    assert value('∑_{n=1.2}^{3.8} n')[0]==5
    assert value('∏_{n=3}^{1} n')[0]==1
    assert value('∑_{n=3}^{1} n')[0]==0
    assert value('at(d/dx ∑_{n=1}^{3} x^2,[x],[2])')[0]==pytest.approx(12,abs=1e-8)


def test_pdf_preview_and_api_methods_and_multiple_integrals():
    for row in DEMO['rows']:assert preview(row['text'])['tree']
    tree=preview('integrate(x+y,[x,y],[0,0],[y,1])')['tree']
    def texts(t):return [t.get('text')]+[s for c in t.get('children',[]) for s in texts(c)]
    assert texts(tree).count('∫')==2
    assert normalize_notation('d/dx ∑_{n=1}^{3} f_0(x)')=='diff(summation(f_0(x), n, 1, 3), x)'
    response=app.test_client().post('/api/evaluate',json={'expressions':[{'text':'∫_0^1 ∫_0^1 normaldist(0,1).pdf(x)*y dxdy'}]})
    assert response.status_code==200
    assert response.json['results'][0]['value']==pytest.approx((norm.cdf(1)-.5)/2,abs=1e-8)


def test_parameterized_distribution_definitions_and_column_methods():
    rows=[{'text':'family(m,s)=normaldist(m,s)'},
          {'text':'f(x)=family(x,1).pdf(0)'},
          {'text':'normaldist(0,1).pdf(data_v)'}, {'text':'D=normaldist(0,1)'}, {'text':'D(data_v)'}]
    dataset={'id':'d','name':'data','columns':[{'name':'v','values':[0,1,None]}],
             'x':None,'y':['v'],'visible':True,'style':'lines'}
    r=Calculator(rows,[dataset]).run([-1,1,-1,1])
    assert not any(v.get('error') for v in r),r
    assert r[0]['kind']=='distribution_function'
    np.testing.assert_allclose(r[1]['y'],norm.pdf(r[1]['x']))
    assert r[2]['kind']==r[4]['kind']=='series'
    assert r[2]['real']==r[4]['real'] and r[2]['real'][-1] is None


def test_document_product_inside_double_integral_crosses_integer_bound():
    rows=[v['text'] for v in DEMO['rows']]
    v,_=value('c_0(2)',rows)
    assert v==pytest.approx(2+2*np.exp(-2),abs=1e-7)
