import os
import time
from concurrent.futures import Future, ThreadPoolExecutor
from pathlib import Path

import numpy as np
import pytest

from app import app, evaluation_payload
from async_compute import JobManager, JobCapacityError, JobNotFound, compute_task
from engine import Calculator, ComputationCancelled
from graphing import validate_graphs


def payload(*texts, graphs=None):
    result = evaluation_payload({'expressions': [{'text': text} for text in texts]})
    result['graphs'] = validate_graphs(graphs or [])
    return result


def until(check, timeout=5):
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        result = check()
        if result:
            return result
        time.sleep(.01)
    raise AssertionError('Background computation did not finish before timeout.')


def finished(manager, ident, timeout=10):
    return until(lambda: (state if (state := manager.poll(ident))['state'] != 'running' else None), timeout)


class ControlledExecutor:
    def __init__(self, workers):
        self.calls = []
        self.workers = workers

    def submit(self, function, *args):
        future = Future()
        future.set_running_or_notify_cancel()
        self.calls.append((future, args))
        return future

    def shutdown(self, **_):
        pass

    def complete(self, index, result=None):
        future, args = self.calls[index]
        _, kind, row_index, *_ = args
        future.set_result(result or {'kind': kind, 'index': row_index, 'result': {'value': row_index}})


@pytest.fixture
def manager():
    instance = JobManager(workers=2, executor_factory=lambda workers: ThreadPoolExecutor(workers))
    yield instance
    instance.close(wait=True)


def test_selected_rows_keep_forward_dependencies_and_do_not_sample_other_functions(monkeypatch):
    rows = [{'text': 'f(t)=sum(sin(k*t),k,1,20)'}, {'text': 'a=b+1'}, {'text': 'b=4'}, {'text': 'a*2'}]
    c = Calculator(rows)
    monkeypatch.setattr(c, 'sample_algebraic', lambda *_: pytest.fail('Unrequested function was sampled'))
    result = c.run([-1, 1, -1, 1], indices=[3, 1])
    assert [item['value'] for item in result] == [10, 5]
    assert c.run([-1, 1, -1, 1], indices=[]) == []
    with pytest.raises(ValueError):c.run([-1, 1, -1, 1], indices=[True])
    with pytest.raises(ValueError):c.run([-1, 1, -1, 1], indices=[0, 0])


def test_api_indices_and_validate_only_never_sample(monkeypatch):
    client = app.test_client()
    rows = [{'text': 'f(t)=integrate(sin(t*x),x,0,10)'}, {'text': 'a=3'}, {'text': 'a^2'}]
    result = client.post('/api/evaluate', json={'expressions': rows, 'indices': [2]})
    assert result.status_code == 200 and len(result.json['results']) == 1
    assert result.json['results'][0]['value'] == 9
    monkeypatch.setattr(Calculator, 'run', lambda *_args, **_kwargs: pytest.fail('Validation must not sample'))
    result = client.post('/api/evaluate', json={'expressions': rows, 'indices': [0], 'validate_only': True})
    assert result.status_code == 200
    assert result.json['results'][0]['function']['name'] == 'f'
    result = client.post('/api/evaluate', json={'expressions': [{'text': 'sin(x)=1'}], 'validate_only': True})
    assert result.json['results'][0]['error']
    for indices in ([3], [True], [0, 0], '0'):
        assert client.post('/api/evaluate', json={'expressions': rows, 'indices': indices}).status_code == 400
    assert client.post('/api/evaluate', json={'validate_only': 'yes'}).status_code == 400


