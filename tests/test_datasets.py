import copy
import numpy as np
import pytest
from app import app
from engine import Calculator
from datasets import parse_delimited, validate_datasets, DatasetError, MAX_IMPORT_BYTES


def dataset(values=None):
    values=[0,2,None,6] if values is None else values
    return {'id':'d1','name':'data_1','columns':[{'name':'time','label':'Time','values':list(range(len(values)))},{'name':'value','label':'Value','values':values}], 'x':'time','y':['value'],'style':'lines','visible':True}


def evaluate(*texts,data=None):
    return Calculator([{'text':t} for t in texts],datasets=[dataset() if data is None else data]).run([-2,2,-2,2])


def test_csv_bom_quotes_blank_cells_and_text_columns():
    p=parse_delimited('\ufeff"Time","Value","Note"\r\n0,1,"a,b"\r\n1,,"two\nlines"\r\n2,3,ok\r\n')
    assert p['rows']==3 and p['columns'][0]['values']==[0,1,2]
    assert p['columns'][1]['values']==[1,None,3] and p['columns'][1]['missing']==1
    assert not p['columns'][2]['numeric'] and p['columns'][2]['invalid']==3
    assert p['preview'][1][2]=='two\nlines'


def test_delimiters_decimal_comma_no_header_and_duplicate_names():
    p=parse_delimited('0\t1\n1\t2',header=False)
    assert p['delimiter']=='\t' and p['columns'][0]['name']=='column_1'
    p=parse_delimited('time;price\n0;1,5\n1;2,75',delimiter=';',decimal=',')
    assert p['columns'][1]['values']==[1.5,2.75]
    p=parse_delimited('alpha,α,Price ($)\n1,2,3')
    assert [c['name'] for c in p['columns']]==['α','α_2','Price']


@pytest.mark.parametrize('text',[',,\n,,','a,b\n1','a,b\n1,2,3','a,b\n"unterminated,2','header',''])
def test_malformed_and_empty_files(text):
    with pytest.raises(DatasetError):parse_delimited(text)


def test_preview_limits_and_nonfinite_values():
    with pytest.raises(DatasetError):parse_delimited('0\n'*10001,header=False)
    with pytest.raises(DatasetError):parse_delimited('x'*(MAX_IMPORT_BYTES+1))
    with pytest.raises(DatasetError):parse_delimited(','.join(['1']*33),header=False)
    p=parse_delimited('a,b,c\nNaN,inf,1e101')
    assert not any(c['numeric'] for c in p['columns'])


def test_large_column_statistics_transformations_and_missing_values():
    d=dataset(list(range(1000)))
    r=evaluate('data_1_value','mean(data_1_value)','f(t)=2*t+1','f(data_1_value)','std(data_1_value)','points(data_1_time,f(data_1_value))',data=d)
    assert not any(a.get('error') for a in r)
    assert r[0]['kind']=='series' and r[0]['shape']==[1000] and len(r[0]['value'])==12
    assert r[1]['value']==pytest.approx(499.5)
    np.testing.assert_allclose(r[3]['real'],2*np.arange(1000)+1)
    assert r[4]['value']==pytest.approx(np.std(np.arange(1000)))
    assert r[5]['kind']=='data_plot' and r[5]['x'][-1]==999 and r[5]['y'][-1]==1999
    r=evaluate('mean(data_1_value)','count(data_1_value)','mean(dropna(data_1_value))','median(dropna(data_1_value))','data_1_value*i')
    assert 'error' in r[0] and r[1]['value']==3
    assert r[2]['value']==pytest.approx(8/3) and r[3]['value']==2
    assert r[4]['real'][2] is None and r[4]['imag'][2] is None


def test_points_keep_row_alignment_and_do_not_sort():
    d=dataset([2,None,4]);d['columns'][0]['values']=[5,3,None]
    r=evaluate('points(data_1_time,data_1_value)',data=d)[0]
    assert r['x']==[5,None,None] and r['y']==[2,None,None]
    assert evaluate('points(data_1_time,[1,2])')[0]['error']


def test_interpolation_and_calculus_over_complete_dataset():
    r=evaluate('f(t)=interp(t,data_1_time,data_1_value)','f(1.5)','integrate(f(t),t,0,3)','f(5)',data=dataset([0,2,4,6]))
    assert r[1]['value']==pytest.approx(3) and r[2]['value']==pytest.approx(9)
    assert 'error' in r[3]
    assert any(v is None for v in r[0]['y'])
    d=dataset([0,2,4]);d['columns'][0]['values']=[0,0,1]
    assert 'strictly increasing' in evaluate('interp(0.5,data_1_time,data_1_value)',data=d)[0]['error']


def test_collision_and_algebraic_matrix_limit_remain_clear():
    r=evaluate('data_1_value=2','mean(dropna(data_1_value))')
    assert 'already defined' in r[0]['error'] and r[1]['value']==pytest.approx(8/3)
    r=evaluate('matrix([data_1_time,data_1_value])',data=dataset(list(range(40))))
    assert 'error' in r[0]
    d=dataset();d['name']='mixed';d['columns']=[{'name':'diff','values':[1,2]}];d['x']=None;d['y']=['diff']
    with pytest.raises(DatasetError,match='reserved'):Calculator([],datasets=[d])


@pytest.mark.parametrize('mutation',[
    lambda d:d.update(columns=[]),lambda d:d.update(y=[]),lambda d:d.update(x='missing'),
    lambda d:d.update(name='not valid'),lambda d:d.update(style='bad'),lambda d:d.update(visible='yes'),
    lambda d:d['columns'][1].update(values=[1]),lambda d:d['columns'][1].update(values=[True,2,3,4]),
    lambda d:d['columns'][1].update(values=[None]*4),lambda d:d['columns'][1].update(values=[1,float('inf'),2,3]),
    lambda d:d['columns'][1].update(values=['1',2,3,4]),lambda d:d['columns'][1].update(name='time'),
])
def test_bad_dataset_payloads(mutation):
    d=dataset();mutation(d)
    res=app.test_client().post('/api/evaluate',json={'datasets':[d],'expressions':[]})
    assert res.status_code==400


def test_total_cells_duplicate_names_and_worksheet_roundtrip():
    d=dataset(list(range(10000)))
    ds=[copy.deepcopy(d) for _ in range(3)]
    for i,item in enumerate(ds):item['name']=f'd_{i}';item['id']=str(i)
    with pytest.raises(DatasetError,match='50,000'):validate_datasets(ds)
    with pytest.raises(DatasetError):validate_datasets([dataset(),dataset()])
    original=dataset();normalized,_=validate_datasets([original])
    assert normalized==[original]
    client=app.test_client()
    response=client.post('/api/datasets/preview',json={'text':'time,value\n0,1\n1,2','header':True})
    assert response.status_code==200 and response.get_json()['rows']==2
    response=client.post('/api/evaluate',json={'datasets':[original],'expressions':[{'text':'count(data_1_value)'}]})
    assert response.get_json()['results'][0]['value']==3
    assert client.post('/api/evaluate',json={'datasets':False,'expressions':[]}).status_code==400
    assert client.post('/api/datasets/preview',json={}).status_code==400
