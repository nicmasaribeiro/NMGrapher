import numpy as np
import pytest
from engine import Calculator
from app import app

def run(*lines):
    return Calculator([{'text':s} for s in lines]).run([-5,5,-5,5])

def test_matrix_algebra():
    r=run('A = [[2,1],[1,3]]','B = [[1,-1],[0,2]]','A @ B','A * B','A^2','A^-1','det(A)','T(B)','solve(A,[1,2])')
    assert not any('error' in x for x in r)
    np.testing.assert_allclose(r[2]['value'],[[2,0],[1,5]])
    np.testing.assert_allclose(r[3]['value'],r[2]['value'])
    np.testing.assert_allclose(r[4]['value'],[[5,5],[5,10]])
    np.testing.assert_allclose(r[5]['value'],[[.6,-.2],[-.2,.4]])
    assert r[6]['value']==pytest.approx(5)
    np.testing.assert_allclose(r[7]['value'],[[1,0],[-1,2]])
    np.testing.assert_allclose(r[8]['value'],[.2,.6])

def test_ctmc_exponential():
    r=run('t=2','Q=[[-0.3,0.2,0.1],[0.1,-0.3,0.2],[0.2,0.1,-0.3]]','P=expm(t*Q)','p=[[0,1,0]]','p@P')
    P=np.array(r[2]['value'])
    assert np.all(P>=0)
    np.testing.assert_allclose(P.sum(axis=1),1,atol=1e-12)
    np.testing.assert_allclose(r[4]['value'],[P[1]])

def test_forward_dependencies_functions_and_sliders():
    r=run('y=f(x)','f(t)=a*sin(t)','a=2','B=[[a,0],[0,a]]','B[0,0]')
    assert r[0]['kind']=='curve'
    np.testing.assert_allclose(r[0]['y'],2*np.sin(r[0]['x']))
    assert r[4]['value']==2

def test_implicit_inequality_and_wavelet():
    r=run('x^2+y^2=9','y<sin(x)','s=1','f(x)=(1-(x/s)^2)*exp(-(x/s)^2/2)/sqrt(s)','x=-4')
    assert not any('error' in x for x in r)
    assert r[0]['kind']=='implicit' and np.shape(r[0]['z'])==(180,180)
    assert set(np.unique(r[1]['z']))=={0,1}
    assert r[3]['kind']=='curve'
    assert r[4]['kind']=='implicit'

def test_complex_and_matrix_exponential_distinction():
    r=run('A=[[0,-1],[1,0]]','eigvals(A)','expm(A)','exp(A)','z=1+2*i','real(z)')
    assert not any('error' in x for x in r)
    assert any('i' in str(v) for v in r[1]['value'])
    assert not np.allclose(r[2]['value'],r[3]['value'])
    assert r[5]['value']==1

@pytest.mark.parametrize('text',[
 '__import__("os").system("echo bad")','(1).__class__','[n for n in [1,2]]',
 'open("file")','eye(100000)','2^100000','[[1,2],[3]]','inv([[1,2],[2,4]])',
 'A=[[]]','solve([[1,0],[0,1]],[1,2,3])','[[1,2]] @ [[1,2]]'
])
def test_invalid_or_unsafe_input(text):
    assert 'error' in run(text)[0]

def test_cycles_and_duplicates_are_local_errors():
    r=run('a=b','b=a','a=3','y=sin(x)')
    assert all('error' in x for x in r[:3])
    assert 'error' not in r[3]

def test_nonfinite_plot_values_serialize_as_null():
    r=run('y=1/(x-x)')[0]
    assert any(v is None for v in r['y'])

