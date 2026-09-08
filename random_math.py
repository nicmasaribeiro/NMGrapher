"""Deterministic random arrays: no global RNG or worker-dependent state."""
import numpy as np


def integer(value, label, low, high):
    if np.ndim(value) or np.iscomplexobj(value) or not np.isfinite(value) or int(value) != value or not low <= value <= high:
        raise ValueError(f'{label} must be an integer from {low} to {high}.')
    return int(value)


def rng(seed):
    return np.random.default_rng(integer(seed, 'Seed', 0, 2**32-1))


def probability(p):
    if np.ndim(p) or np.iscomplexobj(p) or not np.isfinite(p) or not 0 <= p <= 1:
        raise ValueError('Activation probability must be between 0 and 1.')
    return float(p)


def shape(n, m=None):
    n=integer(n, 'Size', 1, 32)
    return (n,) if m is None else (n, integer(m, 'Columns', 1, 32))


def random_vector(n, seed=0):return rng(seed).random(shape(n))
def random_matrix(n, m, seed=0):return rng(seed).random(shape(n,m))
def normal_vector(n, seed=0):return rng(seed).standard_normal(shape(n))
def normal_matrix(n, m, seed=0):return rng(seed).standard_normal(shape(n,m))


def activate(value, p=0.5, seed=0):
    a=np.asarray(value)
    if a.ndim not in (1,2) or not a.size or max(a.shape)>32 or not np.all(np.isfinite(a)):
        raise ValueError('Activation needs a finite vector or matrix up to 32×32.')
    return a*(rng(seed).random(a.shape)<probability(p))


def random_gate(value, p=0.5, seed=0):
    a=np.asarray(value)
    # Reuse shape/finite validation without changing the whole-object gate.
    activate(a, 1, 0)
    return a*(rng(seed).random()<probability(p))


def stochastic_matrix(n, seed=0):
    a=random_matrix(n,n,seed)
    return a/a.sum(axis=1,keepdims=True)

FUNCTIONS={name:globals()[name] for name in ('random_vector','random_matrix','normal_vector','normal_matrix','activate','random_gate','stochastic_matrix')}
