import numpy as np
import pytest
from app import app
from engine import Calculator
import wavelets as w


@pytest.mark.parametrize('wavelet',sorted(w.DWT_WAVELETS))
@pytest.mark.parametrize('mode',['symmetric','periodization'])
def test_perfect_reconstruction_and_additive_bands(wavelet,mode):
    x=np.random.default_rng(4).normal(size=257)
    r=w.decompose(x,wavelet,level=3,mode=mode,strength=0)
    np.testing.assert_allclose(r['reconstruction'],x,atol=2e-10)
    np.testing.assert_allclose(r['denoised'],x,atol=2e-10)
    np.testing.assert_allclose(np.sum([b['values'] for b in r['bands']],axis=0),x,atol=2e-10)
    assert [b['name'] for b in r['bands']]==['A3','D3','D2','D1']


def test_wavelet_functions_zero_mean_and_unit_energy():
    t=np.linspace(-20,20,50001)
    for fn in [w.mexican_hat,w.morlet]:
        y=fn(t,2,1)
        assert abs(np.trapezoid(y,t))<1e-6
        assert np.trapezoid(abs(y)**2,t)==pytest.approx(1,abs=1e-6)
    assert w.haar(np.array([-.1,0,.49,.5,.99,1])).tolist()==[0,1,1,-1,-1,0]


def test_cwt_detects_frequency_and_respects_time_units():
    dt=1/128;t=np.arange(1024)*dt;x=np.sin(2*np.pi*8*t)
    r=w.continuous(x,dt,min_scale=4,max_scale=64,count=48)
    assert r['dominant_frequency']==pytest.approx(8,rel=.12)
    scaled=w.continuous(x,2*dt,min_scale=4,max_scale=64,count=48)
    np.testing.assert_allclose(r['power'],scaled['power'])
    np.testing.assert_allclose(r['frequency'],np.array(scaled['frequency'])*2)


def test_cwt_localizes_frequency_switch():
    t=np.arange(1024)/128;x=np.sin(2*np.pi*np.where(t<4,8,20)*t)
    r=w.continuous(x,1/128,min_scale=4,max_scale=32,count=64)
    power=np.asarray(r['power']);time=np.asarray(r['time']);freq=np.asarray(r['frequency'])
    assert freq[np.argmax(power[:,abs(time-2).argmin()])]==pytest.approx(8,rel=.15)
    assert freq[np.argmax(power[:,abs(time-6).argmin()])]==pytest.approx(20,rel=.15)


def test_denoise_reduces_error_for_seeded_noisy_sine():
    t=np.arange(1024)/128;clean=np.sin(2*np.pi*2*t);noisy=clean+.3*np.random.default_rng(1).normal(size=len(t))
    r=w.decompose(noisy,'db4',level=4)
    assert np.mean((r['denoised']-clean)**2)<np.mean((noisy-clean)**2)
    assert r['threshold']>0
    constant=w.decompose(np.zeros(128),'haar')
    assert constant['threshold']==0 and np.all(np.isfinite(constant['denoised']))


def test_signal_preparation_no_silent_dropping():
    t=np.arange(64,dtype=float);x=2*t+3;x[10]=np.nan
    with pytest.raises(ValueError,match='missing'):w.prepare(x,t)
    p=w.prepare(x,t,missing='interpolate',detrend='linear')
    assert p['missing_count']==1 and len(p['time'])==64
    np.testing.assert_allclose(p['observed'],2*t+3)
    np.testing.assert_allclose(p['prepared'],0,atol=1e-12)
    x[0]=np.nan
    with pytest.raises(ValueError,match='endpoints'):w.prepare(x,t,missing='interpolate')
    t[20]+=.1
    with pytest.raises(ValueError,match='uniformly'):w.prepare(np.arange(64),t)
    p=w.prepare(2*t+3,t,resample=True,detrend='none')
    assert p['resampled'];np.testing.assert_allclose(p['observed'],2*p['time']+3)


def test_trend_restored_in_studio_outputs():
    t=np.arange(256)/128;x=100+2*t+np.sin(2*np.pi*6*t)
    r=w.analyze(x,t,{'strength':0,'detrend':'linear','max_scale':32})
    np.testing.assert_allclose(r['dwt']['denoised'],x,atol=1e-10)
    np.testing.assert_allclose(r['dwt']['reconstruction'],x,atol=1e-10)
    np.testing.assert_allclose(np.sum([b['values'] for b in r['dwt']['bands']],axis=0)+r['baseline'],x,atol=1e-10)


@pytest.mark.parametrize('options',[{'dt':0},{'level':10},{'cwt_wavelet':'unknown'},{'dwt_wavelet':'unknown'},{'scale_count':10000},{'max_scale':10000},{'max_scale':3},{'strength':-1},{'boundary':'other'},{'resample':'yes'}])
def test_validation(options):
    with pytest.raises(ValueError):w.analyze(np.arange(64),options=options)


def test_api_real_dataset_and_invalid_sources():
    client=app.test_client();t=np.arange(128)/32;x=np.sin(2*np.pi*3*t)
    dataset={'id':'recording','name':'sensor','columns':[{'name':'time','values':t.tolist()},{'name':'value','values':x.tolist()}],'x':'time','y':['value'],'style':'lines','visible':True}
    payload={'signal':'sensor_value','time':'sensor_time','datasets':[dataset],'options':{'dwt_wavelet':'haar','strength':0,'max_scale':16}}
    r=client.post('/api/wavelets',json=payload)
    assert r.status_code==200,r.json
    np.testing.assert_allclose(r.json['analysis']['observed'],x)
    assert r.json['analysis']['dt']==pytest.approx(1/32)
    for source in [[1,2,3],'unknown',"__import__('os')",[[1,2]]*8]:
        assert client.post('/api/wavelets',json={'signal':source}).status_code==400
    bad=dict(payload);bad['time']='sensor_time*0'
    assert client.post('/api/wavelets',json=bad).status_code==400


def test_worksheet_wavelet_outputs_remain_observation_sequences():
    x=np.sin(np.arange(128)/8)
    dataset={'id':'d','name':'sensor','columns':[{'name':'value','values':x.tolist()}],'x':None,'y':['value'],'style':'lines','visible':True}
    rows=[{'text':s} for s in ['A=wavelet_approx(sensor_value,2)','D=wavelet_detail(sensor_value,2)','wavelet_denoise(sensor_value,0)','wavelet_cwt(sensor_value,8)','f(t)=mexican_hat(t,2,0)','g(a,t)=real(morlet(t,a))']]
    r=Calculator(rows,[dataset]).run([1,3,-2,2])
    assert not any(v.get('error') for v in r),r
    assert [v['kind'] for v in r[:4]]==['series']*4
    np.testing.assert_allclose(r[2]['real'],x,atol=1e-12)
    assert r[4]['kind']=='curve' and r[5]['kind']=='surface'


def test_display_power_binning_keeps_all_samples():
    x=np.sin(np.arange(1001)/9)
    r=w.continuous(x,min_scale=4,max_scale=32,count=8)
    assert r['display_bins']==800
    starts=np.unique(np.linspace(0,len(x),801,dtype=int));sizes=np.diff(starts)
    np.testing.assert_allclose(np.average(r['power'],axis=1,weights=sizes),r['global_power'])
