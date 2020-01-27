import time
import threading
import traceback
import logging
from flask import request, current_app
from prometheus_client import Counter, Histogram, Info, Gauge

#
# Request callbacks
#

METRICS_INFO = Gauge(
    "application_info", 
    "records static application info such as it's semantic version number",
    ["version"]
)

DEPENDENCY_UP = Gauge(
    'dependency_up',
    'records if a dependency is up or down. 1 for up, 0 for down',
    ["name"]
)

def is_error(code):
    code = str(code) if type(code) is int else code
    return code.startswith("5") or code.startswith("4")

#
# Metrics registration
#
def register_metrics(app, buckets=[0.1, 0.3, 1.5, 10.5], error_fn=None):
    """
    Register metrics middlewares

    Use in your application factory (i.e. create_app):
    register_middlewares(app, settings["version"], settings["config"])

    Flask application can register more than one before_request/after_request.
    Beware! Before/after request callback stored internally in a dictionary.
    Before CPython 3.6 dictionaries didn't guarantee keys order, so callbacks
    could be executed in arbitrary order.
    """
    METRICS_REQUEST_LATENCY = Histogram(
        "request_seconds",
        "records in a histogram the number of http requests and their duration in seconds",
        ["type", "status", "method", "addr", "version", "isError"],
        buckets=buckets
    )

    METRICS_REQUEST_SIZE = Counter(
        "response_size_bytes",
        "counts the size of each http response",
        ["type", "status", "method", "addr", "version", "isError"],
    )
    
    def before_request():
        """
        Get start time of a request
        """
        request._prometheus_metrics_request_start_time = time.time()


    def after_request(response):
        """
        Register Prometheus metrics after each request
        """
        app_version = current_app.config.get("APP_VERSION", "0.0.0")
        size_request = int(response.headers.get("Content-Length", 0))
        request_latency = time.time() - request._prometheus_metrics_request_start_time
        error_status = is_error(response.status_code)
        METRICS_REQUEST_LATENCY \
            .labels("http", response.status_code, request.method, request.path, app_version, error_status) \
            .observe(request_latency)
        METRICS_REQUEST_SIZE.labels(
            "http", response.status_code, request.method, request.path, app_version, error_status
        ).inc(size_request)
        return response
    if error_fn is not None:
        is_error.__code__ = error_fn.__code__
    app.before_request(before_request)
    app.after_request(after_request)

def watch_dependencies(dependency, func, time_execution=1500):
    
    def thread_function():
        x = threading.Timer(time_execution, lambda x: x + 1)
        x.start()
        x.join()
        response = func()
        DEPENDENCY_UP.labels(dependency).set(response)
        thread_function()
    x = threading.Timer(10, thread_function)
    x.start()

