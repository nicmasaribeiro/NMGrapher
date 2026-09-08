"""Reproducible GBM paths and bounded, ordered worksheet trajectories."""
import ast
from dataclasses import dataclass
from functools import lru_cache
import numpy as np
from datasets import DataColumn
from array_types import VectorValue


class TrajectoryError(ValueError):pass


def number(v,label,lo,hi,integer=False):
    if isinstance(v,(bool,np.bool_)) or not isinstance(v,(int,float,np.integer,np.floating)) or not np.isfinite(v) or not lo<=v<=hi or integer and int(v)!=v:
        raise TrajectoryError(f'{label} must be {"an integer " if integer else ""}between {lo} and {hi}.')
    return int(v) if integer else float(v)


def state(value):
    a=np.asarray(value)
    if a.ndim==0:a=a.reshape(1)
    if a.ndim!=1 or not 1<=a.size<=8 or not np.issubdtype(a.dtype,np.number) or np.iscomplexobj(a) and np.any(a.imag!=0):raise TrajectoryError('A state must be a real scalar or vector with 1–8 components.')
    a=np.asarray(a.real,dtype=float)
    if not np.all(np.isfinite(a)) or np.any(np.abs(a)>1e100):raise TrajectoryError('State values must stay finite and within ±1e100. Reduce the step size or stabilize the update.')
    return a


@dataclass(frozen=True,eq=False)
class Trajectory:
    time:np.ndarray
    values:np.ndarray  # path × time × component
    spec:dict


def create(time,values,spec):
    t=np.asarray(time,dtype=float);v=np.asarray(values,dtype=float)
    if t.ndim!=1 or not 2<=len(t)<=2000 or np.any(np.diff(t)<=0) or not np.all(np.isfinite(t)):raise TrajectoryError('Trajectory times must be finite and strictly increasing, with 2–2000 samples.')
    if v.ndim!=3 or v.shape[1]!=len(t) or not 1<=v.shape[0]<=24 or not 1<=v.shape[2]<=8 or v.size+len(t)>50000:raise TrajectoryError('Use at most 24 paths, 8 state components, and 50,000 total values including time.')
    if not np.all(np.isfinite(v)) or np.any(np.abs(v)>1e100):raise TrajectoryError('Trajectory values exceed the supported numeric range. Reduce the horizon, drift, or volatility.')
    t=t.copy();v=v.copy();t.setflags(write=False);v.setflags(write=False)
    return Trajectory(t,v,dict(spec))


def settings(raw):
    if not isinstance(raw,dict):raise TrajectoryError('Supply trajectory settings.')
    kind=raw.get('kind','gbm')
    if kind not in ('gbm','parametric','sequence'):raise TrajectoryError('Choose GBM, a parametric function, or a sequential algorithm.')
    out=dict(kind=kind,steps=number(raw.get('steps',252),'Steps',1,1999,True),horizon=number(raw.get('horizon',1),'Horizon',1e-6,100000))
    if kind=='gbm':
        out.update(initial=number(raw.get('initial',100),'Initial value',1e-12,1e12),drift=number(raw.get('drift',.05),'Drift',-10,10),volatility=number(raw.get('volatility',.2),'Volatility',0,5),paths=number(raw.get('paths',8),'Paths',1,24,True),seed=number(raw.get('seed',42),'Seed',0,2**32-1,True))
        if out['horizon']>100:raise TrajectoryError('GBM horizon must be at most 100 time units.')
    else:
        out['start']=number(raw.get('start',0),'Start time',-1e5,1e5)
        key='update' if kind=='sequence' else 'expression';value=raw.get(key,'')
        if not isinstance(value,str) or not value.strip() or len(value)>1200:raise TrajectoryError('Enter a trajectory formula of 1–1200 characters.')
        out[key]=value.strip()
        from engine import parse
        parse(out[key])
        if kind=='sequence':out['initial']=state(raw.get('initial',[1,0])).tolist()
    return out