def test_api_and_assets():
    client=app.test_client()
    assert client.get('/').status_code==200
    assert client.get('/static/app.js').status_code==200
    assert client.get('/static/style.css').status_code==200
    assert client.get('/static/plotly.min.js').status_code==200
    r=client.post('/api/evaluate',json={'expressions':[{'text':'A=[[2,1],[1,3]]'},{'text':'det(A)'}]})
    assert r.status_code==200 and r.json['results'][1]['value']==pytest.approx(5)
    assert client.post('/api/evaluate',json={'bounds':[0,0,0,0]}).status_code==400
    assert client.post('/api/evaluate',json={'expressions':[{'text':'1'}]*41}).status_code==400
    assert client.post('/api/evaluate',json=[]).status_code==400

def test_matrix_results_remain_matrices_and_grid_powers_are_entrywise():
    r=run('A=[[2,0],[0,3]]','inv(A)^2','expm(A)^0','A[0]^2','y=x^2','x*y=1')
    assert not any('error' in v for v in r)
    np.testing.assert_allclose(r[1]['value'],[[.25,0],[0,1/9]])
    np.testing.assert_allclose(r[2]['value'],np.eye(2))
    np.testing.assert_allclose(r[3]['value'],[4,0])
    np.testing.assert_allclose(r[4]['y'],np.array(r[4]['x'])**2)
    assert r[5]['kind']=='implicit'

def test_imaginary_notation_and_principal_branches():
    r=run('2+3i','2+3j','i^2','j^2','sqrt(-1)','log(-1)','(-1)^0.5','1e-3i','asin(2)')
    assert not any('error' in v for v in r)
    assert r[0]['real']==2 and r[0]['imag']==3
    assert r[1]['imag']==3
    assert r[2]['value']==-1 and r[3]['value']==-1
    assert r[4]['imag']==pytest.approx(1)
    assert r[5]['imag']==pytest.approx(np.pi)
    assert r[6]['imag']==pytest.approx(1)
    assert r[7]['imag']==pytest.approx(.001)
    assert r[8]['complex']

def test_polar_roots_and_inner_product():
    r=run('polar(2,pi/2)','cis(pi)','arg(1+i)','roots(1,4)','inner([1,i],[1,i])','arg(0)')
    assert r[0]['imag']==pytest.approx(2)
    assert r[1]['real']==pytest.approx(-1)
    assert r[2]['value']==pytest.approx(np.pi/4)
    z=np.array(r[3]['real'])+1j*np.array(r[3]['imag'])
    np.testing.assert_allclose(z**4,1,atol=1e-12)
    assert r[4]['value']==2
    assert 'error' in r[5]

def test_hermitian_unitary_and_complex_heatmap_channels():
    r=run('A=[[2,i],[-i,3]]','H(A)','U=expm(i*A)','isunitary(U)','ishermitian(A)','H(U)@U','sqrtm(A)')
    assert not any('error' in v for v in r)
    assert r[0]['hermitian'] and r[0]['imag'][0][1]==1
    assert r[0]['magnitude'][1][0]==1
    assert r[0]['phase'][0][1]==pytest.approx(np.pi/2)
    assert r[3]['value']==1 and r[4]['value']==1
    np.testing.assert_allclose(r[5]['real'],np.eye(2),atol=1e-12)
    root=np.array(r[6]['real'])+1j*np.array(r[6]['imag'])
    np.testing.assert_allclose(root@root,[[2,1j],[-1j,3]],atol=1e-12)

def test_complex_curves_and_domain_maps():
    r=Calculator([{'text':'f(t)=exp(i*t)'}]).run([-3,3,-3,3],curve_range=[0,2*np.pi])[0]
    assert r['kind']=='complex_curve'
    np.testing.assert_allclose(r['y'],np.cos(r['x']),atol=1e-12)
    np.testing.assert_allclose(r['imag'],np.sin(r['x']),atol=1e-12)
    r=Calculator([{'text':'f(z)=z^2'}]).run([-3,3,-3,3],complex_domain=True)[0]
    assert r['kind']=='complex_field'
    xx,yy=np.meshgrid(r['x'],r['y']);z=(xx+1j*yy)**2
    np.testing.assert_allclose(r['magnitude'],np.abs(z))
    np.testing.assert_allclose(r['phase'],np.angle(z))

