"""Bounded background worksheet jobs; subprocesses perform independent row plots.

No executor or thread starts at import time. The standard spawn context works
with macOS/Windows IDE execution as well as a threaded Flask server. Job state
belongs to one WSGI process: use one threaded WSGI worker or sticky routing.
"""
from collections import deque
from concurrent.futures import ProcessPoolExecutor, ThreadPoolExecutor, CancelledError
from concurrent.futures.process import BrokenProcessPool
from dataclasses import dataclass, field
import atexit
import json
import multiprocessing
import os
from pathlib import Path
import tempfile
import threading
import time
import uuid


class JobCapacityError(ValueError):
    pass


class JobNotFound(KeyError):
    pass


def _initialize_worker():
    # Native libraries should not multiply their own thread pools per process.
    # The env values apply before the lazy engine import in ordinary WSGI use.
    for name in ('OPENBLAS_NUM_THREADS', 'OMP_NUM_THREADS', 'MKL_NUM_THREADS', 'NUMEXPR_NUM_THREADS'):
        os.environ[name] = '1'
    try:
        from threadpoolctl import threadpool_limits
        threadpool_limits(limits=1)
    except ImportError:
        pass


class _CancellationToken:
    def __init__(self, path, deadline):
        self.path = path
        self.deadline = deadline
        self.next_check = 0.0

    def __call__(self):
        now = time.monotonic()
        if now >= self.deadline:
            return True
        if now < self.next_check:
            return False
        self.next_check = now + 0.025
        return not os.path.exists(self.path)


def compute_task(payload, kind, index, token_path, deadline):
    """Top-level spawn/pickle entry point; worksheet text stays in the safe AST."""
    from engine import Calculator, ComputationCancelled
    check = _CancellationToken(token_path, deadline)
    started = time.monotonic()
    if check():
        return {'cancelled': True}
    calculator = Calculator(payload['expressions'], payload['datasets'], cancel_check=check)
    try:
        if kind == 'row':
            result = calculator.run(payload['bounds'], complex_domain=payload['complex_domain'],
                                    curve_range=payload['curve_range'], indices=[index])[0]
        else:
            from graphing import sample_graph
            graph = payload['graphs'][index]
            if not graph['visible']:
                result = {'id': graph['id'], 'hidden': True}
            else:
                try:
                    result = sample_graph(calculator, graph)
                except ComputationCancelled:
                    raise
                except Exception as exc:
                    result = {'id': graph['id'], 'error': str(exc) or 'Could not sample this graph.'}
        calculator.check_cancelled()
        return {'kind': kind, 'index': index, 'result': result,
                'duration_ms': round((time.monotonic() - started) * 1000, 1)}
    except ComputationCancelled:
        return {'cancelled': True}


@dataclass
class _Job:
    ident: str
    payload: dict
    token: str
    created: float
    deadline: float
    pending: deque
    total: int
    state: str = 'running'
    events: list = field(default_factory=list)
    size: int = 0
    completed: int = 0
    finished: float | None = None
    error: str | None = None


