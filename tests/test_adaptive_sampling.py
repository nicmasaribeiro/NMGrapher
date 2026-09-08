import numpy as np
import pytest
from engine import Calculator
from graphing import graph_results
from sampling import sample_grid
from app import app


def test_previously_over_budget_curve_keeps_full_domain_and_values():
    # The former 1,000-point loop exhausted its two-million-node budget.
    c = Calculator([{'text': 'f(t)=sum(t/k,k,1,500)'}])
    r = c.run([-2, 2, -10, 10])[0]
    assert 'error' not in r
    assert r['sampling']['reduced']
    assert 9 <= len(r['x']) < 1000
    assert r['x'][0] == -2 and r['x'][-1] == 2
    np.testing.assert_allclose(r['y'], np.array(r['x']) * sum(1/k for k in range(1, 501)))
    assert r['sampling']['evaluation_steps'] <= 2000000
    assert c.sampling_budget is None


def test_vector_integral_retains_complex_components_when_reduced():
    r = Calculator([{'text': 'F(t)=integrate([sum(s/k,k,1,15),i*s],s,0,t)'}]).run([-1, 1, -10, 10])[0]
    assert 'error' not in r
    assert r['sampling']['reduced']
    x = np.array(r['x'])
    np.testing.assert_allclose(r['components'][0]['y'], x*x/2*sum(1/k for k in range(1, 16)), atol=1e-10)
    np.testing.assert_allclose(r['components'][1]['imag'], x*x/2, atol=1e-10)


def test_reduced_matrix_surface_preserves_axes_fixed_inputs_and_selection():
    rows = [{'text': 'M(a,b,c)=[[sum(a/k,k,1,100),b+c],[0,1]]',
             'plot_slice': {'axes':['a','b'], 'fixed':{'c':3}}, 'plot_component':1}]
    r = Calculator(rows).run([-2, 2, -3, 3])[0]
    assert 'error' not in r
    assert r['sampling']['reduced'] and r['shape'] == [2,2]
    assert r['x'][0] == -2 and r['x'][-1] == 2
    assert r['y'][0] == -3 and r['y'][-1] == 3
    x, y = np.meshgrid(r['x'], r['y'])
    np.testing.assert_allclose(r['real'], y+3)
    assert r['selected_component'] == 1


def test_variable_cost_discards_partial_refinement_and_reuses_points():
    c = Calculator([])
    seen = []
    def point(t):
        seen.append(t)
        # Coarse grid costs nine nodes, but the next level has an expensive point.
        for _ in range(100 if t == .125 else 1):
            c.sampling_budget.consume()
        return t*t
    axes, values, info = sample_grid(c, point, [[-1,1]], 1000, 40)
    assert len(axes[0]) == 9 and info['points'] == 9
    np.testing.assert_allclose(values, axes[0]**2)
    assert len(seen) == len(set(seen))
    assert info['evaluation_steps'] == 40 and c.sampling_budget is None


def test_ordinary_curves_reach_original_resolution():
    r = Calculator([{'text':'v(t)=[t,t^2]'}]).run([-1,1,-5,5])[0]
    assert len(r['x']) == 1000 and not r['sampling']['reduced']
    assert 'notice' not in r['sampling']


def test_structural_and_per_point_errors_are_not_hidden_by_fallback():
    c = Calculator([{'text':'f(t)=sum(t/k,k,1,10000)'},
                    {'text':'v(t)=[missing,t]'}, {'text':'w(t)=[t,t+1]'}])
    r = c.run([-1,1,-5,5])
    assert 'Evaluation limit' in r[0]['error']
    assert 'Unknown variable' in r[1]['error']
    assert 'error' not in r[2] and len(r[2]['x']) == 1000
    assert c.sampling_budget is None


@pytest.mark.parametrize('kind', ['function','parametric','surface'])
def test_named_graphs_reduce_resolution_without_truncating(kind):
    g = {'id':'g1', 'name':'Expensive', 'type':kind, 'samples':1000,
         'range':[-1,1], 'yrange':[-2,2], 'parameter':'t',
         'x':'t', 'y':'sum(x/k,k,1,100)' if kind == 'function' else 'sum(t/k,k,1,100)',
         'z':'sum((x+y)/k,k,1,100)'}
    r = graph_results([g], [], [])[0]
    assert 'error' not in r
    assert r['sampling']['reduced'] and r['sampling']['evaluation_steps'] <= 500000
    assert r['x'][0] == -1 and r['x'][-1] == 1
    h = sum(1/k for k in range(1,101))
    if kind == 'surface':
        x,y = np.meshgrid(r['x'],r['y'])
        np.testing.assert_allclose(r['z'], (x+y)*h, atol=1e-12)
    else:
        np.testing.assert_allclose(r['y'], np.array(r['x'])*h, atol=1e-12)


def test_api_returns_reduced_plot_and_notice():
    response = app.test_client().post('/api/evaluate', json={
        'expressions':[{'text':'f(t)=sum(t/k,k,1,500)'}]})
    assert response.status_code == 200
    r = response.json['results'][0]
    assert 'error' not in r and 'Reduced plot detail' in r['sampling']['notice']