def gbm(initial,drift,volatility,horizon=1,steps=252,paths=8,seed=42):
    o=settings(dict(kind='gbm',initial=initial,drift=drift,volatility=volatility,horizon=horizon,steps=steps,paths=paths,seed=seed))
    return _gbm(o['initial'],o['drift'],o['volatility'],o['horizon'],o['steps'],o['paths'],o['seed'])


@lru_cache(maxsize=16)
def _gbm(initial,drift,volatility,horizon,steps,paths,seed):
    # Independent RNG streams keep an existing path unchanged when adding paths.
    time=np.linspace(0,horizon,steps+1);dt=horizon/steps
    streams=np.random.SeedSequence(seed).spawn(paths);values=[]
    for stream in streams:
        z=np.random.default_rng(stream).standard_normal(steps)
        logs=np.log(initial)+np.r_[0,np.cumsum((drift-.5*volatility**2)*dt+volatility*np.sqrt(dt)*z)]
        if np.any(logs>np.log(1e100)) or np.any(logs<-690):raise TrajectoryError('GBM values exceed the positive numeric range. Reduce horizon, drift, or volatility.')
        values.append(np.exp(logs)[:,None])
    result=create(time,values,dict(kind='gbm',initial=initial,drift=drift,volatility=volatility,horizon=horizon,steps=steps,paths=paths,seed=seed))
    # Validate analytical references as well as the sampled realizations.
    gbm_reference(result)
    return result


def gbm_mean(initial,drift,t):
    initial=number(initial,'Initial value',1e-12,1e12);drift=number(drift,'Drift',-10,10);t=np.asarray(t)
    if np.iscomplexobj(t) or not np.all(np.isfinite(t)) or np.any((t<0)|(t>100)):raise TrajectoryError('GBM time must be real and between 0 and 100.')
    with np.errstate(over='ignore'):result=initial*np.exp(drift*t)
    if not np.all(np.isfinite(result)) or np.any(result>1e100):raise TrajectoryError('GBM mean exceeds the supported numeric range.')
    return result


def gbm_reference(g):
    o=g.spec;t=g.time;mu=o['drift'];sigma=o['volatility'];s=o['initial']
    with np.errstate(over='ignore',invalid='ignore'):
        mean=gbm_mean(s,mu,t);median=s*np.exp((mu-.5*sigma*sigma)*t)
        low=median*np.exp(-1.959963984540054*sigma*np.sqrt(t));high=median*np.exp(1.959963984540054*sigma*np.sqrt(t))
        variance=mean*mean*np.expm1(sigma*sigma*t)
    if not all(np.all(np.isfinite(a)) and np.all(np.abs(a)<=1e200) for a in (mean,median,low,high,variance)):raise TrajectoryError('GBM reference moments exceed the numeric range. Reduce horizon, drift, or volatility.')
    return dict(mean=mean.tolist(),median=median.tolist(),lower=low.tolist(),upper=high.tolist(),terminal_variance=float(variance[-1]))


def compute(c,raw,local=None,stack=()):
    from engine import parse,EvaluationLimit
    o=settings(raw);c.check_cancelled()
    if o['kind']=='gbm':return gbm(o['initial'],o['drift'],o['volatility'],o['horizon'],o['steps'],o['paths'],o['seed'])
    time=np.linspace(o['start'],o['start']+o['horizon'],o['steps']+1);dt=o['horizon']/o['steps'];local=local or {};total=0
    tree=parse(o['update'] if o['kind']=='sequence' else o['expression'])
    def point(bindings):
        nonlocal total
        c.check_cancelled();before=c.steps
        with np.errstate(all='ignore'):v=c.evaluate(tree,{**local,**bindings},stack)
        total+=c.steps-before
        if total>500000:raise EvaluationLimit('Trajectory computation limit reached; use fewer steps or a simpler update.')
        return state(v)
    # Each point gets its ordinary expression budget; the full path has its own cap.
    original_steps=c.steps
    try:
        if o['kind']=='sequence':
            current=state(o['initial']);values=[current]
            for k,t in enumerate(time[:-1]):
                c.steps=0
                try:next_state=point(dict(s=current.view(VectorValue),k=k,t=float(t),dt=dt))
                except (ValueError,ArithmeticError) as exc:raise TrajectoryError(f'Update failed at step {k+1}, t={t:g}: {exc}') from exc
                if next_state.shape!=current.shape:raise TrajectoryError(f'Update changed the state dimension at step {k+1}.')
                current=next_state.copy();values.append(current)
        else:
            values=[];shape=None
            for k,t in enumerate(time):
                c.steps=0
                try:v=point(dict(t=float(t),k=k,dt=dt))
                except (ValueError,ArithmeticError) as exc:raise TrajectoryError(f'Trajectory failed at t={t:g}: {exc}') from exc
                if shape is not None and v.shape!=shape:raise TrajectoryError('The trajectory must keep the same number of components.')
                shape=v.shape;values.append(v)
        return create(time,[values],o)
    finally:c.steps=original_steps+total


