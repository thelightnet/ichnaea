"""
Contains :ref:`celery settings <celery:configuration>`.
"""

from ichnaea.async.config import TASK_QUEUES
from ichnaea.config import (
    REDIS_URI,
    TESTING,
)

if TESTING:
    task_always_eager = True
    task_eager_propagates = True

broker_url = REDIS_URI
result_backend = REDIS_URI

# Based on `Celery / Redis caveats
# <celery.rtfd.org/en/latest/getting-started/brokers/redis.html#caveats>`_.
broker_transport_options = {
    'socket_connect_timeout': 60,
    'socket_keepalive': True,
    'socket_timeout': 30,
    'visibility_timeout': 43200,
}

# Name of the default queue.
task_default_queue = 'celery_default'

# Definition of all queues.
task_queues = TASK_QUEUES

# All modules being searched for @task decorators.
imports = [
    'ichnaea.data.tasks',
]

# Disable task results.
task_ignore_result = True

# Optimization for a mix of fast and slow tasks.
worker_prefetch_multiplier = 8
worker_disable_rate_limits = True
task_compression = 'gzip'

# Internal data format, only accept JSON variants.
accept_content = ['json', 'internal_json']
result_serializer = 'internal_json'
task_serializer = 'internal_json'

# cleanup
del REDIS_URI
del TASK_QUEUES
del TESTING
