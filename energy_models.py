"""Small binary Boltzmann machines and Bernoulli RBMs. No external ML runtime."""
from dataclasses import dataclass
from functools import lru_cache
import numpy as np
from scipy.special import expit, logsumexp


class EnergyError(ValueError):pass


def scalar(x,label,lo,hi,integer=False):
    if isinstance(x,(bool,np.bool_)) or not isinstance(x,(int,float,np.integer,np.floating)) or not np.isfinite(x) or not lo<=x<=hi or integer and int(x)!=x:
        raise EnergyError(f'{label} must be {"an integer " if integer else ""}between {lo} and {hi}.')
    return int(x) if integer else float(x)


def real_array(x,label):
    if np.iscomplexobj(x):raise EnergyError(label+' must be real.')
    try:a=np.asarray(x,dtype=float)
    except (ValueError,TypeError):raise EnergyError(label+' must be a rectangular numeric array.')
    if not np.all(np.isfinite(a)):raise EnergyError(label+' must be finite.')
    return a


@dataclass(frozen=True,eq=False)
class EnergyModel:
    kind:str
    W:np.ndarray
    a:np.ndarray
    b:np.ndarray
    temperature:float=1.

    @property
    def visible(self):return len(self.a)
    @property
    def hidden(self):return len(self.b)


@lru_cache(maxsize=64)
def _make(kind,weights,a,b,temperature):
    arrays=[np.asarray(x,dtype=float) for x in (weights,a,b)]
    for x in arrays:x.setflags(write=False)
    return EnergyModel(kind,*arrays,temperature)


def make(kind,W,a,b=(),temperature=1):
    if kind not in ('rbm','bm'):raise EnergyError('Choose rbm or bm.')
    W=real_array(W,'Weights');a=real_array(a,'Visible biases');b=real_array(b,'Hidden biases')
    if a.ndim!=1 or not 1<=a.size<=(16 if kind=='rbm' else 12):raise EnergyError('Use 1–16 visible units for an RBM or 1–12 for a fully visible Boltzmann machine.')
    if kind=='rbm':
        if b.ndim!=1 or not 1<=b.size<=16 or W.shape!=(a.size,b.size):raise EnergyError('RBM weights must have visible × hidden shape, with 1–16 hidden units and matching biases.')
    elif W.shape!=(a.size,a.size) or b.size or not np.allclose(W,W.T,atol=1e-12,rtol=0) or not np.allclose(np.diag(W),0,atol=1e-12,rtol=0):
        raise EnergyError('Fully visible BM weights must be square, symmetric, and have zero diagonal; no hidden bias is used.')
    if any(np.any(np.abs(x)>100) for x in (W,a,b)):raise EnergyError('Weights and biases must be within ±100.')
    if kind=='bm':W=(W+W.T)/2;np.fill_diagonal(W,0)
    T=scalar(temperature,'Temperature',.05,20)
    return _make(kind,tuple(map(tuple,W)),tuple(a),tuple(b),T)


def rbm(W,a,b,temperature=1):return make('rbm',W,a,b,temperature)
def boltzmann_machine(W,a,temperature=1):return make('bm',W,a,(),temperature)

def model(m):
    if not isinstance(m,EnergyModel):raise EnergyError('Use an energy model, for example M=rbm(W,a,b).')
    return m


def pack(m):
    m=model(m)
    return dict(kind=m.kind,weights=m.W.tolist(),visible_bias=m.a.tolist(),hidden_bias=m.b.tolist(),temperature=m.temperature)


def unpack(value):
    if not isinstance(value,dict):raise EnergyError('Supply an energy model object.')
    return make(value.get('kind'),value.get('weights'),value.get('visible_bias'),value.get('hidden_bias',[]),value.get('temperature',1))


def initialize(kind='rbm',visible=4,hidden=2,seed=42,temperature=1):
    nv=scalar(visible,'Visible units',1,16 if kind=='rbm' else 12,True)
    nh=scalar(hidden,'Hidden units',1,16,True) if kind=='rbm' else 0
    rng=np.random.default_rng(scalar(seed,'Seed',0,2**32-1,True))
    W=rng.normal(0,.05,(nv,nh if kind=='rbm' else nv))
    if kind=='bm':W=(W+W.T)/2;np.fill_diagonal(W,0)
    return make(kind,W,np.zeros(nv),np.zeros(nh),temperature)


def state(x,n,binary=False):
    a=real_array(x,'State')
    if a.shape!=(n,) or np.any(np.abs(a)>1e6):raise EnergyError(f'Use a state vector with {n} finite entries within ±1,000,000.')
    if binary and np.any((a!=0)&(a!=1)):raise EnergyError('Probabilities and training require binary states containing only 0 and 1.')
    return a


def energy(m,v,h=None):
    m=model(m);v=state(v,m.visible)
    if m.kind=='bm':
        if h is not None:raise EnergyError('A fully visible BM has no hidden state.')
        return float(-.5*v@m.W@v-m.a@v)
    if h is None:raise EnergyError('RBM joint energy needs visible and hidden states. Use free_energy(M,v) for visible states alone.')
    h=state(h,m.hidden)
    return float(-m.a@v-m.b@h-v@m.W@h)


