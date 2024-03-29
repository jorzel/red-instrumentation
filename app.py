import random
import time
from urllib.parse import urlparse

import prometheus_client
from flask import Flask, request
from prometheus_client import Histogram, make_wsgi_app
from werkzeug import Response
from werkzeug.middleware.dispatcher import DispatcherMiddleware

app = Flask(__name__)
app.wsgi_app = DispatcherMiddleware(app.wsgi_app, {"/metrics": make_wsgi_app()})

prometheus_client.REGISTRY.unregister(prometheus_client.GC_COLLECTOR)
prometheus_client.REGISTRY.unregister(prometheus_client.PLATFORM_COLLECTOR)
prometheus_client.REGISTRY.unregister(prometheus_client.PROCESS_COLLECTOR)

HTTP_REQUEST_DURATION = Histogram(
    "http_request_duration",
    "Requests durations",
    ["method", "path", "code"],
    buckets=[0.01, 0.1, 0.5, 2, float("inf")],
)


def observe_http(func):
    def wrapper(*args, **kwargs):
        start = time.time()
        response = func(*args, **kwargs)
        end = time.time()
        parts = urlparse(request.url)
        HTTP_REQUEST_DURATION.labels(
            method=request.method,
            code=response.status_code,
            path=parts.path,
        ).observe(end - start)
        return response

    return wrapper


@app.route("/synthetic")
@observe_http
def synthetic():
    random_duration = (
        random.choice([1, 1, 1, 1, 1, 1, 1, 1, 2, 2, 3])
        * random.randint(1, 100)
        * 0.001
    )
    time.sleep(random_duration)

    response_code = random.choice([200, 200, 200, 200, 200, 400, 401, 500])
    return Response(str(response_code), status=response_code)


@app.route("/")
@app.route("/up")
def up():
    return "I am running"
