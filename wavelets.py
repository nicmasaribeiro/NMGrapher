"""Wavelet functions and bounded analysis of uniformly sampled real signals."""
import numpy as np
import pywt
from scipy import signal as scipy_signal
from datasets import DataColumn

CWT_WAVELETS = {'cmor1.5-1.0', 'morl', 'mexh', 'gaus1'}
DWT_WAVELETS = {'haar', 'db2', 'db4', 'sym4', 'coif1'}
MAX_SAMPLES = 10000


def number(value, label, lo=-1e100, hi=1e100):
    a = np.asarray(value)
    if a.ndim or np.iscomplexobj(a) and a.imag != 0 or not np.isfinite(a):
        raise ValueError(f'{label} must be a finite real number.')
    v = float(a.real)
    if not lo <= v <= hi: raise ValueError(f'{label} must be between {lo:g} and {hi:g}.')
    return v


def integer(value, label, lo, hi):
    v = number(value, label, lo, hi)
    if not v.is_integer(): raise ValueError(f'{label} must be an integer.')
    return int(v)


def vector(values, label='Signal', missing=False):
    a = np.asarray(values)
    if a.ndim != 1 or not 8 <= len(a) <= MAX_SAMPLES:
        raise ValueError(f'{label} needs 8–10,000 samples in a vector or dataset column.')
    if np.iscomplexobj(a) and np.any(a.imag != 0): raise ValueError(f'{label} must be real; use real(...), imag(...), or abs(...).')
    a = np.asarray(a.real, dtype=float)
    if np.any(np.isinf(a)) or np.any(np.abs(a[np.isfinite(a)]) > 1e100): raise ValueError(f'{label} values must be finite within ±1e100.')
    if not missing and not np.all(np.isfinite(a)): raise ValueError(f'{label} has missing values. Fill them explicitly or enable interpolation in Wavelet studio.')
    return a.copy()


def prepare(values, times=None, dt=1, missing='reject', resample=False, detrend='mean'):
    if missing not in ('reject', 'interpolate') or detrend not in ('none', 'mean', 'linear') or type(resample) is not bool:
        raise ValueError('Choose supported missing-data, sampling, and detrending options.')
    raw = vector(values, missing=True); n = len(raw)
    dt = number(dt, 'Sample spacing', 1e-12, 1e12)
    if times is None: t = np.arange(n, dtype=float)*dt
    else:
        t = vector(times, 'Time')
        if len(t) != n: raise ValueError('Time and signal columns must have the same length.')
        if np.any(np.diff(t) <= 0): raise ValueError('Time must be strictly increasing, without duplicates. Sort paired observations before importing.')
        dt = float((t[-1]-t[0])/(n-1))
        number(dt, 'Inferred sample spacing', 1e-12, 1e12)
    irregular = not np.allclose(np.diff(t), dt, rtol=1e-5, atol=dt*1e-7+2*abs(np.spacing(np.max(np.abs(t)))))
    if irregular and not resample: raise ValueError('Time is not uniformly spaced. Enable linear resampling or supply a regularly sampled signal.')
    bad = ~np.isfinite(raw)
    if np.any(bad):
        if missing != 'interpolate': raise ValueError('Signal has missing samples. Enable interpolation to fill interior gaps without dropping time positions.')
        if bad[0] or bad[-1]: raise ValueError('Cannot interpolate missing endpoints. Choose a segment with observed first and last samples.')
        if np.count_nonzero(~bad) < 2: raise ValueError('At least two observed samples are needed for interpolation.')
    uniform_t = np.linspace(t[0],t[-1],n) if irregular else t.copy()
    observed = np.interp(uniform_t,t[~bad],raw[~bad]) if irregular or np.any(bad) else raw.copy()
    baseline = np.zeros(n)
    if detrend == 'mean': baseline[:] = np.mean(observed)
    elif detrend == 'linear': baseline = observed - scipy_signal.detrend(observed, type='linear')
    prepared = observed-baseline
    return {'time':uniform_t, 'observed':observed, 'prepared':prepared, 'baseline':baseline,
            'raw_time':t, 'raw':raw, 'dt':dt, 'missing_count':int(np.count_nonzero(bad)),
            'resampled':bool(irregular), 'detrend':detrend}


