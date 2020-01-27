import time

from flask import request, current_app

from prometheus_client import Counter, Histogram, Info

#
# Metrics registration
#


METRICS_REQUEST_LATENCY = Histogram(
    "request_seconds",
    "records in a histogram the number of http requests and their duration in seconds",
    ["type", "status", "method", "addr", "version", "isError"]
)

METRICS_REQUEST_SIZE = Counter(
    "response_size_bytes",
    "counts the size of each http response",
    ["type", "status", "method", "addr", "version", "isError"],
)

METRICS_INFO = Info(
    "dependency_up", 
    "records if a dependency is up or down. 1 for up, 0 for down"
)


#
# Request callbacks
#

def is_error(code):
    code = str(code) if type(code) is int else code
    return code.startswith("5") or code.startswith("4")


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
    print("error_status", error_status)
    METRICS_REQUEST_LATENCY.labels("http", response.status_code, request.method, request.path, app_version, error_status).observe(
        request_latency
    )
    METRICS_REQUEST_SIZE.labels(
        "http", response.status_code, request.method, request.path, app_version, error_status
    ).inc(size_request)
    return response


def register_metrics(app, app_version=None, app_config=None, error_fn=None):
    """
    Register metrics middlewares

    Use in your application factory (i.e. create_app):
    register_middlewares(app, settings["version"], settings["config"])

    Flask application can register more than one before_request/after_request.
    Beware! Before/after request callback stored internally in a dictionary.
    Before CPython 3.6 dictionaries didn't guarantee keys order, so callbacks
    could be executed in arbitrary order.
    """
    if error_fn is not None:
        print("passou")
        is_error.__code__ = error_fn.__code__
        print("is_error", is_error("200"))
    app.before_request(before_request)
    app.after_request(after_request)
    # METRICS_INFO.info({"version": app_version, "config": app_config})