def test_complex_invalid_ordering_and_input_validation():
    for text in ['i < 2','polar(-1,2)','roots(1,100)','inner([[1,i]],[[1,i]])']:
        assert 'error' in run(text)[0]
    c=app.test_client()
    assert c.post('/api/evaluate',json={'complex_domain':'yes'}).status_code==400
    assert c.post('/api/evaluate',json={'curve_range':[2,1]}).status_code==400
    r=c.post('/api/evaluate',json={'expressions':[{'text':'f(z)=sqrt(z)'}],'complex_domain':True})
    assert r.status_code==200 and r.json['results'][0]['kind']=='complex_field'

def test_tiny_imaginary_components_are_preserved():
    r=run('1e-15i','A=[[1e-15i]]')
    assert r[0]['imag']==1e-15 and r[0]['complex']
    assert r[1]['imag']==[[1e-15]] and r[1]['complex']

def test_entire_greek_alphabet_and_variants():
    from symbols import GREEK_LETTERS, GREEK_VARIANTS
    assert len(GREEK_LETTERS)==24
    for _,lower,upper in GREEK_LETTERS:
        for letter in (lower,upper):
            if letter=='π':
                assert run(letter)[0]['value']==pytest.approx(np.pi)
            else:
                r=run(f'{letter}=2',f'{letter}+3')
                assert r[1].get('value')==5, (letter,r)
    for _,variant,canonical in GREEK_VARIANTS:
        if canonical=='π':assert run(variant)[0]['value']==pytest.approx(np.pi)
        else:
            r=run(f'{variant}=3',f'{canonical}^2')
            assert r[1].get('value')==9,(variant,r)

def test_greek_functions_matrices_sliders_and_names():
    r=run('α=2','β=3','ψ(θ)=α*exp(i*θ)','Α=[[α,i],[-i,β]]','H(Α)','ζ=2+3i','ι=4','ι+i','απ=7','απ')
    assert not any('error' in v for v in r)
    assert r[0]['numeric']==2
    assert r[2]['kind']=='complex_curve'
    assert r[3]['hermitian']
    assert r[5]['imag']==3
    assert r[7]['real']==4 and r[7]['imag']==1
    assert r[9]['value']==7
    assert 'error' in run('π=3')[0]
    assert 'error' in run('φ=2','ϕ=3')[1]
    c=app.test_client();r=c.get('/api/symbols')
    assert r.status_code==200 and len(r.json['letters'])==24
    r=c.post('/api/evaluate',json={'expressions':[{'text':'ψ(ζ)=ζ^2'}],'complex_domain':True})
    assert r.json['results'][0]['kind']=='complex_field'

def test_two_argument_definitions_calls_and_slices():
    r=run('f(x,y)=x^2+2*y','f(2,3)','f(x,1)','g(t)=f(t,2)','f(x,y)=0')
    assert r[0]['kind']=='surface'
    assert r[0]['function']['parameters']==['x','y']
    assert r[1]['value']==10
    np.testing.assert_allclose(r[2]['y'],np.array(r[2]['x'])**2+2)
    np.testing.assert_allclose(r[3]['y'],np.array(r[3]['x'])**2+4)
    assert 'error' in r[4]

def test_two_argument_greek_surface_and_complex_components():
    r=run('ψ(α,β)=α+i*β','ψ(2,3)','ψ(x,y)')
    assert r[0]['kind']=='surface' and r[0]['parameters']==['α','β']
    xx,yy=np.meshgrid(r[0]['x'],r[0]['y'])
    np.testing.assert_allclose(r[0]['real'],xx)
    np.testing.assert_allclose(r[0]['imag'],yy)
    np.testing.assert_allclose(r[0]['magnitude'],np.abs(xx+1j*yy))
    assert r[1]['real']==2 and r[1]['imag']==3
    assert r[2]['kind']=='surface'

