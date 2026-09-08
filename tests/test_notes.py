from engine import Calculator
from app import app


def test_notes_are_plain_text_and_never_create_definitions():
    note='  alpha = 999\nRemember: compare beta tomorrow <script>bad()</script>  '
    rows=[{'type':'note','text':note},{'text':'alpha=2'},{'text':'alpha+1'},
          {'type':'note','text':"__import__('os').system('bad')"}]
    r=Calculator(rows).run([-1,1,-1,1])
    assert r[0]=={'kind':'note','text':note}
    assert r[2]['value']==3 and r[3]['kind']=='note'
    assert not any(v.get('error') for v in r)


def test_notes_in_api_and_studio_context_do_not_shadow_math():
    client=app.test_client();rows=[{'type':'note','text':'a=999'},{'text':'a=2'}]
    r=client.post('/api/evaluate',json={'expressions':rows+[{'text':'a+1'}]})
    assert r.status_code==200 and r.json['results'][0]['kind']=='note'
    assert r.json['results'][-1]['value']==3
    r=client.post('/api/probability',json={'expressions':rows,'distribution':'normal(a,1)'})
    assert r.status_code==200 and r.json['analysis']['mean']==2
    r=client.post('/api/linear-algebra',json={'expressions':rows,'matrix':'[[a,0],[0,1]]'})
    assert r.status_code==200
    assert 'id="addNoteBtn"' in client.get('/').text


def test_note_length_uses_existing_worksheet_limits():
    client=app.test_client()
    assert client.post('/api/evaluate',json={'expressions':[{'type':'note','text':'a'*1201}]}).status_code==400
