import numpy as np
import pytest
from engine import Calculator
from math_preview import preview
from app import app
import wavelets


def run(*text):
    out=Calculator([{'text':v} for v in text]).run([-2,2,-2,2])
    assert not any(v.get('error') for v in out),[(v['text'],v.get('error')) for v in out]
    return out


def test_all_screenshot_statistics():
    r=run('L=[1,2,3,4]','mean(L)','median(L)','min(L)','max(L)','quartile(L,1)','quantile(L,0.75)','stdev(L)','stdevp(L)','var(L)','varp(L)','cov(L,2*L)','covp(L,2*L)','mad(L)','corr(L,2*L)','spearman(L,-L)','stats(L)','count(L)','total(L)')
    expected=[2.5,2.5,1,4,1.75,3.25,np.sqrt(5/3),np.sqrt(1.25),5/3,1.25,10/3,2.5,1,1,-1]
    for value,expect in zip(r[1:],expected):assert value['value']==pytest.approx(expect)
    assert r[16]['value']==[1,1.75,2.5,3.25,4]
    assert r[17]['value']==4 and r[18]['value']==10


def test_distribution_quantiles_and_legacy_statistics_unchanged():
    r=run('D=normal(0,1)','quantile(D,0.5)','variance([1,2,3])','std([1,2,3])','min(2,3)','max([1,4],[2,3])','log(exp(1))','log10(100)','ln(exp(1))')
    assert r[1]['value']==0
    assert r[2]['value']==pytest.approx(2/3) and r[3]['value']==pytest.approx(np.sqrt(2/3))
    assert r[4]['value']==2 and r[5]['value']==[2,4]
    assert [v['value'] for v in r[6:]]==[1,2,1]


def test_tied_spearman_and_missing_pairs():
    r=run('spearman([1,1,2,3],[2,2,3,4])')
    assert r[0]['value']==pytest.approx(1)
    d={'id':'data','name':'d','columns':[{'name':'a','values':[1,None,3]},{'name':'b','values':[2,4,6]}],'x':'a','y':['b'],'visible':True,'style':'lines'}
    r=Calculator([{'text':s} for s in ['corr(d_a,d_b)','count(d_a)','stats(d_b)']],[d]).run([-2,2,-2,2])
    assert r[0].get('error') and r[1]['value']==2 and r[2]['kind']=='vector'


@pytest.mark.parametrize('expr',['var([1])','corr([1,1],[2,3])','cov([1,2],[3])','quartile([1,2],5)','quantile([1,2],-1)','log_1(8)'])
def test_invalid_stats(expr):
    assert Calculator([{'text':expr}]).run([-1,1,-1,1])[0].get('error')


def test_hyperbolic_and_log_base_notation():
    r=run('sinh(1)','cosh(1)','tanh(1)','csch(1)','sech(1)','coth(1)','log_2(8)','log₂(8)','a=2','log_{a+1}(27)','log(8,2)')
    np.testing.assert_allclose([v['value'] for v in r[:6]],[np.sinh(1),np.cosh(1),np.tanh(1),1/np.sinh(1),1/np.cosh(1),1/np.tanh(1)])
    assert [r[i]['value'] for i in [6,7,9,10]]==pytest.approx([3,3,3,3])


def test_sums_products_binding_empty_and_nested():
    r=run('k=100','∑_{k=1}^{4}(k^2)','∏_{k=1}^{4}(k)','sum(k,k,1,4)','sum(k,k,4,1)','product(k,k,4,1)','sum(sum(k*q,q,1,2),k,1,3)','Σ_1=4','Π_1=5','Σ_1+Π_1','product([[1,k],[0,1]],k,1,3)')
    assert [v['value'] for v in r[1:7]]==[30,24,10,0,1,18]
    assert r[9]['value']==9
    assert r[10]['value']==[[1,6],[0,1]]
    assert Calculator([{'text':'sum(k,k,1,10001)'}]).run([-1,1,-1,1])[0].get('error')


def test_prime_function_derivatives_and_integrals():
    r=run('f(t)=t^3',"f'(2)",'f′(2)',"f''(2)","f'(x)","f''(t)",'F(x)=∫_{0}^{x}(f(t)) dt','F(2)')
    assert [r[i]['value'] for i in [1,2,3]]==pytest.approx([12,12,12],rel=1e-6)
    assert r[4]['kind']==r[5]['kind']=='curve'
    assert r[7]['value']==pytest.approx(4)
    assert Calculator([{'text':'f(x,y)=x*y'},{'text':"f'(1)"}]).run([-1,1,-1,1])[-1].get('error')


def test_previews_sum_product_prime_and_log():
    def texts(n):return ([n['text']] if 'text'in n else [])+sum((texts(c) for c in n.get('children',[])),[])
    for expression,symbol in [('∑_{k=1}^{4}(k^2)','∑'),('∏_{k=1}^{4}(k)','∏'),("f'(x)",'′'),('log_2(8)','log')]:
        tree=preview(expression)['tree'];assert symbol in texts(tree)


def test_wavelet_transform_objects_and_inverses():
    signal=np.sin(np.arange(129)/5)
    d=wavelets.dwt(signal,3,2)
    np.testing.assert_allclose(wavelets.idwt(d),signal,atol=1e-12)
    np.testing.assert_allclose(sum(wavelets.transform_band(d,i) for i in range(4)),signal,atol=1e-12)
    c=wavelets.cwt(signal,[4,8,16],0,.5)
    assert c.coefficients.shape==(3,129)
    np.testing.assert_allclose(c.frequencies,[.5,.25,.125])
    np.testing.assert_allclose(wavelets.transform_coefficients(c,1),wavelets.cwt(signal,8))
    with pytest.raises(ValueError,match='CWT inversion'):wavelets.idwt(c)
    with pytest.raises(ValueError):wavelets.cwt(signal,[0,8])


def test_wavelet_transform_api_worksheet_reuse():
    client=app.test_client();values=np.sin(np.arange(128)/7).tolist()
    dataset={'id':'s','name':'sensor','columns':[{'name':'value','values':values}],'x':None,'y':['value'],'visible':True,'style':'lines'}
    rows=['W=dwt(sensor_value,3,2)','idwt(W)','wavelet_coeffs(W,0)','wavelet_band(W,1)','C=cwt(sensor_value,[4,8,16],0,0.5)','wavelet_power(C,1)','wavelet_frequencies(C)']
    r=client.post('/api/evaluate',json={'datasets':[dataset],'expressions':[{'text':s} for s in rows]}).json['results']
    assert not any(v.get('error') for v in r),r
    assert r[0]['kind']==r[4]['kind']=='wavelet_transform'
    assert r[1]['kind']==r[2]['kind']=='series'
    np.testing.assert_allclose(r[1]['real'],values,atol=1e-12)
    assert r[-1]['real']==[.5,.25,.125]
