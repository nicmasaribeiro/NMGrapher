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

def evaluation_payload(payload):
    """Shared validation for synchronous evaluation and background worksheet jobs."""
    if not isinstance(payload,dict):raise ValueError('Send a JSON object.')
    rows=payload.get('expressions',[])
    if not isinstance(rows,list) or len(rows)>40 or any(not isinstance(r,dict) or not isinstance(r.get('text'),str) or len(r['text'])>1200 for r in rows):
        raise ValueError('Use at most 40 expressions, each up to 1200 characters.')
    if any(r.get('plot_component', 'all') != 'all' and (type(r.get('plot_component')) is not int or not 0 <= r['plot_component'] < 1024) for r in rows):
        raise ValueError('plot_component must be all or an entry index from 0 to 1023.')
    if any(r.get('type','expression') not in ('expression','note','python') for r in rows):raise ValueError('Unknown worksheet cell type.')
    bounds=payload.get('bounds',[-10,10,-7,7])
    if not isinstance(bounds,list) or len(bounds)!=4 or any(type(v) not in (float,int) or not math.isfinite(v) or abs(v)>1e6 for v in bounds):
        raise ValueError('Graph bounds must be four finite numbers within ±1,000,000.')
    if not 1e-6<bounds[1]-bounds[0]<=1e6 or not 1e-6<bounds[3]-bounds[2]<=1e6:
        raise ValueError('Graph minimums must be smaller than maximums.')
    domain=payload.get('complex_domain',False)
    if type(domain) is not bool:raise ValueError('complex_domain must be true or false.')
    curve_range=payload.get('curve_range')
    if curve_range is not None and (not isinstance(curve_range,list) or len(curve_range)!=2 or any(type(v) not in (int,float) or not math.isfinite(v) or abs(v)>1e4 for v in curve_range) or curve_range[1]-curve_range[0]<1e-6):
        raise ValueError('Parameter range needs two increasing finite numbers within ±10,000.')
    return dict(expressions=rows,datasets=payload.get('datasets',[]),bounds=bounds,
                complex_domain=domain,curve_range=curve_range)


@app.post('/api/evaluate')
def evaluate():
    try:
        raw=request.get_json(silent=True)
        payload=evaluation_payload(raw)
        calculator=Calculator(payload['expressions'],datasets=payload['datasets'])
        indices=raw.get('indices')
        if indices is not None and (not isinstance(indices,list) or any(type(i) is not int or not 0<=i<len(payload['expressions']) for i in indices) or len(set(indices))!=len(indices)):
            raise ValueError('indices must be a list of unique existing row indices.')
        validate_only=raw.get('validate_only',False)
        if type(validate_only) is not bool:raise ValueError('validate_only must be true or false.')
        results=(calculator.metadata(indices) if validate_only else
                 calculator.run(payload['bounds'],complex_domain=payload['complex_domain'],curve_range=payload['curve_range'],indices=indices))
        return jsonify(results=results)
    except (DatasetError,ValueError) as exc:
        return jsonify(error=str(exc)),400


@app.after_request
def background_cache_policy(response):
    if request.path.startswith('/api/jobs'):
        response.headers['Cache-Control']='no-store'
    return response


@app.post('/api/jobs')
def start_job():
    from async_compute import manager, JobCapacityError
    from graphing import validate_graphs
    try:
        raw=request.get_json(silent=True)
        payload=evaluation_payload(raw)
        # Dataset and graph validation stays synchronous and inexpensive.
        calculator=Calculator(payload['expressions'],datasets=payload['datasets'])
        payload['graphs']=validate_graphs(raw.get('graphs',[]))
        return jsonify(manager.submit(payload,calculator)),202
    except JobCapacityError as exc:return jsonify(error=str(exc)),429
    except (DatasetError,ValueError) as exc:return jsonify(error=str(exc)),400


@app.get('/api/jobs/<ident>')
def poll_job(ident):
    from async_compute import manager, JobNotFound
    try:
        cursor=request.args.get('after','0')
        if not cursor.isascii() or not cursor.isdecimal() or len(cursor)>8:raise ValueError('Use a nonnegative integer result cursor.')
        return jsonify(manager.poll(ident,int(cursor)))
    except JobNotFound:return jsonify(error='Computation not found or expired. Recalculate the worksheet.'),404
    except ValueError as exc:return jsonify(error=str(exc)),400


@app.post('/api/jobs/<ident>/cancel')
def cancel_job(ident):
    from async_compute import manager, JobNotFound
    try:return jsonify(manager.cancel(ident))
    except JobNotFound:return jsonify(error='Computation not found or expired.'),404


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
