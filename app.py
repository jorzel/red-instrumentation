import random
import time
import redis
import re
import os
import json
import logging
from urllib.parse import urlparse

import prometheus_client
from flask import Flask, request
from prometheus_client import Histogram, make_wsgi_app
from werkzeug import Response
from werkzeug.middleware.dispatcher import DispatcherMiddleware


logging.basicConfig()
logger = logging.getLogger()
logger.setLevel(logging.DEBUG)

app = Flask(__name__)
app.wsgi_app = DispatcherMiddleware(app.wsgi_app, {"/metrics": make_wsgi_app()})

prometheus_client.REGISTRY.unregister(prometheus_client.GC_COLLECTOR)
prometheus_client.REGISTRY.unregister(prometheus_client.PLATFORM_COLLECTOR)
prometheus_client.REGISTRY.unregister(prometheus_client.PROCESS_COLLECTOR)


REDIS_CALL_DURATION = Histogram(
    "redis_call_duration",
    "Redis calls durations",
    ["operation", "status"]
)


def observe_redis(func):
    def wrapper(*args, **kwargs):
        start = time.time()
        status = 'success'
        try:
            result = func(*args, **kwargs)
            return result
        except Exception:
            status = 'error'
            raise
        finally:
            end = time.time()
            REDIS_CALL_DURATION.labels(
                status=status,
                operation=func.__name__
            ).observe(end - start)
    return wrapper


class InstrumentedRedisClient:
    def __init__(self, client):
        self._client = client

    @observe_redis
    def set(self, *args, **kwargs):
        return self._client.set(*args, **kwargs)

    @observe_redis
    def get(self, *args, **kwargs):
        return self._client.get(*args, **kwargs)


redis_client = InstrumentedRedisClient(
    client=redis.Redis(host=os.environ["REDIS_HOST"], port=os.environ["REDIS_PORT"], db=0)
)


HTTP_REQUEST_DURATION = Histogram(
    "http_request_duration",
    "Http requests durations",
    ["method", "path", "code"],
    buckets=[0.01, 0.1, 0.5, 2, float("inf")],
)


RESERVATIONS_REGEX = '^\/reservations\/(?P<user_id>.*)'


def _map_url(incoming_path):
    _path_mapper = {
        RESERVATIONS_REGEX: "/reservations/:user_id"
    }
    for pattern, outgoing_path in _path_mapper.items():
        if re.match(pattern, incoming_path):
            return outgoing_path
    return incoming_path


def observe_http(func):
    def wrapper(*args, **kwargs):
        start = time.time()
        try:
            response = func(*args, **kwargs)
            response_code = response.status_code
            return response
        except Exception:
            response_code = 500
            raise
        finally:
            end = time.time()
            parts = urlparse(request.url)
            HTTP_REQUEST_DURATION.labels(
                method=request.method,
                code=response_code,
                path=_map_url(parts.path),
            ).observe(end - start)
        return response
    return wrapper


@app.route("/reservations/<user_id>")
@observe_http
def reservations(user_id):
    if len(user_id) > 5:
        return Response("400", status=400)

    rand_problem = random.randint(1, 100)
    if rand_problem > 90:
        return Response("500", status=500)

    results = _get_from_cache(user_id)
    logger.info(f"get from cache: {results}")
    if not results:
        logger.info("fetching from external source")
        results = _fetch_reservations(user_id)
        _store_in_cache(user_id, results)

    return Response("200", status=200)


def _user_reservations_key(user_id):
    USER_RESERVATION_PREFIX = 'userReservations:'
    return f"{USER_RESERVATION_PREFIX}{user_id}"


def _store_in_cache(user_id, reservations):
    value = json.dumps(reservations)
    redis_client.set(_user_reservations_key(user_id), value)


def _get_from_cache(user_id):
    raw_value = redis_client.get(_user_reservations_key(user_id))
    if not raw_value:
        return None
    return json.loads(raw_value)


def _fetch_reservations(user_id):
    random_duration = (
        random.choice([1, 1, 1, 1, 1, 1, 1, 1, 2, 2, 3])
        * random.randint(1, 100)
        * 0.001
    )
    time.sleep(random_duration)
    return [{"id": random.randint(0, 12200), "user_id": user_id}]


@app.route("/")
@app.route("/up")
def up():
    return "I am running"