def test_subscript_names_and_superscripts_preserve_meaning():
    r=run('a₁=2','a1=9','a_1+a1','f₁(x₁,x₂)=x₁²+x₂²','f_{1}(3,4)','2⁻²','(-1)^{1/2}','n=3','2ⁿ','A₁=[[1,2],[3,4]]','A_1[0,1]')
    assert not any('error' in v for v in r)
    assert r[2]['value']==11
    assert r[3]['function']['name']=='f_1'
    assert r[4]['value']==25
    assert r[5]['value']==pytest.approx(.25)
    assert r[6]['imag']==pytest.approx(1)
    assert r[8]['value']==8
    assert r[10]['value']==2

def test_subscript_greek_aliases_and_duplicate_arguments():
    assert run('α₁=2','α_{1}^2')[1]['value']==4
    assert 'error' in run('x₁=2','x_1=3')[1]
    for text in ['f(x,x)=x','f(φ,ϕ)=φ','f()=1','f(x,)=x','f(π,y)=y','f(x²,y)=y']:
        assert 'error' in run(text)[0],text
    r=run('f(x,y)=x+y','f(2)','f(1,2,3)')
    assert 'expects 2' in r[1]['error'] and 'expects 2' in r[2]['error']

def test_nested_functions_and_complex_two_argument_call():
    r=run('f(x)=x^2','g(x,y)=f(y)+x','g(2,3)','g(1+i,2-i)')
    assert r[2]['value']==11
    assert r[3]['real']==pytest.approx(4) and r[3]['imag']==pytest.approx(-3)

def test_two_argument_api_and_zero_level_equations():
    client=app.test_client()
    r=client.post('/api/evaluate',json={'expressions':[{'text':'f₁(x₁,x₂)=x₁²-x₂²'},{'text':'f_1(3,2)'},{'text':'(f_1(x,y))=0'}]})
    assert r.status_code==200
    assert r.json['results'][0]['kind']=='surface'
    assert r.json['results'][1]['value']==5
    assert r.json['results'][2]['kind']=='implicit'

def test_numerical_derivatives_and_partial_surfaces():
    r=run('f(x)=x^3','diff(f(x),x,2)','diff(sin(x),x)','diff(x^3,x,2,2)','g(x,y)=x^2*y+sin(y)','diff(g(x,y),x)')
    assert not any('error' in v for v in r),r
    assert r[1]['value']==pytest.approx(12,abs=1e-8)
    np.testing.assert_allclose(r[2]['y'],np.cos(r[2]['x']),atol=1e-8)
    assert r[3]['value']==pytest.approx(12,abs=1e-6)
    xx,yy=np.meshgrid(r[5]['x'],r[5]['y'])
    np.testing.assert_allclose(r[5]['real'],2*xx*yy,atol=1e-7)
    assert r[1]['calculus'][0]['operation']=='derivative'

def test_integrals_bind_variable_and_plot_upper_limit():
    r=run('integrate(x^2,x,0,1)','integrate(sin(t),t,0,pi)','integrate(t^2,t,0,x)','integrate(x^2,x,1,0)','integrate(1/x,x,2,2)')
    assert not any('error' in v for v in r),r
    assert r[0]['kind']=='scalar' and r[0]['value']==pytest.approx(1/3,abs=1e-10)
    assert r[1]['value']==pytest.approx(2,abs=1e-10)
    np.testing.assert_allclose(r[2]['y'],np.array(r[2]['x'])**3/3,atol=1e-9)
    assert r[3]['value']==pytest.approx(-1/3,abs=1e-10)
    assert r[4]['value']==0
    assert r[0]['calculus'][0]['error_estimate']<1e-8

def test_complex_and_matrix_calculus():
    r=run('integral(exp(i*t),t,0,pi)','derivative(exp(i*x),x,0)','A=[[1,0],[0,2]]','diff(expm(t*A),t,0)','integrate(t*A,t,0,1)')
    assert not any('error' in v for v in r),r
    assert r[0]['real']==pytest.approx(0,abs=1e-10) and r[0]['imag']==pytest.approx(2,abs=1e-10)
    assert r[1]['imag']==pytest.approx(1,abs=1e-8)
    np.testing.assert_allclose(r[3]['real'],[[1,0],[0,2]],atol=1e-8)
    np.testing.assert_allclose(r[4]['real'],[[.5,0],[0,1]],atol=1e-10)

