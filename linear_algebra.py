"""Bounded numerical matrix decompositions and diagnostics."""
import numpy as np
from scipy import linalg


def check(a, square=False):
    a=np.asarray(a,dtype=complex)
    if a.ndim!=2 or not a.size or max(a.shape)>32 or not np.all(np.isfinite(a)):
        raise ValueError('Use a finite, nonempty matrix with at most 32 rows and columns.')
    if square and a.shape[0]!=a.shape[1]:raise ValueError('This operation needs a square matrix.')
    return a


def eigenpairs(a):
    a=check(a,True)
    values,vectors=np.linalg.eigh(a) if np.array_equal(a,a.conj().T) else np.linalg.eig(a)
    order=np.lexsort((values.imag,values.real));values=values[order];vectors=vectors[:,order]
    # Choose a consistent phase; eigenvectors are otherwise only defined up to scale.
    for i in range(vectors.shape[1]):
        vectors[:,i]/=np.linalg.norm(vectors[:,i])
        pivot=vectors[np.argmax(abs(vectors[:,i])),i]
        if abs(pivot):vectors[:,i]*=np.conj(pivot)/abs(pivot)
    return values,vectors


def svd(a):return np.linalg.svd(check(a),full_matrices=False)
def qr(a):return np.linalg.qr(check(a),mode='reduced')
def lu(a):return linalg.lu(check(a))

def cholesky(a):
    a=check(a,True)
    if not np.allclose(a,a.conj().T,atol=1e-12,rtol=1e-12):raise ValueError('Cholesky needs a Hermitian positive-definite matrix.')
    try:return np.linalg.cholesky(a)
    except np.linalg.LinAlgError as exc:raise ValueError('Cholesky needs a Hermitian positive-definite matrix.') from exc


def condition(a):
    a=check(a)
    if np.linalg.matrix_rank(a)<min(a.shape):raise ValueError('Condition number is infinite at the numerical rank tolerance; this matrix is rank-deficient.')
    return float(np.linalg.cond(a))


def diagonal(a):
    a=np.asarray(a)
    if a.ndim not in (1,2) or not a.size or max(a.shape)>32:raise ValueError('diag needs a vector or matrix with dimensions up to 32.')
    return np.diag(a)


def least_squares(a,b):
    a=check(a);b=np.asarray(b,dtype=complex)
    if b.ndim not in (1,2) or not b.size or max(b.shape)>32 or b.shape[0]!=a.shape[0] or not np.all(np.isfinite(b)):
        raise ValueError('The right-hand side must be a finite vector or matrix with one row per row of A, within the 32-entry/dimension limit.')
    return np.linalg.lstsq(a,b,rcond=None)[0]

FUNCTIONS={
    'eigvals':lambda a:eigenpairs(a)[0], 'eigenvalues':lambda a:eigenpairs(a)[0],
    'eigvecs':lambda a:eigenpairs(a)[1], 'eigenvectors':lambda a:eigenpairs(a)[1],
    'svdU':lambda a:svd(a)[0], 'svdS':lambda a:np.diag(svd(a)[1]), 'svdVh':lambda a:svd(a)[2],
    'singular_values':lambda a:svd(a)[1], 'qrQ':lambda a:qr(a)[0], 'qrR':lambda a:qr(a)[1],
    'luP':lambda a:lu(a)[0], 'luL':lambda a:lu(a)[1], 'luU':lambda a:lu(a)[2],
    'cholesky':cholesky, 'nullspace':lambda a:linalg.null_space(check(a)),
    'orth':lambda a:linalg.orth(check(a)), 'nullity':lambda a:check(a).shape[1]-np.linalg.matrix_rank(check(a)),
    'cond':condition, 'diag':diagonal, 'lstsq':least_squares,
}


def packed(a):
    a=np.asarray(a)
    def value(z):
        z=complex(z)
        if not np.isfinite(z):return None
        return float(z.real) if abs(z.imag)==0 else f'{z.real:.10g}{z.imag:+.10g}i'
    def nested(a):return [nested(v) for v in a] if a.ndim else value(a)
    return {'shape':list(a.shape),'value':nested(a)}


def analyze(a,b=None):
    a=check(a);m,n=a.shape;rank=int(np.linalg.matrix_rank(a));denominator=max(1.0,float(np.linalg.norm(a)))
    U,s,Vh=svd(a);Q,R=qr(a);P,L,LU=lu(a)
    residual=lambda approximation:float(np.linalg.norm(a-approximation)/denominator)
    info={'shape':[m,n],'rank':rank,'nullity':n-rank,'norm':float(np.linalg.norm(a)),
          'condition':None if rank<min(a.shape) else float(np.linalg.cond(a)),
          'singular_values':packed(s), 'column_basis':packed(linalg.orth(a)), 'null_basis':packed(linalg.null_space(a)),
          'svd':{'U':packed(U),'S':packed(np.diag(s)),'Vh':packed(Vh),'residual':residual(U@np.diag(s)@Vh)},
          'qr':{'Q':packed(Q),'R':packed(R),'residual':residual(Q@R)},
          'lu':{'P':packed(P),'L':packed(L),'U':packed(LU),'residual':residual(P@L@LU)}}
    if m==n:
        values,vectors=eigenpairs(a);vector_rank=int(np.linalg.matrix_rank(vectors))
        info.update(trace=packed(np.trace(a)),determinant=packed(np.linalg.det(a)),
                    hermitian=bool(np.allclose(a,a.conj().T,atol=1e-10,rtol=1e-10)),
                    unitary=bool(np.allclose(a.conj().T@a,np.eye(n),atol=1e-10,rtol=1e-10)))
        info['eigen']={'values':packed(values),'vectors':packed(vectors),
                       'residual':float(np.linalg.norm(a@vectors-vectors@np.diag(values))/denominator),
                       'basis_rank':vector_rank,'diagonalizable':vector_rank==n,
                       'condition':float(np.linalg.cond(vectors)) if vector_rank==n else None}
        try:
            C=cholesky(a);info['cholesky']={'L':packed(C),'residual':residual(C@C.conj().T)}
        except ValueError as exc:info['cholesky']={'error':str(exc)}
    if b is not None:
        solution=least_squares(a,b);b=np.asarray(b)
        info['solution']={'x':packed(solution),'residual':float(np.linalg.norm(a@solution-b)),
                          'exact_within_tolerance':bool(np.linalg.norm(a@solution-b)<=1e-10*max(1,float(np.linalg.norm(b))))}
    return info
