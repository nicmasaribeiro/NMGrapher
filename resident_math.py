"""Descriptive statistics and elementary functions for the resident palette."""
import numpy as np
from scipy.stats import rankdata
from probability import Distribution, quantile as distribution_quantile
from array_types import VectorValue


def data(values,minimum=1):
    a=np.asarray(values)
    if a.ndim!=1 or not minimum<=a.size<=10000:raise ValueError(f'Use a list or dataset column containing {minimum}–10,000 observations.')
    if np.iscomplexobj(a) and np.any(a.imag!=0):raise ValueError('This statistic needs real observations; use real(...), imag(...), or abs(...).')
    return np.asarray(a.real,dtype=float)


def quantile(values,q):
    if isinstance(values,Distribution):return distribution_quantile(values,q)
    a=data(values);q=np.asarray(q)
    if np.iscomplexobj(q) and np.any(q.imag!=0) or not np.all(np.isfinite(q)) or np.any(q<0) or np.any(q>1):raise ValueError('Quantile probabilities must be between 0 and 1.')
    return np.quantile(a,q.real,method='linear')


def quartile(values,q):
    q=np.asarray(q)
    if np.iscomplexobj(q) and np.any(q.imag!=0) or not np.all(np.isfinite(q)) or np.any(q<0) or np.any(q>4):raise ValueError('Quartile positions must be between 0 and 4.')
    return quantile(values,q.real/4)


def variance(values,ddof):
    if isinstance(values,Distribution):return values.rv.var()
    a=data(values,ddof+1);return np.var(a,ddof=ddof)


def covariance(x,y,ddof):
    a=data(x,ddof+1);b=data(y,ddof+1)
    if a.shape!=b.shape:raise ValueError('Paired statistics require equal-length observation lists.')
    return np.sum((a-a.mean())*(b-b.mean()))/(len(a)-ddof)


def correlation(x,y,rank=False):
    a=data(x,2);b=data(y,2)
    if a.shape!=b.shape:raise ValueError('Paired statistics require equal-length observation lists.')
    if not np.all(np.isfinite(a)) or not np.all(np.isfinite(b)):return float('nan')
    if rank:a=rankdata(a,method='average');b=rankdata(b,method='average')
    a=a-a.mean();b=b-b.mean();scalea=np.max(abs(a));scaleb=np.max(abs(b))
    if scalea==0 or scaleb==0:raise ValueError('Correlation is undefined for a constant observation list.')
    a=a/scalea;b=b/scaleb
    return float(np.clip(np.dot(a,b)/np.sqrt(np.dot(a,a)*np.dot(b,b)),-1,1))


def extreme(*args,maximum=False):
    if len(args)==1:return (np.max if maximum else np.min)(data(args[0]))
    if len(args)<2:raise ValueError('Supply a list or at least two values.')
    result=args[0]
    for value in args[1:]:result=(np.maximum if maximum else np.minimum)(result,value)
    return result


def logbase(value,base):
    b=np.asarray(base)
    if np.iscomplexobj(b) and np.any(b.imag!=0) or not np.all(np.isfinite(b)) or np.any(b<=0) or np.any(b==1):raise ValueError('Logarithm bases must be real, positive, and different from 1.')
    return np.emath.log(value)/np.log(b.real)


def logarithm(value,base=None):return np.emath.log(value) if base is None else logbase(value,base)


FUNCTIONS={
 'tanh':np.tanh,'csch':lambda x:1/np.sinh(x),'sech':lambda x:1/np.cosh(x),'coth':lambda x:1/np.tanh(x),
 'min':lambda *args:extreme(*args),'max':lambda *args:extreme(*args,maximum=True),
 'quartile':quartile,'quantile':quantile,'stdev':lambda a:np.sqrt(variance(a,1)),
 'stdevp':lambda a:np.sqrt(variance(a,0)),'var':lambda a:variance(a,1),'varp':lambda a:variance(a,0),
 'cov':lambda a,b:covariance(a,b,1),'covp':lambda a,b:covariance(a,b,0),'mad':lambda a:np.mean(abs(data(a)-np.mean(data(a)))),
 'corr':correlation,'spearman':lambda a,b:correlation(a,b,True),
 'stats':lambda a:np.asarray(quantile(a,[0,.25,.5,.75,1])).view(VectorValue),
 'total':lambda a:np.sum(a),'product':lambda a:np.prod(a),'prod':lambda a:np.prod(a),'summation':lambda a:np.sum(a),
 'log':logarithm,'logbase':logbase,
}
