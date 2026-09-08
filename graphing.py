"""Explicit, bounded graph specifications evaluated by the worksheet interpreter."""
import keyword
import re
import numpy as np
from engine import Calculator, parse, ExpressionError, FUNCTIONS, CONSTANTS, CALCULUS
from notation import normalize_notation
from sampling import sample_grid

TYPES = {'function', 'parametric', 'polar', 'parametric3d', 'implicit', 'surface', 'contour', 'scatter', 'line', 'bar', 'histogram', 'probability'}
GRID_TYPES = {'implicit', 'surface', 'contour'}
DATA_TYPES = {'scatter', 'line', 'bar', 'histogram'}
MAX_GRAPHS = 12


def validate_graphs(items):
    if not isinstance(items, list) or len(items) > MAX_GRAPHS:
        raise ValueError('Use at most 12 saved graphs.')
    ids = set()
    result = []
    for item in items:
        if not isinstance(item, dict): raise ValueError('Invalid graph specification.')
        g = dict(item)
        ident = g.get('id')
        if not isinstance(ident, str) or not re.fullmatch(r'[A-Za-z0-9_-]{1,80}', ident) or ident in ids or ident in ('2d','3d'):
            raise ValueError('Graph IDs must be unique letters, digits, underscores, or hyphens.')
        ids.add(ident)
        if not isinstance(g.get('type'),str) or g.get('type') not in TYPES: raise ValueError('Choose a supported graph type.')
        if not isinstance(g.get('name'), str) or not 1 <= len(g['name'].strip()) <= 80: raise ValueError('Graph names need 1–80 characters.')
        if not isinstance(g.get('color', '#2864d7'), str) or not re.fullmatch(r'#[0-9a-fA-F]{6}', g.get('color', '#2864d7')): raise ValueError('Choose a graph color.')
        if type(g.get('visible', True)) is not bool: raise ValueError('Invalid graph visibility.')
        for field in ['x', 'y', 'z', 'r', 'expression', 'values']:
            value = g.get(field, '')
            if not isinstance(value, str) or len(value) > 1200: raise ValueError('Graph formulas must be text up to 1200 characters.')
            g[field] = value.strip()
        g.setdefault('color', '#2864d7'); g.setdefault('visible', True)
        if g['type'] not in DATA_TYPES:
            parameter = g.get('parameter', 't')
            if not isinstance(parameter, str) or len(parameter) > 40: raise ValueError('Choose a valid parameter name.')
            parameter = normalize_notation(parameter.strip())
            if not parameter.isidentifier() or keyword.iskeyword(parameter) or parameter in set(FUNCTIONS) | set(CONSTANTS) | CALCULUS:
                raise ValueError('Parameter must be a name other than a reserved constant or function.')
            g['parameter'] = parameter
            for field, default in [('range', [-5, 5]), ('yrange', [-5, 5])]:
                value = g.get(field, default)
                if not isinstance(value, list) or len(value) != 2 or any(type(v) not in (int, float) or not np.isfinite(v) or abs(v) > 1e6 for v in value) or not 1e-6 <= value[1] - value[0] <= 1e6:
                    raise ValueError('Ranges need increasing finite bounds within ±1,000,000, with width 0.000001–1,000,000.')
                g[field] = value
            samples = g.get('samples', 400)
            if type(samples) is not int or not 50 <= samples <= 1000: raise ValueError('Use 50–1000 curve samples.')
            g['samples'] = samples
        if g['type'] == 'histogram':
            bins = g.get('bins', 20)
            if type(bins) is not int or not 1 <= bins <= 100: raise ValueError('Use 1–100 histogram bins.')
            g['bins'] = bins
        if g.get('probability_mode','density') not in ('density','cdf'): raise ValueError('Choose density/mass or cumulative probability.')
        result.append(g)
    return result


class Sampler:
    def __init__(self, calculator):
        self.calculator = calculator
        self.total = 0

    def value(self, tree, local):
        c = self.calculator
        c.steps = 0
        try:
            with np.errstate(all='ignore'): return c.evaluate(tree, local)
        finally:
            self.total += c.steps
            if self.total > 500000: raise ExpressionError('Graph sampling limit reached; reduce samples or simplify the formula.')

    def point(self, tree, local):
        try:
            a = np.asarray(self.value(tree, local), dtype=complex)
            if a.ndim: raise ExpressionError('Graph coordinates must be scalar. Select a vector or matrix entry, such as v(t)[0].')
            v = complex(a)
            if not np.isfinite(v) or abs(v.imag) > 1e-10 * max(1, abs(v.real)): return None
            return float(v.real)
        except (ZeroDivisionError, OverflowError, FloatingPointError):
            return None

    def series(self, source):
        a = np.asarray(self.value(parse(source), {}), dtype=complex)
        if a.ndim != 1 or not 1 <= len(a) <= 10000: raise ExpressionError('Use a vector or dataset column with 1–10,000 values.')
        if np.any(np.isfinite(a) & (np.abs(a.imag) > 1e-10 * np.maximum(1, np.abs(a.real)))):
            raise ExpressionError('Data charts need real values. Use real(...), imag(...), or abs(...).')
        return [float(v.real) if np.isfinite(v) else None for v in a]


