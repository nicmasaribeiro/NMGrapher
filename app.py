"""Run this file in your IDE, then open http://127.0.0.1:5000."""
import math
from flask import Flask, jsonify, render_template, request
from engine import Calculator, parse, ExpressionError
import linear_algebra
from math_preview import preview
from symbols import symbol_catalog
from datasets import parse_delimited, DatasetError

app=Flask(__name__)
app.config['MAX_CONTENT_LENGTH']=2*1024*1024

@app.get('/')
def index():
    return render_template('index.html')

@app.get('/api/symbols')
def symbols():
    return jsonify(symbol_catalog())

@app.post('/api/evaluate')
def evaluate():
    payload=request.get_json(silent=True)
    if not isinstance(payload,dict):return jsonify(error='Send a JSON object.'),400
    rows=payload.get('expressions',[])
    if not isinstance(rows,list) or len(rows)>40 or any(not isinstance(r,dict) or not isinstance(r.get('text'),str) or len(r['text'])>1200 for r in rows):
        return jsonify(error='Use at most 40 expressions, each up to 1200 characters.'),400
    if any(r.get('plot_component', 'all') != 'all' and (type(r.get('plot_component')) is not int or not 0 <= r['plot_component'] < 1024) for r in rows):
        return jsonify(error='plot_component must be all or an entry index from 0 to 1023.'),400
    bounds=payload.get('bounds',[-10,10,-7,7])
    if not isinstance(bounds,list) or len(bounds)!=4 or any(type(v) not in (float,int) or not math.isfinite(v) or abs(v)>1e6 for v in bounds):
        return jsonify(error='Graph bounds must be four finite numbers within ±1,000,000.'),400
    if not 1e-6<bounds[1]-bounds[0]<=1e6 or not 1e-6<bounds[3]-bounds[2]<=1e6:
        return jsonify(error='Graph minimums must be smaller than maximums.'),400
    domain=payload.get('complex_domain',False)
    if type(domain) is not bool:return jsonify(error='complex_domain must be true or false.'),400
    curve_range=payload.get('curve_range')
    if curve_range is not None and (not isinstance(curve_range,list) or len(curve_range)!=2 or any(type(v) not in (int,float) or not math.isfinite(v) or abs(v)>1e4 for v in curve_range) or curve_range[1]-curve_range[0]<1e-6):
        return jsonify(error='Parameter range needs two increasing finite numbers within ±10,000.'),400
    try:
        datasets=payload.get('datasets',[])
        calculator=Calculator(rows,datasets=datasets)
        return jsonify(results=calculator.run(bounds,complex_domain=domain,curve_range=curve_range))
    except DatasetError as exc:
        return jsonify(error=str(exc)),400

@app.post('/api/wavelets')
def wavelet_analysis():
    import wavelets
    payload=request.get_json(silent=True)
    if not isinstance(payload,dict):return jsonify(error='Send a signal and wavelet options.'),400
    rows=payload.get('expressions',[])
    if not isinstance(rows,list) or len(rows)>40 or any(not isinstance(r,dict) or not isinstance(r.get('text'),str) or len(r['text'])>1200 for r in rows):
        return jsonify(error='Use at most 40 worksheet expressions of 1200 characters.'),400
    try:
        calculator=Calculator(rows,payload.get('datasets',[]))
        source=payload.get('signal');times=payload.get('time')
        def evaluate_source(value,label):
            if isinstance(value,str):
                if not 1<=len(value)<=1200:raise ValueError(label+' expression must contain 1–1200 characters.')
                return calculator.evaluate(parse(value))
            if isinstance(value,list) and 8<=len(value)<=10000 and all(v is None or type(v) in (float,int) for v in value):return value
            raise ValueError(label+' must be a numeric sample list or a worksheet expression.')
        values=evaluate_source(source,'Signal')
        time_values=evaluate_source(times,'Time') if times is not None and times!='' else None
        return jsonify(analysis=wavelets.analyze(values,time_values,payload.get('options')))
    except Exception as exc:return jsonify(error=str(exc) or 'Could not analyze this signal.'),400

