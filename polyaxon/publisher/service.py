from amqp import AMQPError
from polyaxon_schemas.utils import to_list
from redis import RedisError

from django.conf import settings

from libs.redis_db import RedisToStream
from libs.services import Service
from polyaxon.celery_api import app as celery_app
from polyaxon.settings import EventsCeleryTasks, RoutingKeys


class PublisherService(Service):
    __all__ = ('publish_experiment_job_log',
               'publish_build_job_log',
               'publish_job_log',
               'setup')

    def __init__(self):
        self._logger = None

    def publish_experiment_job_log(self,
                                   log_line,
                                   status,
                                   experiment_uuid,
                                   experiment_name,
                                   job_uuid,
                                   task_type=None,
                                   task_idx=None):
        try:
            log_line = log_line.decode('utf-8')
        except AttributeError:
            pass

        self._logger.info("Publishing log event for task: %s.%s, %s", task_type, task_idx,
                          experiment_name)
        celery_app.send_task(
            EventsCeleryTasks.EVENTS_HANDLE_LOGS_EXPERIMENT_JOB,
            kwargs={
                'experiment_name': experiment_name,
                'experiment_uuid': experiment_uuid,
                'job_uuid': job_uuid,
                'log_line': log_line,
                'task_type': task_type,
                'task_idx': task_idx})
        try:
            should_stream = (RedisToStream.is_monitored_job_logs(job_uuid) or
                             RedisToStream.is_monitored_experiment_logs(experiment_uuid))
        except RedisError:
            should_stream = False
        if should_stream:
            self._logger.info("Streaming new log event for experiment: %s", experiment_uuid)

            with celery_app.producer_or_acquire(None) as producer:
                try:
                    producer.publish(
                        {
                            'experiment_uuid': experiment_uuid,
                            'job_uuid': job_uuid,
                            'log_line': log_line,
                            'status': status,
                            'task_type': task_type,
                            'task_idx': task_idx
                        },
                        routing_key='{}.{}.{}'.format(RoutingKeys.LOGS_SIDECARS,
                                                      experiment_uuid,
                                                      job_uuid),
                        exchange=settings.INTERNAL_EXCHANGE,
                    )
                except (TimeoutError, AMQPError):
                    pass

    def publish_build_job_log(self, log_lines, job_uuid, job_name):
        log_lines = to_list(log_lines)

        self._logger.info("Publishing log event for task: %s", job_uuid)
        celery_app.send_task(
            EventsCeleryTasks.EVENTS_HANDLE_LOGS_BUILD_JOB,
            kwargs={'job_uuid': job_uuid, 'job_name': job_name, 'log_lines': log_lines})

    def publish_job_log(self, log_line, job_uuid, job_name):
        try:
            log_line = log_line.decode('utf-8')
        except AttributeError:
            pass

        self._logger.info("Publishing log event for task: %s", job_uuid)
        celery_app.send_task(
            EventsCeleryTasks.EVENTS_HANDLE_LOGS_JOB,
            kwargs={'job_uuid': job_uuid, 'job_name': job_name, 'log_line': log_line})

    def setup(self):
        import logging

        self._logger = logging.getLogger('polyaxon.monitors.publisher')