def decompose(values, wavelet='db4', level=None, mode='symmetric', strength=1, threshold_mode='soft', dt=1):
    x = vector(values)
    if wavelet not in DWT_WAVELETS: raise ValueError('Choose Haar, db2, db4, sym4, or coif1.')
    if mode not in ('symmetric','periodization'): raise ValueError('Choose symmetric or periodization boundary extension.')
    if threshold_mode not in ('soft','hard'): raise ValueError('Choose soft or hard thresholding.')
    strength = number(strength, 'Threshold multiplier', 0, 10)
    dt = number(dt, 'Sample spacing', 1e-12, 1e12)
    maximum = min(10,pywt.dwt_max_level(len(x),pywt.Wavelet(wavelet).dec_len))
    if maximum < 1: raise ValueError('This signal is too short for the selected wavelet. Use Haar or a longer signal.')
    level = min(5,maximum) if level is None else integer(level,'Decomposition level',1,maximum)
    coeffs = pywt.wavedec(x,wavelet,mode=mode,level=level)
    sigma = float(np.median(np.abs(coeffs[-1]-np.median(coeffs[-1])))/0.6744897501960817)
    threshold = float(strength*sigma*np.sqrt(2*np.log(len(x))))
    filtered = [coeffs[0].copy()] + [pywt.threshold(c,threshold,mode=threshold_mode) if threshold>0 else c.copy() for c in coeffs[1:]]
    reconstruction = pywt.waverec(coeffs,wavelet,mode=mode)[:len(x)]
    denoised = pywt.waverec(filtered,wavelet,mode=mode)[:len(x)]
    bands = []
    for i,c in enumerate(coeffs):
        isolated = [np.zeros_like(v) for v in coeffs]; isolated[i] = c
        series = pywt.waverec(isolated,wavelet,mode=mode)[:len(x)]
        j = level if i == 0 else level-i+1
        band_range = [0,1/(dt*2**(level+1))] if i == 0 else [1/(dt*2**(j+1)),1/(dt*2**j)]
        bands.append({'name':('A' if i==0 else 'D')+str(j),'level':j,'coefficients':c.tolist(),
                      'values':series.tolist(),'coefficient_energy':float(np.sum(c*c)), 'frequency_band':band_range})
    energies = np.array([b['coefficient_energy'] for b in bands]); total = float(energies.sum())
    for b in bands: b['coefficient_share'] = b['coefficient_energy']/total if total else 0
    return {'wavelet':wavelet,'mode':mode,'level':level,'max_level':maximum,'bands':bands,
            'reconstruction':reconstruction,'denoised':denoised,'sigma_estimate':sigma,'threshold':threshold,
            'threshold_mode':threshold_mode,'reconstruction_rmse':float(np.sqrt(np.mean((x-reconstruction)**2))),
            'residual_rms':float(np.sqrt(np.mean((x-denoised)**2)))}


def continuous(values, dt=1, wavelet='cmor1.5-1.0', min_scale=4, max_scale=None, count=48, time=None):
    x = vector(values); n = len(x);dt = number(dt,'Sample spacing',1e-12,1e12)
    if wavelet not in CWT_WAVELETS: raise ValueError('Choose complex Morlet, real Morlet, Mexican hat, or Gaussian derivative.')
    count = integer(count,'Scale count',8,96)
    lo = number(min_scale,'Minimum scale',2,1024)
    hi = min(128,n/4) if max_scale is None else number(max_scale,'Maximum scale',2,1024)
    if not lo < hi or hi > n/2: raise ValueError('Maximum scale must exceed minimum scale and be at most half the sample count.')
    scales = np.geomspace(lo,hi,count)
    frequency = pywt.scale2frequency(wavelet,scales)/dt
    if np.any(frequency > .5/dt*(1+1e-12)): raise ValueError('Scales exceed the Nyquist frequency. Increase the minimum scale.')
    coefs,frequency = pywt.cwt(x,scales,wavelet,sampling_period=dt,method='fft')
    power = np.abs(coefs)**2
    if not np.all(np.isfinite(power)): raise ValueError('Wavelet coefficients overflowed. Rescale the signal.')
    t = np.arange(n)*dt if time is None else np.asarray(time)
    # Only the display is compressed: average full-resolution power into time bins.
    starts = np.unique(np.linspace(0,n,min(n,800)+1,dtype=int))
    sizes = np.diff(starts)
    display_power = np.add.reduceat(power,starts[:-1],axis=1)/sizes
    display_time = np.add.reduceat(t,starts[:-1])/sizes
    w = pywt.ContinuousWavelet(wavelet)
    edge = np.maximum(abs(w.lower_bound),abs(w.upper_bound))*scales*dt
    global_power = power.mean(axis=1)
    interior = [float(np.mean(row[(t-t[0]>=width)&(t[-1]-t>=width)])) if np.any((t-t[0]>=width)&(t[-1]-t>=width)) else None for row,width in zip(power,edge)]
    return {'wavelet':wavelet,'scales':scales.tolist(),'frequency':frequency.tolist(), 'period':(1/frequency).tolist(),
            'time':display_time.tolist(),'power':display_power.tolist(),'global_power':global_power.tolist(),
            'interior_power':interior,'edge_width':edge.tolist(),'display_bins':len(display_time),
            'dominant_frequency':float(frequency[np.argmax(global_power)]) if np.max(global_power)>0 else None}