class JobManager:
    """One scheduler, at most `workers` submitted futures, bounded retained jobs."""
    def __init__(self, workers=None, *, executor_factory=None, max_active=4,
                 max_jobs=8, ttl=120, timeout=180, max_output_bytes=64 * 1024 * 1024,
                 max_retained_bytes=128 * 1024 * 1024, clock=time.monotonic):
        configured = os.environ.get('NMGRAPHER_WORKERS', '')
        if workers is None:
            try: workers = int(configured) if configured else min(4, os.cpu_count() or 1)
            except ValueError: workers = 2
        self.workers = max(1, min(4, workers))
        self.mode = 'process'
        self.notice = None
        self.max_active = max_active
        self.max_jobs = max_jobs
        self.ttl = ttl
        self.timeout = timeout
        self.max_output_bytes = max_output_bytes
        self.max_retained_bytes = max_retained_bytes
        self._clock = clock
        self._executor_factory = executor_factory
        self._executor = None
        self._condition = threading.Condition(threading.RLock())
        self._jobs = {}
        self._active = {}
        self._turn = deque()
        self._directory = None
        self._thread = None
        self._closed = False

    def _ensure_started(self):
        if self._closed:
            raise JobCapacityError('Background computation is shutting down; restart the app.')
        if self._thread is not None:
            return
        self._directory = tempfile.TemporaryDirectory(prefix='nmgrapher-jobs-')
        try:
            self._executor = (self._executor_factory(self.workers) if self._executor_factory else
                              ProcessPoolExecutor(max_workers=self.workers,
                                                  mp_context=multiprocessing.get_context('spawn'),
                                                  initializer=_initialize_worker))
        except (OSError, RuntimeError, NotImplementedError):
            self._fallback()
        self._thread = threading.Thread(target=self._schedule, name='nmgrapher-jobs', daemon=True)
        self._thread.start()

    def _fallback(self):
        old = self._executor
        # A broken pool may still have a task inside a native operation. Retrying
        # gets a fresh token so the old computation stops at its next checkpoint.
        for job in self._jobs.values():
            if job.state == 'running':
                Path(job.token).unlink(missing_ok=True)
                job.token = str(Path(self._directory.name) / uuid.uuid4().hex)
                Path(job.token).touch()
        self.mode = 'thread'
        self.workers = min(self.workers, 2)
        self.notice = 'Subprocesses are unavailable on this host. Background threads are active; CPU parallelism is limited.'
        self._executor = ThreadPoolExecutor(max_workers=self.workers, thread_name_prefix='nmgrapher-compute')
        if old is not None:
            old.shutdown(wait=False, cancel_futures=True)

    def _remove(self, ident):
        job = self._jobs.pop(ident, None)
        if job:
            Path(job.token).unlink(missing_ok=True)
        self._turn = deque(item for item in self._turn if item != ident)

    def _prune(self):
        now = self._clock()
        for ident, job in list(self._jobs.items()):
            if job.state != 'running' and job.finished is not None and now - job.finished >= self.ttl:
                self._remove(ident)
        while len(self._jobs) >= self.max_jobs:
            old = [job for job in self._jobs.values() if job.state != 'running']
            if not old:
                break
            self._remove(min(old, key=lambda job: job.finished).ident)

    def submit(self, payload, calculator=None):
        # The HTTP layer validates all inputs; snapshot prevents caller mutation.
        payload = json.loads(json.dumps(payload))
        from engine import Calculator
        calculator = calculator or Calculator(payload['expressions'], payload['datasets'])
        ready = []
        ranked = []
        for index, item in enumerate(calculator.items):
            if item['kind'] == 'note' or item.get('error') or item.get('tree') is None:
                ready.append({'kind': 'row', 'index': index, 'result': calculator.metadata([index])[0]})
                continue
            tree = item['tree']
            priority = (4 if calculator.contains_multiple_integrals(tree) else
                        3 if calculator.contains_calculus(tree) else
                        2 if calculator.needs_pointwise(tree) else
                        1 if item['kind'] in ('function', 'implicit', 'explicit', 'inequality') or calculator.free_names(tree) else 0)
            ranked.append((priority, 'row', index))
        for index, graph in enumerate(payload['graphs']):
            if not graph['visible']:
                ready.append({'kind': 'graph', 'index': index, 'result': {'id': graph['id'], 'hidden': True}})
            else:
                ranked.append((2, 'graph', index))
        pending = deque((kind, index) for _, kind, index in sorted(ranked, key=lambda item: item[0]))
        with self._condition:
            self._prune()
            if sum(job.state == 'running' for job in self._jobs.values()) >= self.max_active or len(self._jobs) >= self.max_jobs:
                raise JobCapacityError('The computation queue is full. Wait for a worksheet to finish or cancel it.')
            self._ensure_started()
            ident = uuid.uuid4().hex
            token = str(Path(self._directory.name) / ident)
            Path(token).touch()
            now = self._clock()
            job = _Job(ident, payload, token, now, now + self.timeout, pending, len(pending) + len(ready))
            job.events = [json.dumps(event, separators=(',', ':')) for event in ready]
            job.completed = len(ready)
            job.size = sum(len(event.encode('utf-8')) for event in job.events)
            self._jobs[ident] = job
            self._turn.append(ident)
            if not pending:
                self._finish(job, 'complete')
            self._condition.notify_all()
            return self._snapshot(job, 0)

    def _finish(self, job, state, error=None):
        if job.state != 'running':
            return
        job.state, job.error, job.finished = state, error, self._clock()
        job.pending.clear()
        # Payloads are held by in-flight tasks as needed; release the retained copy.
        job.payload = {}
        Path(job.token).unlink(missing_ok=True)
        for future, (ident, _, _) in self._active.items():
            if ident == job.ident:
                future.cancel()

    def _snapshot(self, job, after):
        result = {'job_id': job.ident, 'state': job.state, 'completed': job.completed,
                  'total': job.total, 'workers': self.workers, 'mode': self.mode,
                  'cursor': len(job.events), 'results': [json.loads(event) for event in job.events[after:]]}
        if job.error:
            result['error'] = job.error
        if self.notice:
            result['notice'] = self.notice
        return result

    def poll(self, ident, after=0):
        with self._condition:
            # Expire by completion time, not by polling activity.
            job = self._jobs.get(ident)
            if job and job.finished is not None and self._clock() - job.finished >= self.ttl:
                self._remove(ident); job = None
            if job is None:
                raise JobNotFound(ident)
            if type(after) is not int or not 0 <= after <= len(job.events):
                raise ValueError('The result cursor is outside this job.')
            return self._snapshot(job, after)

    def cancel(self, ident):
        with self._condition:
            job = self._jobs.get(ident)
            if job is None:
                raise JobNotFound(ident)
            self._finish(job, 'cancelled')
            self._condition.notify_all()
            return self._snapshot(job, len(job.events))

    def _collect(self):
        broken = False
        for future, (ident, kind, index) in list(self._active.items()):
            if not future.done():
                continue
            del self._active[future]
            job = self._jobs.get(ident)
            try:
                event = future.result()
            except BrokenProcessPool:
                broken = True
                if job and job.state == 'running':
                    job.pending.appendleft((kind, index))
                continue
            except CancelledError:
                continue
            except Exception:
                event = {'kind': kind, 'index': index, 'result': {'error': 'Computation failed. Retry this expression.'}}
                if kind == 'graph' and job and job.payload:
                    event['result']['id'] = job.payload['graphs'][index]['id']
            if job is None or job.state != 'running':
                continue
            if event.get('cancelled'):
                self._finish(job, 'error', 'Computation took too long. Reduce plot detail or simplify the formula.')
                continue
            encoded = json.dumps(event, separators=(',', ':'))
            size = len(encoded.encode('utf-8'))
            retained = sum(item.size for item in self._jobs.values())
            # Evict old completed responses before rejecting a large active one.
            for old in sorted((item for item in self._jobs.values() if item.state != 'running'), key=lambda item: item.finished):
                if retained + size <= self.max_retained_bytes:
                    break
                retained -= old.size
                self._remove(old.ident)
            if job.size + size > self.max_output_bytes or retained + size > self.max_retained_bytes:
                self._finish(job, 'error', 'This worksheet produces too much plot data. Reduce the number of surfaces or select individual components.')
                continue
            job.events.append(encoded)
            job.size += size
            job.completed += 1
            if job.completed == job.total:
                self._finish(job, 'complete')
        if broken and self.mode == 'process':
            # Requeue other submitted work exactly once before replacing the pool.
            for future, (ident, kind, index) in list(self._active.items()):
                job = self._jobs.get(ident)
                if job and job.state == 'running':
                    job.pending.appendleft((kind, index))
                future.cancel()
            self._active.clear()
            self._fallback()

    def _dispatch(self):
        turns = len(self._turn)
        while len(self._active) < self.workers and self._turn and turns:
            ident = self._turn.popleft()
            job = self._jobs.get(ident)
            if job is None or job.state != 'running':
                turns -= 1
                continue
            self._turn.append(ident)
            if not job.pending:
                turns -= 1
                continue
            kind, index = job.pending.popleft()
            try:
                future = self._executor.submit(compute_task, job.payload, kind, index, job.token, job.deadline)
            except (BrokenProcessPool, OSError, RuntimeError):
                job.pending.appendleft((kind, index))
                if self.mode == 'process':
                    # Existing futures are collected/requeued on their next turn.
                    for running, (other_id, other_kind, other_index) in list(self._active.items()):
                        other = self._jobs.get(other_id)
                        if other and other.state == 'running':other.pending.appendleft((other_kind, other_index))
                        running.cancel()
                    self._active.clear()
                    self._fallback()
                    return
                self._finish(job, 'error', 'Background computation is unavailable. Restart the app.')
                continue
            self._active[future] = (ident, kind, index)
            turns = len(self._turn)

    def _schedule(self):
        with self._condition:
            while not self._closed:
                try:
                    self._collect()
                    now = self._clock()
                    for job in list(self._jobs.values()):
                        if job.state == 'running' and now >= job.deadline:
                            self._finish(job, 'error', 'Computation took too long. Reduce plot detail or simplify the formula.')
                        elif job.finished is not None and now - job.finished >= self.ttl:
                            self._remove(job.ident)
                    self._dispatch()
                except Exception:
                    for job in list(self._jobs.values()):
                        self._finish(job, 'error', 'Background computation stopped unexpectedly. Retry the worksheet.')
                self._condition.wait(timeout=0.03)

    def close(self, wait=False):
        with self._condition:
            if self._closed:
                return
            self._closed = True
            for job in list(self._jobs.values()):
                self._finish(job, 'cancelled')
            self._condition.notify_all()
            executor = self._executor
        if self._thread is not None and self._thread is not threading.current_thread():
            self._thread.join(timeout=1)
        if executor is not None:
            executor.shutdown(wait=wait, cancel_futures=True)
        if self._directory is not None:
            self._directory.cleanup()


# Lazy singleton: importing app.py never spawns subprocesses (including in children).
manager = JobManager()
atexit.register(manager.close)