def test_calculus_greek_subscripts_and_nested_integrals():
    r=run('f₁(θ₁,θ₂)=θ₁²+θ₂','g(θ₂)=integrate(f_1(θ_1,θ_2),θ_1,0,1)','g(2)','diff(θ₁³,θ₁,2)','integrate(integrate(x*y,y,0,1),x,0,1)')
    assert not any('error' in v for v in r),r
    assert r[2]['value']==pytest.approx(7/3,abs=1e-9)
    assert r[3]['value']==pytest.approx(12,abs=1e-8)
    assert r[4]['value']==pytest.approx(.25,abs=1e-10)

def test_calculus_invalid_inputs_and_cusp():
    for text in ['diff(abs(x),x,0)','diff(x,x,1,3)','diff(x,1)','diff(x,x,1,1,-1)','integrate(x,x,0,i)','integrate(1/x,x,-1,1)','integrate(x,x,0)','integrate=3']:
        assert 'error' in run(text)[0],text

def test_calculus_api_and_fundamental_theorem():
    client=app.test_client()
    r=client.post('/api/evaluate',json={'expressions':[{'text':'diff(integrate(t^2,t,0,x),x,2)'}]})
    assert r.status_code==200
    assert r.json['results'][0]['value']==pytest.approx(4,abs=1e-7)

def test_mixed_partial_and_bound_shadowing():
    r=run('f(x,y)=x^2*y^3','h(x,y)=diff(diff(f(x,y),x),y)','h(2,3)','x_1=9','integrate(x_1^2,x_1,0,1)','x_1')
    assert not any('error' in v for v in r),r
    assert r[2]['value']==pytest.approx(108,abs=1e-5)
    assert r[4]['value']==pytest.approx(1/3,abs=1e-10)
    assert r[5]['value']==9

def test_adaptive_integral_endpoint_and_invalid_step():
    r=run('integrate(1/sqrt(x),x,0,1)','diff(x^2,x,2,1,0.001)')
    assert r[0]['value']==pytest.approx(2,abs=1e-6)
    assert r[1]['value']==pytest.approx(4,abs=1e-8)

def test_matrix_vector_multiplication_and_products():
    r=run('A=[[1,2],[3,4]]','v=[2,1]','A*v','v*A','A@v','matmul(v,A)','dot([1,i],[1,i])','inner([1,i],[1,i])','outer([1,i],[1,i])','bra([1,i])@col([1,i])','[1,2]*[3,4]')
    assert not any('error' in x for x in r),r
    np.testing.assert_allclose(r[2]['value'],[4,10])
    np.testing.assert_allclose(r[3]['value'],[5,8])
    np.testing.assert_allclose(r[4]['value'],r[2]['value'])
    np.testing.assert_allclose(r[5]['value'],r[3]['value'])
    assert r[6]['value']==0 and r[7]['value']==2
    assert r[8]['imag']==[[0,1],[1,0]] and r[8]['real']==[[1,0],[0,-1]]
    assert r[9]['value']==[[2]] and r[10]['value']==[3,8]

def test_qubit_normalization_and_born_probabilities():
    r=run('ψ=qubit(1,i)','probabilities(ψ)','bloch(ψ)','density(ψ)','qubit(0,0)')
    assert r[0]['quantum']['qubits']==1
    np.testing.assert_allclose(r[1]['value'],[.5,.5])
    np.testing.assert_allclose(r[2]['value'],[0,1,0],atol=1e-12)
    assert r[3]['quantum']['purity']==pytest.approx(1)
    assert 'error' in r[4]