def scores(m,V):
    if m.kind=='bm':return -.5*np.sum((V@m.W)*V,axis=1)-V@m.a
    return -V@m.a-m.temperature*np.logaddexp(0,(V@m.W+m.b)/m.temperature).sum(axis=1)


def free_energy(m,v):
    m=model(m);return float(scores(m,state(v,m.visible)[None,:])[0])


@lru_cache(maxsize=16)
def states(n):
    n=scalar(n,'Enumerated visible units',1,12,True)
    x=((np.arange(2**n)[:,None]>>np.arange(n-1,-1,-1))&1).astype(float);x.setflags(write=False)
    return x


@lru_cache(maxsize=64)
def log_partition(m):
    m=model(m)
    if m.visible>12:raise EnergyError('Exact probabilities and partition functions support at most 12 visible units. Sampling remains available.')
    return float(logsumexp(-scores(m,states(m.visible))/m.temperature))


def energy_probability(m,v):
    m=model(m);v=state(v,m.visible,True)
    return float(np.exp(-free_energy(m,v)/m.temperature-log_partition(m)))


def hidden_probabilities(m,v):
    m=model(m)
    if m.kind!='rbm':raise EnergyError('Hidden probabilities require an RBM.')
    return expit((state(v,m.visible)@m.W+m.b)/m.temperature)


def reconstruct(m,v):
    m=model(m);v=state(v,m.visible)
    if m.kind!='rbm':raise EnergyError('Reconstruction requires an RBM.')
    return expit((hidden_probabilities(m,v)@m.W.T+m.a)/m.temperature)


def energy_state(index,n):
    n=scalar(n,'Visible units',1,16,True);index=scalar(index,'Binary state index',0,2**n-1,True)
    return ((index>>np.arange(n-1,-1,-1))&1).astype(float)


def sample(m,count=32,seed=42,burn=100,thin=5,check=lambda:None):
    m=model(m);count=scalar(count,'Sample count',1,512,True);burn=scalar(burn,'Burn-in sweeps',0,1000,True);thin=scalar(thin,'Thinning sweeps',1,100,True)
    rng=np.random.default_rng(scalar(seed,'Seed',0,2**32-1,True));v=rng.integers(0,2,m.visible).astype(float);out=[]
    for sweep in range(burn+count*thin):
        check()
        if m.kind=='rbm':
            h=rng.random(m.hidden)<expit((v@m.W+m.b)/m.temperature)
            v=(rng.random(m.visible)<expit((h@m.W.T+m.a)/m.temperature)).astype(float)
        else:
            for j in rng.permutation(m.visible):v[j]=rng.random()<expit((m.a[j]+m.W[j]@v)/m.temperature)
        if sweep>=burn and (sweep-burn+1)%thin==0:out.append(v.copy())
    return np.asarray(out)


def energy_sample(m,count=1,seed=42,burn=100,thin=5,*,check=lambda:None):
    scalar(count,'Worksheet sample count',1,32,True)
    return sample(m,count,seed,burn,thin,check=check)


def describe(m):
    m=model(m)
    return dict(kind=m.kind,visible=m.visible,hidden=m.hidden,temperature=m.temperature,exact_available=m.visible<=12)


def analyze(m,count=64,seed=42,check=lambda:None):
    m=model(m);report=describe(m);report['model']=pack(m)
    if m.visible<=12:
        V=states(m.visible);f=scores(m,V);z=log_partition(m);p=np.exp(-f/m.temperature-z)
        order=np.argsort(-p,kind='stable')[:32]
        if m.kind=='rbm':
            H=expit((V@m.W+m.b)/m.temperature)
            joint_energy=-V@m.a-H@m.b-np.sum((V@m.W)*H,axis=1)
        else:joint_energy=f
        report.update(log_partition=z,visible_entropy_bits=float(-np.sum(p*np.log2(np.maximum(p,1e-300)))),
                      expected_energy=float(p@joint_energy),visible_means=(p@V).tolist(),
                      top_states=[dict(state=V[k].astype(int).tolist(),label=''.join(map(str,V[k].astype(int))),probability=float(p[k]),energy=float(f[k])) for k in order],
                      shown_probability_mass=float(np.sum(p[order])),state_count=len(V))
    report['samples']=sample(m,count,seed,check=check).astype(int).tolist()
    report['sample_notice']='Gibbs samples may be correlated; finite burn-in does not guarantee equilibrium.'
    return report