def analyze(values, times=None, options=None):
    options = {} if options is None else options
    if not isinstance(options,dict): raise ValueError('Wavelet options must be an object.')
    p = prepare(values,times,options.get('dt',1),options.get('missing','reject'),options.get('resample',False),options.get('detrend','mean'))
    d = decompose(p['prepared'],options.get('dwt_wavelet','db4'),options.get('level'),options.get('boundary','symmetric'),options.get('strength',1),options.get('threshold_mode','soft'),p['dt'])
    c = continuous(p['prepared'],p['dt'],options.get('cwt_wavelet','cmor1.5-1.0'),options.get('min_scale',4),options.get('max_scale'),options.get('scale_count',48),p['time'])
    # Return reconstruction/denoising in the input signal's units, restoring removed trend.
    d['reconstruction'] = (d['reconstruction']+p['baseline']).tolist()
    d['denoised'] = (d['denoised']+p['baseline']).tolist()
    clean = lambda a:np.where(np.isfinite(a),a,None).tolist()
    out = {k:clean(v) if isinstance(v,np.ndarray) else v for k,v in p.items()}
    out.update(cwt=c,dwt=d,n=len(p['time']),sample_rate=1/p['dt'],nyquist=.5/p['dt'])
    return out


# Worksheet functions use numeric wavelet IDs to keep the expression interpreter string-free.
DWT_IDS = {0:'haar',1:'db2',2:'db4',3:'sym4',4:'coif1'}
CWT_IDS = {0:'cmor1.5-1.0',1:'morl',2:'mexh',3:'gaus1'}


def mexican_hat(t, scale=1, shift=0):
    scale = number(scale,'Scale',1e-12,1e12);shift = number(shift,'Shift')
    u=(np.asarray(t)-shift)/scale
    return 2/(np.sqrt(3)*np.pi**.25)*(1-u*u)*np.exp(-u*u/2)/np.sqrt(scale)


def morlet(t, scale=1, shift=0, omega=6):
    scale = number(scale,'Scale',1e-12,1e12);shift = number(shift,'Shift');omega=number(omega,'Angular frequency',1,30)
    u=(np.asarray(t)-shift)/scale
    normalization=np.sqrt(1+np.exp(-omega**2)-2*np.exp(-3*omega**2/4))
    return np.pi**(-.25)*(np.exp(1j*omega*u)-np.exp(-omega**2/2))*np.exp(-u*u/2)/(np.sqrt(scale)*normalization)


def haar(t, scale=1, shift=0):
    scale=number(scale,'Scale',1e-12,1e12);shift=number(shift,'Shift');u=(np.asarray(t)-shift)/scale
    if np.iscomplexobj(u) and np.any(u.imag!=0): raise ValueError('Haar wavelet inputs must be real.')
    u=u.real
    return np.where((u>=0)&(u<.5),1,np.where((u>=.5)&(u<1),-1,0))/np.sqrt(scale)


def dwt_part(values, level=1, wavelet_id=0, detail=False):
    wavelet=DWT_IDS[integer(wavelet_id,'Wavelet ID',0,4)]
    report=decompose(values,wavelet,integer(level,'Level',1,10),strength=0)
    return np.asarray(report['bands'][1 if detail else 0]['values']).view(DataColumn)


def denoise(values, strength=1, wavelet_id=2, level=0):
    level=integer(level,'Level',0,10)
    report=decompose(values,DWT_IDS[integer(wavelet_id,'Wavelet ID',0,4)],level or None,strength=strength)
    return np.asarray(report['denoised']).view(DataColumn)


def cwt_at(values,scale,wavelet_id=0):
    x=vector(values);scale=number(scale,'Scale',2,min(1024,len(x)/2))
    w=CWT_IDS[integer(wavelet_id,'Wavelet ID',0,3)]
    if pywt.scale2frequency(w,scale)>.5: raise ValueError('Scale exceeds Nyquist; increase it.')
    coefs,_=pywt.cwt(x,[scale],w,method='fft')
    return np.asarray(coefs[0]).view(DataColumn)


FUNCTIONS={'mexican_hat':mexican_hat,'morlet':morlet,'haar':haar,
           'wavelet_approx':lambda values,level=1,wavelet_id=0:dwt_part(values,level,wavelet_id),
           'wavelet_detail':lambda values,level=1,wavelet_id=0:dwt_part(values,level,wavelet_id,True),
           'wavelet_denoise':denoise,'wavelet_cwt':cwt_at}