@app.post('/api/probability')
def probability_analysis():
    import probability
    payload=request.get_json(silent=True)
    if not isinstance(payload,dict):return jsonify(error='Send a distribution expression and worksheet context.'),400
    rows=payload.get('expressions',[]);source=payload.get('distribution','')
    if not isinstance(rows,list) or len(rows)>40 or any(not isinstance(r,dict) or not isinstance(r.get('text'),str) or len(r['text'])>1200 for r in rows):
        return jsonify(error='Use at most 40 worksheet expressions of 1200 characters.'),400
    if not isinstance(source,str) or not 1<=len(source)<=1200:return jsonify(error='Enter a distribution expression of 1–1200 characters.'),400
    try:
        c=Calculator(rows,payload.get('datasets',[]));d=probability.distribution(c.evaluate(parse(source)))
        report=probability.describe(d)
        limits=payload.get('range')
        if limits is not None and (not isinstance(limits,list) or len(limits)!=2):raise ValueError('Use two plotting bounds.')
        report['plot']=probability.plot(d,*(limits or []))
        query=payload.get('query')
        if query is not None:
            if not isinstance(query,dict) or query.get('operation') not in ('pdf','pmf','cdf','sf','quantile','prob'):raise ValueError('Choose a supported probability calculation.')
            args=query.get('arguments',[])
            count=2 if query['operation']=='prob' else 1
            if not isinstance(args,list) or len(args)!=count or any(not isinstance(v,str) or not 1<=len(v)<=1200 for v in args):raise ValueError('Enter the required numeric expressions.')
            values=[c.evaluate(parse(v)) for v in args]
            # Studio queries are scalar; worksheet operators also support arrays.
            values=[probability.real(v,'Query argument') for v in values]
            value=float(probability.FUNCTIONS[query['operation']](d,*values))
            report['query']={'value':value if math.isfinite(value) else None,'nonfinite':not math.isfinite(value)}
        return jsonify(analysis=report)
    except Exception as exc:return jsonify(error=str(exc) or 'Could not analyze distribution.'),400

@app.post('/api/graphs')
def graphs():
    from graphing import graph_results
    payload = request.get_json(silent=True)
    if not isinstance(payload, dict): return jsonify(error='Send graph specifications and worksheet context.'), 400
    rows = payload.get('expressions', [])
    if not isinstance(rows, list) or len(rows) > 40 or any(not isinstance(r, dict) or not isinstance(r.get('text'), str) or len(r['text']) > 1200 for r in rows):
        return jsonify(error='Use at most 40 worksheet expressions of 1200 characters.'), 400
    try:
        return jsonify(results=graph_results(payload.get('graphs', []), rows, payload.get('datasets', [])))
    except (ValueError, ExpressionError) as exc:
        return jsonify(error=str(exc)), 400

@app.post('/api/linear-algebra')
def linear_algebra_analysis():
    payload=request.get_json(silent=True)
    if not isinstance(payload,dict):return jsonify(error='Send a matrix expression and worksheet context.'),400
    rows=payload.get('expressions',[]);expression=payload.get('matrix');rhs=payload.get('rhs','')
    if not isinstance(rows,list) or len(rows)>40 or any(not isinstance(r,dict) or not isinstance(r.get('text'),str) or len(r['text'])>1200 for r in rows):
        return jsonify(error='Use at most 40 worksheet expressions of 1200 characters.'),400
    if not isinstance(expression,str) or not 1<=len(expression)<=1200 or not isinstance(rhs,str) or len(rhs)>1200:
        return jsonify(error='Enter a matrix expression and an optional right-hand side, each up to 1200 characters.'),400
    try:
        calculator=Calculator(rows,payload.get('datasets',[]))
        value=calculator.evaluate(parse(expression))
        b=calculator.evaluate(parse(rhs)) if rhs.strip() else None
        return jsonify(analysis=linear_algebra.analyze(value,b))
    except (Exception,RecursionError) as exc:
        return jsonify(error=str(exc) or 'Could not analyze this matrix.'),400

@app.post('/api/preview')
def mathematical_preview():
    payload=request.get_json(silent=True)
    expressions=payload.get('expressions') if isinstance(payload,dict) else None
    if not isinstance(expressions,list) or len(expressions)>60 or any(not isinstance(s,str) or len(s)>3600 for s in expressions):
        return jsonify(error='Preview up to 60 expressions of at most 3600 characters.'),400
    previews=[]
    for source in expressions:
        try:previews.append(preview(source))
        except (Exception,RecursionError) as exc:previews.append({'error':str(exc) or 'Finish the expression to preview it.'})
    return jsonify(previews=previews)

@app.post('/api/datasets/preview')
def dataset_preview():
    payload=request.get_json(silent=True)
    if not isinstance(payload,dict):return jsonify(error='Send CSV text and import options.'),400
    try:
        return jsonify(parse_delimited(payload.get('text'),payload.get('delimiter','auto'),payload.get('header',True),payload.get('decimal','.')))
    except DatasetError as exc:
        return jsonify(error=str(exc)),400

@app.errorhandler(413)
def too_large(_):return jsonify(error='Request exceeds 2 MB; reduce the dataset size.'),413

if __name__=='__main__':
    app.run(host='127.0.0.1',port=5000,debug=False)
