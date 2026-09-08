"""Start with: python -m celery -A celery_app:celery_app worker --concurrency=4."""
import os
from celery import Celery, Task
from celery.signals import worker_process_init

celery_app=Celery('nmgrapher',broker=os.environ.get('NMGRAPHER_CELERY_BROKER_URL','redis://127.0.0.1:6379/0'))
celery_app.conf.update(
    task_default_queue='nmgrapher',task_serializer='json',accept_content=['json'],
    task_ignore_result=True,worker_prefetch_multiplier=1,task_acks_late=True,
    task_reject_on_worker_lost=True,task_soft_time_limit=180,task_time_limit=190,
    broker_connection_timeout=2,broker_connection_retry_on_startup=True,
    broker_transport_options={'visibility_timeout':300,'socket_connect_timeout':2,'socket_timeout':3},
    worker_max_tasks_per_child=100,worker_cancel_long_running_tasks_on_connection_loss=True,
)

@worker_process_init.connect
def initialize_worker(**kwargs):
    from async_compute import _initialize_worker
    _initialize_worker()

class ComputeTask(Task):
    def on_failure(self, exc, task_id, args, kwargs, einfo):
        from celery_compute import RedisJobManager
        try:RedisJobManager().finish(args[0],'error','A calculation worker failed. Retry the worksheet.')
        except Exception:pass  # Broker recovery/deadline handling remains available.

@celery_app.task(bind=True,base=ComputeTask,name='nmgrapher.compute')
def compute(self, ident, kind, index):
    from async_compute import BackendUnavailable, JobNotFound, compute_payload
    from celery_compute import RedisJobManager, RedisCancellationToken
    manager=RedisJobManager()
    try:
        work=manager.read_work(ident)
        if work is None:return
        payload,deadline=work
        result=compute_payload(payload,kind,index,RedisCancellationToken(manager,ident,deadline))
        if result.get('cancelled'):
            manager.poll(ident)  # Finalize a deadline; user cancellation already persisted.
        else:manager.append(ident,result)
    except JobNotFound:
        return  # Expired/evicted jobs have no work left to publish.
    except BackendUnavailable as exc:
        raise self.retry(exc=exc,countdown=1,max_retries=2)
