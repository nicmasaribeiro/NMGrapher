"""Small numerical quantum-state simulator (up to five qubits, hbar = 1)."""
import numpy as np
from scipy.linalg import expm

MAX_DIM=32
TOL=1e-9

class QuantumError(ValueError):
    pass


def vector(v):
    a=np.asarray(v,dtype=complex)
    if a.ndim==2 and a.shape[1]==1:a=a[:,0]
    if a.ndim!=1 or not 1<=a.size<=MAX_DIM or not np.all(np.isfinite(a)):
        raise QuantumError('Use a finite vector of 1–32 entries, or a column vector.')
    return a


def normalize(v):
    a=vector(v);scale=np.max(np.abs(a))
    if scale==0:raise QuantumError('The zero vector cannot be normalized.')
    a=a/scale
    return a/np.linalg.norm(a)


def register_dimension(n):
    if n<2 or n>MAX_DIM or n&(n-1):
        raise QuantumError('A quantum state needs 2, 4, 8, 16, or 32 amplitudes.')
    return int(np.log2(n))


def state(v):
    a=normalize(v);register_dimension(len(a));return a


def qubit(alpha,beta):
    if np.ndim(alpha) or np.ndim(beta):raise QuantumError('Qubit amplitudes must be scalars.')
    return state([alpha,beta])


def real_scalar(v,label='Angle'):
    if np.ndim(v) or not np.isfinite(v) or np.imag(v)!=0:
        raise QuantumError(label+' must be a finite real scalar.')
    return float(np.real(v))


def blochstate(theta,phi):
    theta,phi=real_scalar(theta),real_scalar(phi)
    return np.array([np.cos(theta/2),np.exp(1j*phi)*np.sin(theta/2)])


def basis(index,qubits=1):
    n=real_scalar(qubits,'Qubit count');k=real_scalar(index,'Basis index')
    if int(n)!=n or not 1<=n<=5:raise QuantumError('Use an integer qubit count from 1 to 5.')
    if int(k)!=k or not 0<=k<2**int(n):raise QuantumError('Basis index is outside the register.')
    out=np.zeros(2**int(n),complex);out[int(k)]=1;return out


def ket(v):
    """An unnormalized register column; never silently change its amplitudes."""
    a=vector(v);register_dimension(len(a));return a.reshape(-1,1)


def ketbasis(index,qubits=1):return ket(basis(index,qubits))
def ketplus():return ket([1/np.sqrt(2),1/np.sqrt(2)])
def ketminus():return ket([1/np.sqrt(2),-1/np.sqrt(2)])
def ketplusi():return ket([1/np.sqrt(2),1j/np.sqrt(2)])
def ketminusi():return ket([1/np.sqrt(2),-1j/np.sqrt(2)])


def braket(a,b):
    a,b=ket(a)[:,0],ket(b)[:,0]
    if a.shape!=b.shape:raise QuantumError('Bra and ket dimensions must agree.')
    return np.vdot(a,b)


def ketbra(a,b):
    # Rectangular maps between different registers are valid dyads.
    return ket(a)@ket(b).conj().T


def matrix_element(a,operator,b):
    a,b=ket(a)[:,0],ket(b)[:,0];operator=np.asarray(operator,dtype=complex)
    if operator.shape!=(len(a),len(b)) or not np.all(np.isfinite(operator)):
        raise QuantumError('The operator dimensions must match the bra and ket.')
    return np.vdot(a,operator@b)


def pure_vector(v):
    a=vector(v);register_dimension(len(a))
    if not np.isclose(np.vdot(a,a).real,1,atol=TOL,rtol=0):
        raise QuantumError('State amplitudes must have norm 1. Use state(v) or normalize(v).')
    return a


def density(s):
    a=np.asarray(s,dtype=complex)
    if a.ndim==1 or (a.ndim==2 and a.shape[1]==1):
        a=pure_vector(a);return np.outer(a,a.conj())
    if a.ndim!=2 or a.shape[0]!=a.shape[1]:raise QuantumError('Use a state vector or a square density matrix.')
    register_dimension(len(a))
    if not np.all(np.isfinite(a)) or not np.allclose(a,a.conj().T,atol=TOL,rtol=0):
        raise QuantumError('A density matrix must be finite and Hermitian.')
    if not np.isclose(np.trace(a),1,atol=TOL,rtol=0):raise QuantumError('A density matrix must have trace 1.')
    if np.linalg.eigvalsh(a).min()<-TOL:raise QuantumError('A density matrix must be positive semidefinite.')
    return a


