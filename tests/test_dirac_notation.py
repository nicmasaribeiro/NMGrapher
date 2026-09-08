import ast
import numpy as np
import pytest

from app import app
from engine import Calculator, parse
from math_preview import preview
from notation import normalize_notation


def value(text, *definitions):
    c=Calculator([{'text':s} for s in (*definitions,text)])
    assert not any(item.get('error') for item in c.items), c.items
    return c.evaluate(c.items[-1]['tree'],{})


def leaves(node):
    return str(node.get('text',''))+''.join(leaves(c) for c in node.get('children',[]))


@pytest.mark.parametrize('text,index,qubits',[
    ('|0⟩',0,1),('|1>',1,1),('|01⟩',1,2),('|1 0〉',2,2),('|00001⟩',1,5)])
def test_basis_keeps_bit_width_and_column_shape(text,index,qubits):
    actual=value(text);expected=np.zeros((2**qubits,1));expected[index]=1
    np.testing.assert_array_equal(actual,expected)


@pytest.mark.parametrize('label,phase',[('+',1),('-',-1),('−',-1),('+i',1j),('-i',-1j)])
def test_superposition_kets(label,phase):
    np.testing.assert_allclose(value('|'+label+'⟩'),np.array([[1],[phase]])/np.sqrt(2))


def test_named_greek_ket_definitions_forward_references_and_no_normalization():
    np.testing.assert_allclose(value('|psi_1>', '|ψ_1⟩=2|0⟩+3i|1⟩'),[[2],[3j]])
    np.testing.assert_allclose(value('|ψ⟩','|ψ⟩=|φ⟩','|φ⟩=[1,i]'),[[1],[1j]])
    np.testing.assert_allclose(value('ψ','|ψ⟩=[1,i]'),[[1],[1j]])
    assert value('⟨ψ|ψ⟩','|ψ⟩=[1,i]')==pytest.approx(2)
    result=Calculator([{'text':'|ψ⟩=2|0⟩'},{'text':'probabilities(|ψ⟩)'}]).run([-1,1,-1,1])
    assert 'quantum' not in result[0]
    assert 'norm 1' in result[1]['error']


@pytest.mark.parametrize('notation',['⟨φ|ψ⟩','<phi|psi>','⟨φ| |ψ⟩','⟨φ| @ |ψ⟩'])
def test_bra_ket_conjugates_first_argument(notation):
    assert value(notation,'φ=[1,i]','ψ=[1,1]')==pytest.approx(1-1j)


@pytest.mark.parametrize('notation',['|ψ⟩⟨φ|','|psi><phi|','|ψ⟩ @ ⟨φ|','|ψ⟩ * ⟨φ|'])
def test_outer_product_conjugates_bra_and_does_not_normalize(notation):
    np.testing.assert_allclose(value(notation,'ψ=[1,i]','φ=[1,-i]'),[[1,1j],[1j,-1]])


def test_bra_rows_operators_and_general_matrix_elements():
    np.testing.assert_array_equal(value('⟨ψ|','ψ=[1,i]'),[[1,-1j]])
    np.testing.assert_allclose(value('hadamard()|0⟩'),np.array([[1],[1]])/np.sqrt(2))
    assert value('⟨ψ|pauliY()|ψ⟩','|ψ⟩=(|0⟩+i|1⟩)/sqrt(2)')==pytest.approx(1)
    assert value('⟨0|A|1⟩','A=[[0,2+i],[0,0]]')==pytest.approx(2+1j)
    np.testing.assert_allclose(value('|0⟩(2+i)'),[[2+1j],[0]])


def test_tensor_order_bell_state_and_register_limits():
    for expr in ('|0⟩|1⟩','|0⟩ ⊗ |1⟩','tensor(|0⟩,|1⟩)'):
        np.testing.assert_array_equal(value(expr),value('|01⟩'))
    np.testing.assert_array_equal(value('|0⟩|1⟩|0⟩'),value('|010⟩'))
    np.testing.assert_allclose(value('probabilities((|00⟩+|11⟩)/sqrt(2))'),[.5,0,0,.5])
    with pytest.raises(ValueError):value('|00000⟩|0⟩')