def test_gates_and_rotations_preserve_norm():
    r=run('hadamard() * ket0()','pauliX() @ ket0()','Ry(pi) @ ket0()','Rz(pi) @ qubit(1,1)','Rx(pi/3)','isunitary(Rx(pi/3))','H(hadamard()) @ hadamard()')
    assert not any('error' in x for x in r),r
    np.testing.assert_allclose(r[0]['quantum']['bloch'],[1,0,0],atol=1e-12)
    np.testing.assert_allclose(r[1]['value'],[0,1])
    np.testing.assert_allclose(r[2]['quantum']['probabilities'],[0,1],atol=1e-12)
    np.testing.assert_allclose(r[3]['quantum']['bloch'],[-1,0,0],atol=1e-12)
    assert r[5]['value']==1
    np.testing.assert_allclose(r[6]['real'],np.eye(2),atol=1e-12)

def test_bell_state_tensor_order_and_reductions():
    r=run('ψ=CNOT() @ tensor(hadamard() @ ket0(),ket0())','probabilities(ψ)','reduced(ψ,0)','reduced(ψ,1)','entropy(reduced(ψ,0))','tensor(ket0(),ket1())','basis(1,2)')
    assert not any('error' in x for x in r),r
    assert r[0]['quantum']['qubits']==2 and r[0]['quantum']['bloch'] is None
    np.testing.assert_allclose(r[1]['value'],[.5,0,0,.5],atol=1e-12)
    for k in [2,3]:np.testing.assert_allclose(r[k]['real'],np.eye(2)/2,atol=1e-12)
    assert r[4]['value']==pytest.approx(1)
    assert r[5]['value']==[0,1,0,0] and r[6]['value']==r[5]['value']

def test_mixed_qubit_and_hamiltonian_evolution():
    r=run('ρ=eye(2)/2','bloch(ρ)','purity(ρ)','ψ=blochstate(pi/2,0)','expect(pauliZ(),ψ)','evolve(ψ,pauliZ(),pi/2)','fidelity(ket0(),ket1())','evolve(ρ,pauliY(),1)')
    assert not any('error' in x for x in r),r
    np.testing.assert_allclose(r[1]['value'],[0,0,0],atol=1e-12)
    assert r[2]['value']==pytest.approx(.5)
    assert r[4]['real']==pytest.approx(0,abs=1e-12)
    np.testing.assert_allclose(r[5]['quantum']['bloch'],[-1,0,0],atol=1e-12)
    assert r[6]['value']==0
    np.testing.assert_allclose(r[7]['real'],np.eye(2)/2,atol=1e-12)

def test_quantum_validation_and_bounded_tensor():
    for expr in ['probabilities([1,1])','density([[1,2],[0,0]])','density([[2,0],[0,-1]])','state([1,0,0])','basis(0,6)','tensor(eye(8),eye(8))','reduced(ket0(),1)','evolve(ket0(),[[1,1],[0,1]],1)','bloch(basis(0,2))','[[1,2]] * [1,2,3]']:
        assert 'error' in run(expr)[0],expr

def test_gate_state_columns_and_five_qubit_register():
    r=run('ψ=state(basis(17,5))','reduced(ψ,0)','reduced(ψ,4)','col(ket0())','pauliX()*col(ket0())','tensor(pauliX(),eye(2)) * basis(0,2)')
    assert not any('error' in x for x in r),r
    assert r[0]['quantum']['qubits']==5
    for k in [1,2]:assert r[k]['quantum']['probabilities']==[0,1]
    assert r[4]['value']==[[0],[1]]
    assert r[5]['value']==[0,0,1,0]

def test_quantum_api_metadata_and_existing_conjugate_transpose():
    c=app.test_client();r=c.post('/api/evaluate',json={'expressions':[{'text':'ψ=qubit(1,i)'},{'text':'pauliY()*ψ'},{'text':'H([[i,0],[0,1]])'}]})
    assert r.status_code==200
    assert r.json['results'][1]['quantum']['probabilities']==pytest.approx([.5,.5])
    assert r.json['results'][2]['imag']==[[-1,0],[0,0]]
