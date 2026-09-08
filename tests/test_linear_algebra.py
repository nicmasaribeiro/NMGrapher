import numpy as np
import pytest
from linear_algebra import eigenpairs, analyze, FUNCTIONS
from engine import Calculator
from app import app


def run(*rows):return Calculator([{'text':s} for s in rows]).run([-2,2,-2,2])


@pytest.mark.parametrize('a',[
    [[2,1],[1,3]],[[0,-1],[1,0]],[[2,1j],[-1j,3]],np.eye(3),[[1,1],[0,1]],
])
def test_eigenpair_alignment_normalization_and_residual(a):
    a=np.asarray(a);w,V=eigenpairs(a)
    np.testing.assert_allclose(a@V,V@np.diag(w),atol=1e-10)
    np.testing.assert_allclose(np.linalg.norm(V,axis=0),1,atol=1e-10)
    np.testing.assert_allclose(FUNCTIONS['eigvals'](a),w)
    np.testing.assert_allclose(FUNCTIONS['eigvecs'](a),V)


@pytest.mark.parametrize('a',[
    [[1,2,3],[4,5,6]],[[1,2],[3,4],[5,6]],[[1,2],[2,4]],[[1,1j],[2,3]],
])
def test_decomposition_reconstruction(a):
    a=np.asarray(a)
    np.testing.assert_allclose(FUNCTIONS['svdU'](a)@FUNCTIONS['svdS'](a)@FUNCTIONS['svdVh'](a),a,atol=1e-10)
    np.testing.assert_allclose(FUNCTIONS['qrQ'](a)@FUNCTIONS['qrR'](a),a,atol=1e-10)
    np.testing.assert_allclose(FUNCTIONS['luP'](a)@FUNCTIONS['luL'](a)@FUNCTIONS['luU'](a),a,atol=1e-10)
    report=analyze(a)
    assert max(report[k]['residual'] for k in ('svd','qr','lu'))<1e-12


def test_cholesky_complex_and_invalid_inputs():
    a=np.array([[3,1j],[-1j,2]])
    L=FUNCTIONS['cholesky'](a)
    np.testing.assert_allclose(L@L.conj().T,a,atol=1e-10)
    for a in ([[1,2],[2,1]],[[1,2],[0,1]]):
        with pytest.raises(ValueError,match='positive-definite'):FUNCTIONS['cholesky'](a)


def test_nullspaces_zero_dimension_and_orthonormal_bases():
    a=np.array([[1,2,3],[2,4,6]])
    N=FUNCTIONS['nullspace'](a);Q=FUNCTIONS['orth'](a)
    assert N.shape==(3,2) and Q.shape==(2,1)
    np.testing.assert_allclose(a@N,0,atol=1e-10)
    np.testing.assert_allclose(N.conj().T@N,np.eye(2),atol=1e-10)
    r=run('nullspace(eye(3))','orth([[0,0],[0,0]])','nullity(eye(3))')
    assert not any(v.get('error') for v in r)
    assert r[0]['shape']==[3,0] and r[0]['empty_basis']
    assert r[1]['shape']==[2,0] and r[2]['value']==0


def test_least_squares_minimum_norm_and_multiple_rhs():
    a=np.array([[1,1]])
    np.testing.assert_allclose(FUNCTIONS['lstsq'](a,[2]),[1,1],atol=1e-10)
    a=np.array([[1,0],[0,1],[1,1]])
    b=np.array([[1,2],[2,4],[4,8]])
    x=FUNCTIONS['lstsq'](a,b)
    np.testing.assert_allclose(a.T@(a@x-b),0,atol=1e-10)
    assert analyze(a,b)['solution']['exact_within_tolerance'] is False


def test_defective_matrix_diagnostics():
    report=analyze([[1,1],[0,1]])
    assert not report['eigen']['diagonalizable'] and report['eigen']['basis_rank']==1
    assert analyze([[1,2],[2,4]])['condition'] is None
    with pytest.raises(ValueError,match='rank-deficient'):FUNCTIONS['cond']([[1,2],[2,4]])


def test_equation_functions_and_matrix_function_composition():
    r=run('A=[[2,1],[1,3]]','V=eigvecs(A)','λ=eigvals(A)','A@V-V@diag(λ)','s(t)=singular_values([[t,0],[0,2]])','s(1)','lstsq([[1,1]],[2])')
    assert not any(v.get('error') for v in r),[v.get('error') for v in r]
    np.testing.assert_allclose(r[3]['real'],0,atol=1e-10)
    np.testing.assert_allclose(r[5]['value'],[2,1],atol=1e-10)
    np.testing.assert_allclose(r[6]['value'],[1,1],atol=1e-10)


def test_analysis_api_context_and_validation():
    client=app.test_client()
    response=client.post('/api/linear-algebra',json={'expressions':[{'text':'A=[[2,1],[1,3]]'}],'matrix':'A','rhs':'[1,0]'})
    assert response.status_code==200
    a=response.get_json()['analysis'];assert a['rank']==2 and a['null_basis']['shape']==[2,0]
    np.testing.assert_allclose(a['solution']['x']['value'],[.6,-.2],atol=1e-10)
    for payload in ({'matrix':'[1,2]'}, {'matrix':'[[1,2],[3,4]]','rhs':'[1]'}, {'matrix':'unknown'}, {'matrix':"__import__('os')"}):
        assert client.post('/api/linear-algebra',json=payload).status_code==400