def test_ket_functions_calculus_and_scalar_expectation_curves():
    rows=['|ψ(t)⟩=cos(t)|0⟩+sin(t)|1⟩','E(t)=⟨ψ(t)|pauliZ()|ψ(t)⟩',
          '|ψ(0)⟩','diff(|ψ(t)⟩,t,0)','integrate(|ψ(t)⟩,t,0,pi/2)']
    c=Calculator([{'text':s} for s in rows]);r=c.run([-1,1,-1,1])
    assert not any(x.get('error') for x in r),r
    assert r[0]['shape']==[2,1]
    np.testing.assert_allclose(r[1]['y'],np.cos(2*np.array(r[1]['x'])),atol=1e-12)
    np.testing.assert_allclose(r[2]['value'],[[1],[0]])
    np.testing.assert_allclose(r[3]['value'],[[0],[1]],atol=1e-8)
    np.testing.assert_allclose(r[4]['value'],[[1],[1]],atol=1e-7)


@pytest.mark.parametrize('text',[
    '|2⟩','|000000⟩','|⟩','|ψ','⟨ψ','|0⟩=[1,0]', '|ψ⟩=3',
    '|ψ⟩=[[1,0],[0,1]]','|[1,2,3]⟩','⟨0|00⟩',
    '⟨0|eye(4)|0⟩','|__import__("os").system("bad")⟩',
    '|(1).__class__⟩','|[x for x in [1,2]]⟩'])
def test_invalid_and_unsafe_kets_are_local_row_errors(text):
    result=Calculator([{'text':text},{'text':'2+3'}]).run([-1,1,-1,1])
    assert result[0].get('error'),result
    assert result[1]['value']==5


def test_plain_comparisons_and_notes_remain_unchanged():
    for text in ('x<1','x>1','x<=1','1<x','where(x<0,-1,1)'):
        assert isinstance(parse(text),(ast.Compare,ast.Call))
    rows=[{'type':'note','text':'|not finished alpha'},{'text':'2+3'}]
    result=Calculator(rows).run([-1,1,-1,1])
    assert result[0]=={'text':rows[0]['text'],'kind':'note'}
    assert result[1]['value']==5


def test_mathml_preview_preserves_labels_and_ket_definition():
    cases={'|01⟩':'|01⟩','|ψ⟩=|+⟩':'|ψ⟩=|+⟩','⟨φ|ψ⟩':'⟨φ|ψ⟩',
           '|ψ⟩⟨φ|':'|ψ⟩⟨φ|','⟨ψ|A|ψ⟩':'⟨ψ|A|ψ⟩',
           '|0⟩ ⊗ |1⟩':'|0⟩⊗|1⟩'}
    for source,expected in cases.items():assert leaves(preview(source)['tree'])==expected
    assert 'ketbasis' in leaves(preview('ketbasis(1,100000000)')['tree'])
    for source in cases:assert normalize_notation(normalize_notation(source))==normalize_notation(source)


def test_http_preview_evaluation_metadata_and_ui_palette():
    client=app.test_client()
    rows=[{'text':'|ψ⟩=(|0⟩+i|1⟩)/sqrt(2)'},{'text':'⟨ψ|pauliY()|ψ⟩'}]
    response=client.post('/api/evaluate',json={'expressions':rows})
    assert response.status_code==200
    assert response.json['results'][0]['quantum']['qubits']==1
    assert response.json['results'][1]['value']==pytest.approx(1)
    response=client.post('/api/evaluate',json={'expressions':[{'text':'|ψ(t)⟩=cos(t)|0⟩+sin(t)|1⟩'}],'validate_only':True})
    assert response.json['results'][0]['function']['name']=='ψ'
    response=client.post('/api/preview',json={'expressions':[r['text'] for r in rows]})
    assert all('tree' in p for p in response.json['previews'])
    html=client.get('/').text
    assert 'Ket / Dirac notation' in html and 'Dirac notation is used for display' not in html


def test_kets_in_parallel_background_jobs():
    import time
    from app import evaluation_payload
    from async_compute import JobManager
    manager=JobManager(workers=2)
    try:
        payload=evaluation_payload({'expressions':[{'text':'⟨ψ|pauliY()|ψ⟩'},
            {'text':'|ψ⟩=(|0⟩+i|1⟩)/sqrt(2)'}]})
        payload['graphs']=[]
        job=manager.submit(payload)
        deadline=time.monotonic()+40
        while time.monotonic()<deadline:
            snapshot=manager.poll(job['job_id'])
            if snapshot['state']!='running':break
            time.sleep(.02)
        assert snapshot['state']=='complete',snapshot
        results={event['index']:event['result'] for event in snapshot['results']}
        assert results[0]['value']==pytest.approx(1)
        assert results[1]['quantum']['qubits']==1
    finally:
        manager.close(wait=True)