def probabilities(s):
    rho=density(s);p=np.maximum(np.diag(rho).real,0);return p/p.sum()


def pauliX():return np.array([[0,1],[1,0]],complex)
def pauliY():return np.array([[0,-1j],[1j,0]],complex)
def pauliZ():return np.array([[1,0],[0,-1]],complex)
def hadamard():return np.array([[1,1],[1,-1]],complex)/np.sqrt(2)
def Sgate():return np.diag([1,1j])
def Tgate():return np.diag([1,np.exp(1j*np.pi/4)])
def CNOT():return np.array([[1,0,0,0],[0,1,0,0],[0,0,0,1],[0,0,1,0]],complex)


def rotation(pauli,angle):
    angle=real_scalar(angle)
    return np.cos(angle/2)*np.eye(2)-1j*np.sin(angle/2)*pauli

def Rx(angle):return rotation(pauliX(),angle)
def Ry(angle):return rotation(pauliY(),angle)
def Rz(angle):return rotation(pauliZ(),angle)


def expect(operator,s):
    rho=density(s);a=np.asarray(operator,dtype=complex)
    if a.shape!=rho.shape or not np.all(np.isfinite(a)):raise QuantumError('Operator and state dimensions must agree.')
    return np.trace(rho@a)


def bloch(s):
    rho=density(s)
    if rho.shape!=(2,2):raise QuantumError('The Bloch sphere represents one qubit. Use reduced(state, index) for a register.')
    return np.array([np.trace(rho@p).real for p in (pauliX(),pauliY(),pauliZ())])


def purity(s):return float(np.trace(density(s)@density(s)).real)

def entropy(s):
    vals=np.maximum(np.linalg.eigvalsh(density(s)),0);vals=vals[vals>0]
    return float(-np.sum(vals*np.log2(vals)))


def fidelity(a,b):return float(abs(np.vdot(pure_vector(a),pure_vector(b)))**2)


def reduced(s,index):
    rho=density(s);n=register_dimension(len(rho));index=real_scalar(index,'Qubit index')
    if int(index)!=index or not 0<=index<n:raise QuantumError('Qubit index must be from 0 to n-1 (leftmost qubit is 0).')
    k=int(index);axes=[k]+[j for j in range(n) if j!=k]+[n+k]+[n+j for j in range(n) if j!=k]
    a=rho.reshape([2]*(2*n)).transpose(axes).reshape(2,2**(n-1),2,2**(n-1))
    return np.trace(a,axis1=1,axis2=3)


def evolve(s,hamiltonian,time):
    rho=density(s);h=np.asarray(hamiltonian,dtype=complex);time=real_scalar(time,'Time')
    if h.shape!=rho.shape or not np.all(np.isfinite(h)) or not np.allclose(h,h.conj().T,atol=TOL,rtol=0):
        raise QuantumError('The Hamiltonian must be a finite Hermitian matrix matching the state.')
    u=expm(-1j*time*h)
    a=np.asarray(s)
    return u@pure_vector(s) if a.ndim==1 or (a.ndim==2 and a.shape[1]==1) else u@rho@u.conj().T


def quantum_info(s):
    """Return a physical interpretation only for already valid states."""
    try:
        rho=density(s);n=register_dimension(len(rho))
        return {'qubits':n,'dimension':len(rho),'probabilities':probabilities(rho).tolist(),
                'purity':purity(rho),'entropy':entropy(rho),
                'bloch':bloch(rho).tolist() if n==1 else None,
                'basis':[format(k,f'0{n}b') for k in range(len(rho))]}
    except (ValueError,TypeError,np.linalg.LinAlgError):return None

FUNCTIONS={name:globals()[name] for name in (
    'ket','ketbasis','ketplus','ketminus','ketplusi','ketminusi','braket','ketbra','matrix_element',
    'state','qubit','blochstate','basis','normalize','density','probabilities','pauliX','pauliY','pauliZ',
    'hadamard','Sgate','Tgate','CNOT','Rx','Ry','Rz','expect','bloch','purity','entropy','fidelity','reduced','evolve')}
FUNCTIONS.update(ket0=lambda:basis(0),ket1=lambda:basis(1),projector=density)
