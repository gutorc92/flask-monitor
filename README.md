# flask-monitor
A Prometheus middleware to add basic but very useful metrics for your Python Flask app.

# Metrics

The only exposed metrics (for now) are the following:

```
request_seconds_bucket{type,status, method, addr, version, isError, le}
request_seconds_count{type, status, method, addr, version, isError}
request_seconds_sum{type, status, method, addr, version, isError}
response_size_bytes{type, status, method, addr, version, isError}
dependency_up{name}
```

Where, for a specific request, `type` tells which request protocol was used (e.g. `grpc` or `http`), `status` registers the response HTTP status, `method` registers the request method, `addr` registers the requested endpoint address, `version` tells which version of your app handled the request and `isError` lets us know if the status code reported is an error or not.

In detail:

1. The `request_seconds_bucket` metric defines the histogram of how many requests are falling into the well defined buckets represented by the label `le`;

2. The `request_seconds_count` is a counter that counts the overall number of requests with those exact label occurrences;

3. The `request_seconds_sum` is a counter that counts the overall sum of how long the requests with those exact label occurrences are taking;

4. The `response_size_bytes` is a counter that computes how much data is being sent back to the user for a given request type. It captures the response size from the `content-length` response header. If there is no such header, the value exposed as metric will be zero;

5. Finally, `dependency_up` is a metric to register weather a specific dependency is up (1) or down (0). The label `name` registers the dependency name;

# How to

Add this package as a dependency:

```
pip install flask-monitor
```

```
pipenv install flask-monitor
```

## HTTP Metrics

Use it as middleware:

```python

from flask import Flask
from prometheus_client import make_wsgi_app
from werkzeug.middleware.dispatcher import DispatcherMiddleware
from werkzeug.serving import run_simple
from flask_monitor import register_metrics

app = Flask(__name__)
app.config["APP_VERSION"] = "v0.1.2"

register_metrics(app)
# Plug metrics WSGI app to your main app with dispatcher
dispatcher = DispatcherMiddleware(app.wsgi_app, {"/metrics": make_wsgi_app()})

```

One can optionally define the buckets of observation for the `request_second` histogram by doing:

```python
register_metrics(app, buckets=[0.1]); // where only one bucket (of 100ms) will be given as output in the /metrics endpoint
```

Other optional parameters are also:
2. `error_fn`: an error callback to define what **you** consider as error. `4**` and `5**` considered as errors by default;

`Monitor` also comes with a `promclient` so you can expose your custom prometheus metrics:

```js
// below we define a Gauge metric
var myGauge = new Monitor.promclient.Gauge({
    name: "my_gauge",
    help: "records my custom gauge metric",
    labelNames: [ "example_label" ]
});

...

// and here we add a metric event that will be automatically exposed to /metrics endpoint
myGauge.set({"example_label":"value"}, 220);
```

**Important**: This middleware requires to be put first in the middleware execution chain, so it can capture metrics from all possible requests.

## Dependency Metrics

For you to know when a dependency is up or down, just provide a health check callback to be `watchDependencies` function:

```js
const express = require("express");
const { Monitor } = require("@labbsr0x/express-monitor");

const app = express();
Monitor.init(app, true);

// A RegisterDepedencyMetricsCallback will be automatically injected into the HealthCheckCallback
Monitor.watchDependencies((register) => {
    // here you implement the logic to go after your dependencies and check their health
    register({ name: "Fake dependency 1", up: true});
    register({ name: "Fake dependency 2", up: false});
});
```

Now run your app and point prometheus to the defined metrics endpoint of your server.

More details on how Prometheus works, you can find it [here](https://medium.com/ibm-ix/white-box-your-metrics-now-895a9e9d34ec).

# Example

In the `example` folder, you'll find a very simple but useful example to get you started. On your terminal, navigate to the project's root folder and type:

```bash
cd example
pipenv install
```

and then

```bash
python app.py
```

On your browser, go to `localhost:5000` and then go to `localhost:5000/metrics` to see the exposed metrics.

# Big Brother

This is part of a more large application called [Big Brother](https://github.com/labbsr0x/big-brother).