def sample_graph(c, g):
    s = Sampler(c); kind = g['type']
    out = {'id': g['id'], 'type': kind, 'dimension': 3 if kind in {'surface', 'parametric3d'} else 2}
    if kind == 'probability':
        import probability
        d=probability.distribution(s.value(parse(g['expression']),{}))
        data=probability.plot(d,*g['range'])
        out.update(x=data['x'],y=data['cdf'] if g.get('probability_mode')=='cdf' else data['y'],discrete=d.discrete)
        return out
    if kind in DATA_TYPES:
        if kind == 'histogram':
            values = s.series(g['values']); finite = [v for v in values if v is not None]
            if not finite: raise ExpressionError('No finite values to plot.')
            counts, edges = np.histogram(finite, bins=g['bins'])
            out.update(x=((edges[:-1]+edges[1:])/2).tolist(), y=counts.tolist(), widths=np.diff(edges).tolist(), edges=edges.tolist(), omitted=len(values)-len(finite))
        else:
            y = s.series(g['y']); x = s.series(g['x']) if g['x'] else list(range(len(y)))
            if len(x) != len(y): raise ExpressionError('X and Y columns must have the same length.')
            valid = [a is not None and b is not None for a, b in zip(x, y)]
            if not any(valid): raise ExpressionError('No complete X/Y pairs to plot.')
            out.update(x=[a if ok else None for a, ok in zip(x, valid)], y=[b if ok else None for b, ok in zip(y, valid)], omitted=valid.count(False))
        return out
    if kind in GRID_TYPES:
        source = g['expression'] if kind == 'implicit' else g['z']
        if kind == 'implicit':
            sides = re.split(r'(?<![<>=!])=(?!=)', source)
            if len(sides) == 2: source = f'({sides[0]})-({sides[1]})'
            elif len(sides) > 2: raise ExpressionError('Use a single equality for an implicit curve.')
        tree = parse(source)
        count = 32 if c.contains_calculus(tree) else 60
        axes, values, sampling = sample_grid(c, lambda x, y: s.point(tree, {'x': x, 'y': y}),
                                             [g['range'], g['yrange']], count, 500000)
        xs, ys = axes
        count = len(xs)
        z = [values[k:k+count] for k in range(0, len(values), count)]
        valid = sum(v is not None for row in z for v in row)
        if not valid: raise ExpressionError('No finite real samples in this range. Choose another range or use real(...), imag(...), or abs(...).')
        out.update(x=xs.tolist(), y=ys.tolist(), z=z, gaps=count*count-valid, sampling=sampling)
        return out
    p = 'x' if kind == 'function' else g['parameter']
    fields = {'function': ['y'], 'parametric': ['x','y'], 'parametric3d': ['x','y','z'], 'polar': ['r']}[kind]
    trees = {field: parse(g[field]) for field in fields}
    axes, sampled, sampling = sample_grid(c, lambda t: {field: s.point(tree, {p: t}) for field, tree in trees.items()},
                                         [g['range']], g['samples'], 500000)
    ts = axes[0]
    coords = {key: [] for key in (['x','y','z'] if kind == 'parametric3d' else ['x','y'])}
    gaps = 0
    for t, values in zip(ts, sampled):
        if any(v is None for v in values.values()):
            for series in coords.values(): series.append(None)
            gaps += 1
            continue
        if kind == 'function': values['x'] = float(t)
        if kind == 'polar': values = {'x': values['r']*float(np.cos(t)), 'y': values['r']*float(np.sin(t))}
        for key in coords: coords[key].append(values[key])
    if gaps == len(ts): raise ExpressionError('No finite real samples in this range. Choose another range or use real(...), imag(...), or abs(...).')
    out.update(**coords, parameter=ts.tolist(), gaps=gaps, sampling=sampling)
    return out


def graph_results(graphs, rows, datasets):
    specs = validate_graphs(graphs)
    c = Calculator(rows, datasets)
    results = []
    for g in specs:
        if not g['visible']:
            results.append({'id':g['id'], 'hidden': True}); continue
        try: results.append(sample_graph(c, g))
        except Exception as exc: results.append({'id':g['id'], 'error':str(exc) or 'Could not sample this graph.'})
    return results
