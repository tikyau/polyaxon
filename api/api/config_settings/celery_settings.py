# -*- coding: utf-8 -*-
from __future__ import absolute_import, division, print_function

from datetime import timedelta

from kombu import Exchange, Queue

from api.utils import config

CELERY_TRACK_STARTED = True

CELERY_BROKER_URL = config.get_string('POLYAXON_AMQP_URL')
INTERNAL_EXCHANGE = config.get_string('POLYAXON_INTERNAL_EXCHANGE')

CELERY_RESULT_BACKEND = config.get_string('POLYAXON_REDIS_CELERY_RESULT_BACKEND_URL')
CELERYD_PREFETCH_MULTIPLIER = config.get_int('POLYAXON_CELERYD_PREFETCH_MULTIPLIER')

CELERY_TASK_ALWAYS_EAGER = config.get_boolean('POLYAXON_CELERY_ALWAYS_EAGER')
if CELERY_TASK_ALWAYS_EAGER:
    BROKER_TRANSPORT = 'memory'

CELERY_ACCEPT_CONTENT = ['application/json']
CELERY_TASK_SERIALIZER = 'json'
CELERY_RESULT_SERIALIZER = 'json'


class Intervals(object):
    """All intervals are in seconds"""
    EXPERIMENTS_SCHEDULER = config.get_int(
        'POLYAXON_INTERVALS_EXPERIMENTS_SCHEDULER',
        is_optional=True) or 30
    CLUSTERS_UPDATE_SYSTEM_INFO = config.get_int(
        'POLYAXON_INTERVALS_CLUSTERS_UPDATE_SYSTEM_INFO',
        is_optional=True) or 150
    CLUSTERS_UPDATE_SYSTEM_NODES = config.get_int(
        'POLYAXON_INTERVALS_CLUSTERS_UPDATE_SYSTEM_NODES',
        is_optional=True) or 150

    @staticmethod
    def get_schedule(interval):
        return timedelta(seconds=int(interval))

    @staticmethod
    def get_expires(interval):
        int(interval / 2)


class RoutingKeys(object):
    LOGS_SIDECARS = config.get_string('POLYAXON_ROUTING_KEYS_LOGS_SIDECARS')


class CeleryPublishTask(object):
    """Tasks to be send as a signal to the exchange."""
    PUBLISH_LOGS_SIDECAR = 'publish_logs_sidecar'


class CeleryTasks(object):
    """Normal celery tasks."""
    EXPERIMENTS_START = 'experiments_start'
    EXPERIMENTS_START_GROUP = 'experiments_start_group'
    EXPERIMENTS_CHECK_STATUS = 'experiments_check_status'
    CLUSTERS_UPDATE_SYSTEM_INFO = 'clusters_update_system_info'
    CLUSTERS_UPDATE_SYSTEM_NODES = 'clusters_update_system_nodes'
    CLUSTERS_UPDATE_SYSTEM_NODES_GPUS = 'clusters_update_system_nodes'
    EVENTS_HANDLE_NAMESPACE = 'events_handle_namespace'
    EVENTS_HANDLE_RESOURCES = 'events_handle_resources'
    EVENTS_HANDLE_JOB_STATUSES = 'events_handle_job_statuses'
    EVENTS_HANDLE_LOGS_SIDECAR = 'events_handle_logs_sidecar'


class CeleryQueues(object):
    API_EXPERIMENTS = config.get_string(
        'POLYAXON_QUEUES_API_EXPERIMENTS',
        is_optional=True) or 'api.experiments'
    API_CLUSTERS = config.get_string(
        'POLYAXON_QUEUES_API_CLUSTERS',
        is_optional=True) or 'api.clusters'
    EVENTS_NAMESPACE = config.get_string(
        'POLYAXON_QUEUES_EVENTS_NAMESPACE',
        is_optional=True) or 'events.namespace'
    EVENTS_RESOURCES = config.get_string(
        'POLYAXON_QUEUES_EVENTS_RESOURCES',
        is_optional=True) or 'events.resources'
    EVENTS_JOB_STATUSES = config.get_string(
        'POLYAXON_QUEUES_EVENTS_JOB_STATUSES',
        is_optional=True) or 'events.statuses'
    LOGS_SIDECARS = config.get_string(
        'POLYAXON_QUEUES_LOGS_SIDECARS',
        is_optional=True) or 'logs.sidecars'
    STREAM_LOGS_SIDECARS = config.get_string(
        'POLYAXON_QUEUES_STREAM_LOGS_SIDECARS',
        is_optional=True) or 'stream.logs.sidecars'


# Queues on non default exchange
CELERY_TASK_QUEUES = (
    Queue(CeleryQueues.LOGS_SIDECARS,
          exchange=Exchange(INTERNAL_EXCHANGE, 'topic'),
          routing_key=RoutingKeys.LOGS_SIDECARS),
)

CELERY_TASK_ROUTES = {
    CeleryTasks.EXPERIMENTS_START: {'queue': CeleryQueues.API_EXPERIMENTS},
    CeleryTasks.EXPERIMENTS_START_GROUP: {'queue': CeleryQueues.API_EXPERIMENTS},
    CeleryTasks.EXPERIMENTS_CHECK_STATUS: {'queue': CeleryQueues.API_EXPERIMENTS},
    CeleryTasks.CLUSTERS_UPDATE_SYSTEM_INFO: {'queue': CeleryQueues.API_CLUSTERS},
    CeleryTasks.CLUSTERS_UPDATE_SYSTEM_NODES: {'queue': CeleryQueues.API_CLUSTERS},
    CeleryTasks.EVENTS_HANDLE_NAMESPACE: {'queue': CeleryQueues.EVENTS_NAMESPACE},
    CeleryTasks.EVENTS_HANDLE_RESOURCES: {'queue': CeleryQueues.EVENTS_RESOURCES},
    CeleryTasks.EVENTS_HANDLE_JOB_STATUSES: {'queue': CeleryQueues.EVENTS_JOB_STATUSES},
    CeleryTasks.EVENTS_HANDLE_LOGS_SIDECAR: {'queue': CeleryQueues.LOGS_SIDECARS},

    # TODO: remove
    # CeleryRoutedTasks.EVENTS_NAMESPACE: {'queue': CeleryQueues.EVENTS_NAMESPACE},
    CeleryPublishTask.PUBLISH_LOGS_SIDECAR: {'exchange': INTERNAL_EXCHANGE,
                                             'routing_key': RoutingKeys.LOGS_SIDECARS,
                                             'exchange_type': 'topic'},
}

CELERY_BEAT_SCHEDULE = {
    CeleryTasks.CLUSTERS_UPDATE_SYSTEM_INFO + '_beat': {
        'task': CeleryTasks.CLUSTERS_UPDATE_SYSTEM_INFO,
        'schedule': Intervals.get_schedule(Intervals.CLUSTERS_UPDATE_SYSTEM_INFO),
        'options': {
            'expires': Intervals.get_expires(Intervals.CLUSTERS_UPDATE_SYSTEM_INFO),
        },
    },
    CeleryTasks.CLUSTERS_UPDATE_SYSTEM_NODES + '_beat': {
        'task': CeleryTasks.CLUSTERS_UPDATE_SYSTEM_NODES,
        'schedule': Intervals.get_schedule(Intervals.CLUSTERS_UPDATE_SYSTEM_NODES),
        'options': {
            'expires': Intervals.get_expires(Intervals.CLUSTERS_UPDATE_SYSTEM_NODES),
        },
    },
}