def test_job_incremental_results_context_graphs_notes_and_row_order(manager):
    p = payload('a=b+1', 'b=4', 'a*2', graphs=[{'id': 'g1', 'name': 'named', 'type': 'function', 'y': 'a*x', 'samples': 50}])
    p['expressions'].insert(1, {'type': 'note', 'text': 'a=100\nreminder'})
    initial = manager.submit(p)
    assert initial['total'] == 5
    assert initial['results'][0]['index'] == 1
    after = initial['cursor']
    result = finished(manager, initial['job_id'])
    assert result['state'] == 'complete' and result['completed'] == 5
    assert len(manager.poll(initial['job_id'], after)['results']) == 5 - after
    assert manager.poll(initial['job_id'], result['cursor'])['results'] == []
    by_index = {entry['index']: entry['result'] for entry in result['results'] if entry['kind'] == 'row'}
    assert by_index[0]['value'] == 5 and by_index[3]['value'] == 10
    graph = next(entry['result'] for entry in result['results'] if entry['kind'] == 'graph')
    np.testing.assert_allclose(graph['y'], np.array(graph['x']) * 5)
    with pytest.raises(ValueError):manager.poll(initial['job_id'], 999)


def test_queue_never_submits_more_than_worker_count_and_prioritizes_simple_rows():
    executor = ControlledExecutor(2)
    manager = JobManager(workers=2, executor_factory=lambda _: executor, max_active=2)
    try:
        first = manager.submit(payload('f(t)=integrate(sin(t*x),x,0,10)', 'a=2', 'a+1', 'a+2'))
        until(lambda: len(executor.calls) == 2)
        assert [args[2] for _, args in executor.calls] == [1, 2]
        second = manager.submit(payload('1', '2'))
        with pytest.raises(JobCapacityError):manager.submit(payload('3'))
        time.sleep(.04)
        assert len(executor.calls) == 2
        executor.complete(0)
        until(lambda: len(executor.calls) == 3)
        assert len([future for future, _ in executor.calls if not future.done()]) <= 2
        manager.cancel(first['job_id'])
        manager.cancel(second['job_id'])
        for future, _ in executor.calls:
            if not future.done():future.set_result({'cancelled': True})
    finally:
        manager.close()


def test_cancel_removes_token_discards_late_result_and_keeps_new_job_isolated():
    executor = ControlledExecutor(1)
    manager = JobManager(workers=1, executor_factory=lambda _: executor)
    try:
        old = manager.submit(payload('1', '2'))
        until(lambda: len(executor.calls) == 1)
        token = executor.calls[0][1][3]
        assert Path(token).exists()
        assert manager.cancel(old['job_id'])['state'] == 'cancelled'
        assert not Path(token).exists()
        new = manager.submit(payload('3'))
        executor.complete(0)
        until(lambda: len(executor.calls) == 2)
        executor.complete(1, {'kind': 'row', 'index': 0, 'result': {'value': 3}})
        assert finished(manager, new['job_id'])['results'][0]['result']['value'] == 3
        assert manager.poll(old['job_id'])['results'] == []
    finally:
        manager.close()


def test_cooperative_cancel_propagates_out_of_calculus():
    calls = 0
    def cancel():
        nonlocal calls
        calls += 1
        return calls >= 4
    c = Calculator([{'text': 'f(t)=integrate(sin(t*x),x,0,10)'}], cancel_check=cancel)
    with pytest.raises(ComputationCancelled):
        c.run([-1, 1, -1, 1])
    assert calls == 4


def test_cancelled_worker_does_not_evaluate_missing_token(tmp_path):
    event = compute_task(payload('1'), 'row', 0, str(tmp_path / 'gone'), time.monotonic() + 5)
    assert event == {'cancelled': True}


def test_completed_jobs_expire_and_results_are_bounded():
    now = [time.monotonic()]
    executor = ControlledExecutor(1)
    manager = JobManager(workers=1, executor_factory=lambda _: executor, ttl=2, clock=lambda: now[0], max_output_bytes=20)
    try:
        job = manager.submit(payload('1'))
        until(lambda: len(executor.calls) == 1)
        executor.complete(0)
        result = finished(manager, job['job_id'])
        assert result['state'] == 'error' and 'too much plot data' in result['error']
        now[0] += 3
        with pytest.raises(JobNotFound):manager.poll(job['job_id'])
    finally:
        manager.close()