def evaluate_operator(c,node,local,stack):
    name=node.func.id
    if len(node.args)!=4 or not isinstance(node.args[0],ast.Name) or node.args[0].id not in c.functions:raise TrajectoryError('Use iterate(G,initial,steps,dt) with G(s,k,t,dt), or trajectory(r,start,end,steps) with r(t).')
    function=node.args[0].id;params,_=c.functions[function]
    values=[c.evaluate(arg,local,stack) for arg in node.args[1:]]
    if name=='iterate':
        if len(params)!=4:raise TrajectoryError('An update function needs four arguments: G(s,k,t,dt).')
        initial,steps,dt=values;steps=number(steps,'Steps',1,1999,True);dt=number(dt,'Step size',1e-9,1e5)
        spec=dict(kind='sequence',initial=initial,steps=steps,horizon=dt*steps,update=f'{function}(s,k,t,dt)')
    else:
        if len(params)!=1:raise TrajectoryError('A parametric function needs one time argument: r(t).')
        lower,upper,steps=values;lower=number(lower,'Start time',-1e5,1e5);upper=number(upper,'End time',-1e5,2e5)
        spec=dict(kind='parametric',start=lower,horizon=upper-lower,steps=steps,expression=f'{function}(t)')
    return compute(c,spec,local,stack)


def trajectory(g):
    if not isinstance(g,Trajectory):raise TrajectoryError('Use a trajectory object such as G=gbm(100,0.05,0.2).')
    return g


def trajectory_times(g):return trajectory(g).time.copy().view(DataColumn)
def trajectory_path(g,index=0,component=0):
    g=trajectory(g);i=number(index,'Path index',0,g.values.shape[0]-1,True);j=number(component,'Component index',0,g.values.shape[2]-1,True)
    return g.values[i,:,j].copy().view(DataColumn)


def report(g):
    g=trajectory(g);out=dict(kind=g.spec['kind'],time=g.time.tolist(),values=g.values.tolist(),dimensions=g.values.shape[2],paths=g.values.shape[0],frames=len(g.time),spec=g.spec)
    if out['kind']=='gbm':out['reference']=gbm_reference(g)
    return out


def validate_report(raw):
    if not isinstance(raw,dict):raise TrajectoryError('Supply a generated trajectory.')
    g=create(raw.get('time'),raw.get('values'),settings(raw.get('spec')))
    o=g.spec;start=o.get('start',0)
    if len(g.time)!=o['steps']+1 or not np.allclose(g.time,np.linspace(start,start+o['horizon'],o['steps']+1),rtol=1e-12,atol=1e-12) or g.values.shape[0]!=(o.get('paths',1) if o['kind']=='gbm' else 1):raise TrajectoryError('Trajectory values do not match the generation settings.')
    # Export never trusts supplied metadata, dimensions, or theoretical curves.
    if g.spec['kind']=='gbm':
        if g.values.shape[2]!=1 or np.any(g.values<=0):raise TrajectoryError('GBM paths must be positive scalars.')
    return report(g)


FUNCTIONS={'gbm':gbm,'gbm_mean':gbm_mean,'trajectory_times':trajectory_times,'trajectory_path':trajectory_path}