def training_data(value,n,binarize=False,threshold=.5):
    if type(binarize) is not bool:raise EnergyError('Binarize must be true or false.')
    a=real_array(value,'Training data')
    if a.ndim!=2 or not 1<=len(a)<=2048 or a.shape[1]!=n:raise EnergyError(f'Training data needs 1–2048 rows and {n} visible-feature columns.')
    if binarize:a=(a>=scalar(threshold,'Threshold',-1e6,1e6)).astype(float)
    if np.any((a!=0)&(a!=1)):raise EnergyError('Training data must contain only 0 and 1. Enable explicit threshold binarization for continuous values.')
    return a


def options(raw,m,rows):
    if not isinstance(raw,dict):raise EnergyError('Training options must be an object.')
    o=dict(epochs=scalar(raw.get('epochs',200),'Epochs',1,2000,True),rate=scalar(raw.get('rate',.05),'Learning rate',1e-6,1),
           k=scalar(raw.get('k',1),'CD steps',1,20,True),batch=scalar(raw.get('batch',32),'Batch size',1,256,True),
           decay=scalar(raw.get('decay',.0001),'Weight decay',0,1),seed=scalar(raw.get('seed',42),'Seed',0,2**32-1,True),
           validation=scalar(raw.get('validation',.2),'Validation fraction',0,.5))
    cost=o['epochs']*((2**m.visible)*m.visible**2 if m.kind=='bm' else rows*o['k']*m.visible*m.hidden)
    cost+=min(51,o['epochs']+1)*(2**m.visible)*m.visible*max(1,m.hidden) if m.visible<=12 else 0
    if cost>100_000_000:raise EnergyError('Training request is too large. Reduce units, epochs, data rows, or CD steps.')
    return o


def train(m,data,raw_options,check=lambda:None):
    m=model(m);data=training_data(data,m.visible);o=options(raw_options,m,len(data));rng=np.random.default_rng(o['seed'])
    indices=rng.permutation(len(data));nv=min(len(data)-1,max(1,int(len(data)*o['validation']))) if o['validation'] and len(data)>1 else 0
    validation=data[indices[:nv]];train=data[indices[nv:]];W=m.W.copy();a=m.a.copy();b=m.b.copy();T=m.temperature
    history=[];clipped=0
    def current():return make(m.kind,W,a,b,T)
    def metrics(epoch):
        check();active=current();record={'epoch':epoch}
        for label,values in [('train',train),('validation',validation)]:
            if not len(values):continue
            if active.kind=='rbm':
                H=expit((values@W+b)/T);R=expit((H@W.T+a)/T)
                record[label+'_reconstruction_mse']=float(np.mean((values-R)**2))
            if active.visible<=12:record[label+'_nll']=float(np.mean(scores(active,values))/T+log_partition(active))
        history.append(record)
    metrics(0)
    for epoch in range(1,o['epochs']+1):
        check()
        if m.kind=='bm':
            V=states(m.visible);active=current();p=np.exp(-scores(active,V)/T-log_partition(active))
            dW=(train.T@train/len(train)-V.T@(p[:,None]*V))/T-o['decay']*W
            da=(train.mean(axis=0)-p@V)/T
            W+=o['rate']*dW;np.fill_diagonal(W,0);W=(W+W.T)/2;a+=o['rate']*da
        else:
            for start in range(0,len(train),o['batch']):
                check()
                if start==0:order=rng.permutation(len(train))
                v0=train[order[start:start+o['batch']]];ph0=expit((v0@W+b)/T);vk=v0.copy()
                for _ in range(o['k']):
                    check();hk=rng.random((len(vk),m.hidden))<expit((vk@W+b)/T)
                    vk=(rng.random(vk.shape)<expit((hk@W.T+a)/T)).astype(float)
                phk=expit((vk@W+b)/T)
                W+=o['rate']*((v0.T@ph0-vk.T@phk)/(len(v0)*T)-o['decay']*W)
                a+=o['rate']*np.mean(v0-vk,axis=0)/T;b+=o['rate']*np.mean(ph0-phk,axis=0)/T
        for x in (W,a,b):
            if not np.all(np.isfinite(x)):raise EnergyError('Training became non-finite. Reduce the learning rate or increase temperature.')
            clipped+=int(np.count_nonzero(np.abs(x)>100));np.clip(x,-100,100,out=x)
        if epoch%max(1,int(np.ceil(o['epochs']/50)))==0 or epoch==o['epochs']:metrics(epoch)
    fitted=current();report=analyze(fitted,seed=o['seed'],check=check)
    report.update(history=history,training=dict(algorithm='CD-'+str(o['k']) if m.kind=='rbm' else 'Exact maximum likelihood',train_rows=len(train),validation_rows=len(validation),options=o,clipped_parameters=clipped))
    return report


FUNCTIONS={'rbm':rbm,'boltzmann_machine':boltzmann_machine,'energy':energy,'free_energy':free_energy,
           'energy_probability':energy_probability,'log_partition':log_partition,'hidden_probabilities':hidden_probabilities,
           'reconstruct':reconstruct,'energy_sample':energy_sample,'energy_state':energy_state,
           'energy_weights':lambda m:model(m).W,'energy_bias':lambda m:model(m).a,'hidden_bias':lambda m:model(m).b}