def test_timeout_cancels_pending_work():
    executor = ControlledExecutor(1)
    manager = JobManager(workers=1, executor_factory=lambda _: executor, timeout=.08)
    try:
        job = manager.submit(payload('1', '2'))
        result = finished(manager, job['job_id'])
        assert result['state'] == 'error' and 'too long' in result['error']
        assert len(executor.calls) == 1
        assert not Path(executor.calls[0][1][3]).exists()
        executor.complete(0)
    finally:
        manager.close()


def test_subprocess_failure_is_explicit_thread_fallback():
    def unavailable(_):raise OSError('Host does not permit subprocesses')
    manager = JobManager(workers=4, executor_factory=unavailable)
    try:
        job = manager.submit(payload('2+3'))
        assert job['mode'] == 'thread' and job['workers'] == 2 and 'limited' in job['notice']
        assert finished(manager, job['job_id'])['results'][0]['result']['value'] == 5
    finally:
        manager.close(wait=True)


def test_http_jobs_validate_poll_and_cancel(manager, monkeypatch):
    import async_compute
    monkeypatch.setattr(async_compute, 'manager', manager)
    client = app.test_client()
    result = client.post('/api/jobs', json={'expressions': [{'text': '2+3'}]})
    assert result.status_code == 202
    ident = result.json['job_id']
    finished(manager, ident)
    result = client.get('/api/jobs/' + ident)
    assert result.json['results'][0]['result']['value'] == 5
    assert client.post('/api/jobs/' + ident + '/cancel').json['state'] == 'complete'
    assert client.get('/api/jobs/' + ident + '?after=-1').status_code == 400
    assert client.get('/api/jobs/' + ident + '?after=abc').status_code == 400
    assert client.get('/api/jobs/missing').status_code == 404
    assert client.post('/api/jobs/missing/cancel').status_code == 404
    for data in ([], {'expressions': [{'text': '1'}] * 41}, {'graphs': [{}]}, {'datasets': 'bad'}, {'bounds': [1, 1, 0, 2]}):
        assert client.post('/api/jobs', json=data).status_code == 400


def test_spawned_process_pool_computes_independent_rows_with_full_context():
    manager = JobManager(workers=2)
    try:
        job = manager.submit(payload('a=3', 'f(x)=a*x^2', 'f(2)', 'integrate(f(t),t,0,1)'))
        result = finished(manager, job['job_id'], timeout=40)
        assert result['state'] == 'complete', result
        assert result['mode'] == 'process' and result['workers'] == 2
        assert len(manager._executor._processes) == 2
        assert all(process.pid != os.getpid() and process.is_alive() for process in manager._executor._processes.values())
        rows = {entry['index']: entry['result'] for entry in result['results']}
        assert rows[2]['value'] == 12
        assert rows[3]['value'] == pytest.approx(1)
        np.testing.assert_allclose(rows[1]['y'], 3 * np.array(rows[1]['x']) ** 2)
    finally:
        manager.close(wait=True)


def test_broken_pool_rotates_tokens_and_retries_unfinished_tasks():
    from concurrent.futures.process import BrokenProcessPool
    executor = ControlledExecutor(2)
    manager = JobManager(workers=2, executor_factory=lambda _: executor)
    try:
        job = manager.submit(payload('2+3', '4+5'))
        until(lambda: len(executor.calls) == 2)
        old_token = executor.calls[0][1][3]
        executor.calls[0][0].set_exception(BrokenProcessPool('worker stopped'))
        result = finished(manager, job['job_id'])
        assert result['state'] == 'complete' and result['mode'] == 'thread'
        assert not Path(old_token).exists()
        assert sorted(event['result']['value'] for event in result['results']) == [5, 9]
        assert len({event['index'] for event in result['results']}) == 2
        # A late old-worker result cannot overwrite or duplicate a retried event.
        executor.calls[1][0].set_result({'kind': 'row', 'index': 1, 'result': {'value': 999}})
        assert manager.poll(job['job_id'])['completed'] == 2
    finally:
        manager.close(wait=True)
