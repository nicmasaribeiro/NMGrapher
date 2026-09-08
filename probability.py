"""Named numerical probability distributions, including finite Boltzmann states."""
from dataclasses import dataclass
from functools import lru_cache
import numpy as np
from scipy import stats
from datasets import DataColumn


def real(value, label='Value'):
    a=np.asarray(value)
    if a.ndim or not np.isfinite(a) or np.iscomplexobj(a) and a.imag != 0: raise ValueError(f'{label} must be a finite real scalar.')
    return float(a.real)


def positive(value,label):
    v=real(value,label)
    if not 1e-12 <= v <= 1e12: raise ValueError(f'{label} must be between 1e-12 and 1e12.')
    return v


def integer(value,label,lo,hi):
    v=real(value,label)
    if not v.is_integer() or not lo<=v<=hi: raise ValueError(f'{label} must be an integer from {lo} to {hi}.')
    return int(v)


@dataclass(frozen=True)
class Distribution:
    family: str
    parameters: tuple
    rv: object
    discrete: bool=False
    energies: tuple=()
    weights: tuple=()


@lru_cache(maxsize=128)
def make(family, args):
    if family=='normal':
        mu,sigma=args;mu=real(mu,'Mean');sigma=positive(sigma,'Standard deviation')
        return Distribution(family,(mu,sigma),stats.norm(loc=mu,scale=sigma))
    if family=='poisson':
        rate=real(args[0],'Rate')
        if not 0<=rate<=1e6: raise ValueError('Poisson rate must be between 0 and 1,000,000.')
        return Distribution(family,(rate,),stats.poisson(mu=rate),True)
    if family=='binomial':
        n=integer(args[0],'Trials',0,1000000);p=real(args[1],'Success probability')
        if not 0<=p<=1: raise ValueError('Success probability must be between 0 and 1.')
        return Distribution(family,(n,p),stats.binom(n=n,p=p),True)
    if family=='uniform':
        lo,hi=[real(v,'Bound') for v in args]
        if not 1e-12<=hi-lo<=1e12: raise ValueError('Uniform upper bound must exceed its lower bound by 1e-12–1e12.')
        return Distribution(family,(lo,hi),stats.uniform(loc=lo,scale=hi-lo))
    if family=='exponential':
        rate=positive(args[0],'Rate');return Distribution(family,(rate,),stats.expon(scale=1/rate))
    if family=='geometric':
        p=real(args[0],'Success probability')
        if not 0<p<=1: raise ValueError('Success probability must be greater than 0 and at most 1.')
        return Distribution(family,(p,),stats.geom(p=p),True)
    if family=='boltzmann':
        energies,temp=args;temp=positive(temp,'Temperature')
        energies=np.asarray(energies,dtype=float)
        if energies.ndim!=1 or not 1<=len(energies)<=32 or not np.all(np.isfinite(energies)) or np.any(abs(energies)>1e100): raise ValueError('Use a finite vector of 1–32 energy levels within ±1e100.')
        # Subtract the minimum energy before exponentiating; k_B = 1.
        scores=-(energies-energies.min())/temp;weights=np.exp(scores);weights/=weights.sum()
        rv=stats.rv_discrete(values=(np.arange(len(weights)),weights))
        return Distribution(family,(tuple(energies),temp),rv,True,tuple(energies),tuple(weights))
    raise ValueError('Unsupported distribution family.')


def scalar_constructor(family,*args):
    return make(family,tuple(real(v,'Distribution parameter') for v in args))


def boltzmann(energies,temperature=1):
    a=np.asarray(energies)
    if a.ndim!=1 or not 1<=a.size<=32 or not np.all(np.isfinite(a)) or np.any(np.imag(a)!=0): raise ValueError('Use a finite real vector of 1–32 energy levels.')
    return make('boltzmann',(tuple(float(v) for v in a.real),real(temperature,'Temperature')))


def distribution(d):
    if not isinstance(d,Distribution): raise ValueError('Use a named distribution, such as D = normal(0,1).')
    return d


def coordinates(value):
    a=np.asarray(value)
    if np.iscomplexobj(a) and np.any(np.imag(a)!=0): raise ValueError('Probability coordinates must be real.')
    return np.asarray(a.real,dtype=float)


def density(d,x):
    d=distribution(d)
    if d.discrete: raise ValueError('Use pmf(D,k) for a discrete distribution.')
    return d.rv.pdf(coordinates(x))


def mass(d,x):
    d=distribution(d)
    if not d.discrete: raise ValueError('Use pdf(D,x) for a continuous distribution.')
    return d.rv.pmf(coordinates(x))


