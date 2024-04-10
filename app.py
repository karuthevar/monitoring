from flask import Flask
from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.instrumentation.flask import FlaskInstrumentation
from opentelemetry.instrumentation.requests import RequestsInstrumentation
from opentelemetry.sdk.resources import SERVICE_NAME, Resource
from opentelemetry.sdk.metrics import MeterProvider
from opentelemetry.exporter.otlp.proto.grpc.metric_exporter import OTLPMetricExporter
from opentelemetry.sdk.metrics.export import PeriodicExportingMetricReader
from opentelemetry.sdk._logs import LoggingHandler, get_log_emitter_provider
from opentelemetry.sdk._logs.export import OTLPHandler

import logging
import requests

# Configure Tracer
trace.set_tracer_provider(TracerProvider(
  resource=Resource.create({SERVICE_NAME: "sample-app"})
))
tracer = trace.get_tracer(__name__)
span_exporter = OTLPSpanExporter()
span_processor = BatchSpanProcessor(span_exporter)
trace.get_tracer_provider().add_span_processor(span_processor)

# Configure Meter
meter_provider = MeterProvider(resource=Resource.create({SERVICE_NAME: "sample-app"}))
metric_exporter = OTLPMetricExporter()
metric_reader = PeriodicExportingMetricReader(metric_exporter)
meter_provider.add_metric_reader(metric_reader)
meter = meter_provider.get_meter(__name__)

# Configure Logger
logger = logging.getLogger(__name__)
otlp_handler = OTLPHandler()
logger.addHandler(otlp_handler)
logger.setLevel(logging.INFO)
logging.basicConfig(handlers=[LoggingHandler()], level=logging.INFO)

app = Flask(__name__)
FlaskInstrumentation().instrument_app(app)
RequestsInstrumentation().instrument()

# Generate a counter metric
request_counter = meter.create_counter(
    "requests",
    description="Number of requests",
)

@app.route("/")
def hello():
    # Generate a trace
    with tracer.start_as_current_span("hello-span"):
        # Simulate a request that can be traced
        requests.get("http://example.com")

    # Increment the counter
    request_counter.add(1, {"method": "GET"})

    # Generate a log
    logger.info("Handled request to '/'.")

    return "Hello, World!"

if __name__ == "__main__":
    app.run(debug=True)
