"""Distributed tracing — OpenTelemetry integration for request tracing."""

from opentelemetry import trace
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor, ConsoleSpanExporter

from app.shared.config import get_settings
from app.shared.logging import get_logger

logger = get_logger(__name__)

_tracer_provider: TracerProvider | None = None


def setup_tracing() -> None:
    """Initialize OpenTelemetry tracing.

    In production, configure OTLP exporter for Jaeger/Tempo.
    In development, use console exporter for debugging.
    """
    global _tracer_provider

    settings = get_settings()
    resource = Resource.create(
        {
            "service.name": "upcp-backend",
            "service.version": "0.1.0",
            "deployment.environment": settings.env,
        }
    )

    _tracer_provider = TracerProvider(resource=resource)

    if settings.env in ("local", "test"):
        exporter = ConsoleSpanExporter()
        _tracer_provider.add_span_processor(BatchSpanProcessor(exporter))
    else:
        try:
            from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter

            otlp_exporter = OTLPSpanExporter()
            _tracer_provider.add_span_processor(BatchSpanProcessor(otlp_exporter))
            logger.info("Tracing initialized with OTLP exporter")
        except ImportError:
            logger.warning("OTLP exporter not installed, using console")
            fallback_exporter = ConsoleSpanExporter()
            _tracer_provider.add_span_processor(BatchSpanProcessor(fallback_exporter))

    trace.set_tracer_provider(_tracer_provider)
    logger.info(f"Tracing initialized for env={settings.env}")


def get_tracer(name: str = "upcp") -> trace.Tracer:
    """Get a named tracer."""
    return trace.get_tracer(name)