def cumulative(d,x):return distribution(d).rv.cdf(coordinates(x))
def survival(d,x):return distribution(d).rv.sf(coordinates(x))
def quantile(d,q):
    q=coordinates(q)
    if not np.all(np.isfinite(q)) or np.any((q<0)|(q>1)): raise ValueError('Quantile probabilities must be between 0 and 1.')
    return distribution(d).rv.ppf(q)


def interval(d,lower,upper):
    d=distribution(d);lo=coordinates(lower);hi=coordinates(upper)
    if np.any(np.isnan(lo)) or np.any(np.isnan(hi)) or np.any(lo>hi): raise ValueError('Interval lower bounds must not exceed upper bounds.')
    # Both endpoints are included for integer-valued distributions.
    left=np.ceil(lo)-1 if d.discrete else lo
    right=np.floor(hi) if d.discrete else hi
    cdf_diff=d.rv.cdf(right)-d.rv.cdf(left)
    sf_diff=d.rv.sf(left)-d.rv.sf(right)
    result=np.where(d.rv.cdf(left)>.5,sf_diff,cdf_diff)
    return np.clip(result,0,1)


def draw(d,count,seed=0):
    d=distribution(d);n=integer(count,'Sample count',1,10000);seed=integer(seed,'Seed',0,2**32-1)
    return np.asarray(d.rv.rvs(size=n,random_state=np.random.default_rng(seed)),dtype=float).view(DataColumn)


def energy(d):
    d=distribution(d)
    if d.family!='boltzmann': raise ValueError('expected_energy needs a Boltzmann distribution.')
    return float(np.dot(d.energies,d.weights))


FUNCTIONS={
    'normal':lambda mu=0,sigma=1:scalar_constructor('normal',mu,sigma),
    'poisson':lambda rate:scalar_constructor('poisson',rate),
    'binomial':lambda n,p:scalar_constructor('binomial',n,p),
    'uniform':lambda lo=0,hi=1:scalar_constructor('uniform',lo,hi),
    'exponential':lambda rate=1:scalar_constructor('exponential',rate),
    'geometric':lambda p:scalar_constructor('geometric',p),
    'boltzmann':boltzmann,'pdf':density,'pmf':mass,'cdf':cumulative,'sf':survival,
    'quantile':quantile,'prob':interval,'sample':draw,'expected_energy':energy,
}


def install(functions):
    functions.update(FUNCTIONS)
    for name,method in [('mean','mean'),('variance','var'),('std','std'),('median','median'),('entropy','entropy')]:
        original=functions[name]
        functions[name]=lambda value,original=original,method=method: getattr(value.rv,method)() if isinstance(value,Distribution) else original(value)
    original=functions['probabilities']
    def probabilities(value):
        if isinstance(value,Distribution):
            if value.family!='boltzmann': raise ValueError('probabilities(D) returns finite Boltzmann state weights. Use pmf(D,k) for other discrete distributions.')
            return np.asarray(value.weights)
        return original(value)
    functions['probabilities']=probabilities


def describe(d):
    d=distribution(d)
    finite=lambda x:float(x) if np.isfinite(x) else None
    info={'family':d.family,'parameters':list(d.parameters),'discrete':d.discrete,
          'mean':finite(d.rv.mean()),'variance':finite(d.rv.var()),'std':finite(d.rv.std()),'entropy':finite(d.rv.entropy())}
    if d.family=='boltzmann':info.update(energies=list(d.energies),probabilities=list(d.weights),expected_energy=energy(d))
    return info


def plot(d,lo=None,hi=None):
    d=distribution(d)
    if lo is None:
        lo,hi=[float(v) for v in d.rv.ppf([.001,.999])]
        if not np.isfinite(lo) or not np.isfinite(hi): raise ValueError('Choose a finite plotting range.')
        if lo==hi:lo-=1;hi+=1
    else:
        lo=real(lo,'Minimum');hi=real(hi,'Maximum')
    if not lo<hi or max(abs(lo),abs(hi))>1e100: raise ValueError('Choose increasing finite plot bounds within ±1e100.')
    if d.discrete:
        start,end=int(np.ceil(lo)),int(np.floor(hi))
        if end-start+1>2000: raise ValueError('Choose a range containing at most 2,000 integer outcomes.')
        if end<start:raise ValueError('Choose a range containing an integer outcome.')
        x=np.arange(start,end+1,dtype=float);y=d.rv.pmf(x)
    else:x=np.linspace(lo,hi,500);y=d.rv.pdf(x)
    clean=lambda a:[float(v) if np.isfinite(v) else None for v in a]
    return {'x':clean(x),'y':clean(y),'cdf':clean(d.rv.cdf(x)), 'range':[lo,hi]}