from dataclasses import dataclass

@dataclass(frozen=True)
class DiscreteTransform:
    coefficients: tuple
    wavelet: str
    length: int
    level: int
    mode: str='symmetric'

@dataclass(frozen=True)
class ContinuousTransform:
    coefficients: np.ndarray
    wavelet: str
    scales: np.ndarray
    frequencies: np.ndarray
    dt: float


def dwt(values,level=0,wavelet_id=2):
    x=vector(values);wavelet=DWT_IDS[integer(wavelet_id,'Wavelet ID',0,4)]
    maximum=min(10,pywt.dwt_max_level(len(x),pywt.Wavelet(wavelet).dec_len))
    if maximum<1:raise ValueError('Signal is too short for this wavelet. Use Haar or more observations.')
    requested=integer(level,'Level',0,maximum);level=requested or min(5,maximum)
    coefficients=tuple(pywt.wavedec(x,wavelet,mode='symmetric',level=level))
    return DiscreteTransform(coefficients,wavelet,len(x),level)


def idwt(transform):
    if not isinstance(transform,DiscreteTransform):raise ValueError('idwt needs a discrete transform from dwt(signal). CWT inversion is not implemented.')
    return np.asarray(pywt.waverec(transform.coefficients,transform.wavelet,mode=transform.mode)[:transform.length]).view(DataColumn)


def cwt(values,scales,wavelet_id=0,dt=1):
    x=vector(values);w=CWT_IDS[integer(wavelet_id,'Wavelet ID',0,3)];dt=number(dt,'Sample spacing',1e-12,1e12)
    a=np.asarray(scales)
    if a.ndim==0:return cwt_at(values,scales,wavelet_id)
    if a.ndim!=1 or not 1<=len(a)<=96 or np.iscomplexobj(a) and np.any(a.imag!=0) or not np.all(np.isfinite(a)):
        raise ValueError('Supply a scalar scale or a real list of 1–96 scales.')
    a=np.asarray(a.real,dtype=float)
    if np.any(a<2) or np.any(a>min(1024,len(x)/2)):raise ValueError('Scales must be between 2 and min(1024, sample count / 2).')
    if np.any(pywt.scale2frequency(w,a)>.5):raise ValueError('Scales exceed Nyquist. Increase the minimum scale.')
    coeff,freq=pywt.cwt(x,a,w,sampling_period=dt,method='fft')
    return ContinuousTransform(coeff,w,a,freq,dt)


def transform_coefficients(transform,index=0):
    if not isinstance(transform,(DiscreteTransform,ContinuousTransform)):raise ValueError('Use a transform from dwt or multiscale cwt.')
    index=integer(index,'Coefficient index',0,len(transform.coefficients)-1)
    return np.asarray(transform.coefficients[index]).copy().view(DataColumn)


def transform_band(transform,index=0):
    if not isinstance(transform,DiscreteTransform):raise ValueError('wavelet_band needs a DWT result; use wavelet_coeffs for a CWT scale.')
    index=integer(index,'Band index',0,len(transform.coefficients)-1)
    coefficients=[np.zeros_like(c) for c in transform.coefficients];coefficients[index]=transform.coefficients[index]
    return np.asarray(pywt.waverec(coefficients,transform.wavelet,mode=transform.mode)[:transform.length]).view(DataColumn)


def transform_axis(transform,frequency=False):
    if not isinstance(transform,ContinuousTransform):raise ValueError('Use a multiscale CWT result for scales/frequencies.')
    return (transform.frequencies if frequency else transform.scales).copy().view(DataColumn)


def transform_summary(transform):
    if isinstance(transform,DiscreteTransform):
        names=['A'+str(transform.level)]+['D'+str(j) for j in range(transform.level,0,-1)]
        return {'type':'dwt','wavelet':transform.wavelet,'length':transform.length,'level':transform.level,'labels':names,'sizes':[len(c) for c in transform.coefficients]}
    return {'type':'cwt','wavelet':transform.wavelet,'length':transform.coefficients.shape[1],'labels':['scale '+str(s) for s in transform.scales], 'scales':transform.scales.tolist(),'frequencies':transform.frequencies.tolist(),'dt':transform.dt}

FUNCTIONS.update({'dwt':dwt,'wavelet_transform':dwt,'idwt':idwt,'wavelet_reconstruct':idwt,'cwt':cwt,
                  'wavelet_coeffs':transform_coefficients,'wavelet_band':transform_band,
                  'wavelet_power':lambda t,index=0:np.abs(transform_coefficients(t,index))**2,
                  'wavelet_scales':transform_axis,'wavelet_frequencies':lambda t:transform_axis(t,True)})
