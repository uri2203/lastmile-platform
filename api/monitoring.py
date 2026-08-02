"""
MONITORING MODULE - Sentry + Health Metrics
Inicializa Sentry SDK si SENTRY_DSN esta configurado.
Proporciona helpers para metricas de monitoreo.
"""

import os
import logging
import time
from functools import wraps

logger = logging.getLogger(__name__)


def init_monitoring(app):
    """Initialize Sentry error monitoring if DSN is configured."""
    sentry_dsn = os.environ.get('SENTRY_DSN')
    if sentry_dsn:
        try:
            import sentry_sdk
            from sentry_sdk.integrations.flask import FlaskIntegration

            sentry_sdk.init(
                dsn=sentry_dsn,
                integrations=[FlaskIntegration()],
                traces_sample_rate=float(os.environ.get('SENTRY_TRACES_RATE', '0.1')),
                environment=os.environ.get('FLASK_ENV', 'development'),
                release=os.environ.get('APP_VERSION', '4.0.0'),
                attach_stacktrace=True,
                send_default_pii=False,
            )
            app.logger.info('[MONITORING] Sentry initialized successfully')
        except ImportError:
            app.logger.warning('[MONITORING] sentry-sdk not installed. Run: pip install sentry-sdk[flask]')
        except Exception as e:
            app.logger.error(f'[MONITORING] Sentry init failed: {e}')
    else:
        app.logger.info('[MONITORING] Sentry DSN not configured, monitoring disabled')

    _init_metrics(app)


def _init_metrics(app):
    """Initialize basic request metrics tracking."""
    app.config['METRICS'] = {
        'requests_total': 0,
        'errors_total': 0,
        'start_time': time.time(),
    }

    @app.after_request
    def _track_metrics(response):
        metrics = app.config.get('METRICS', {})
        metrics['requests_total'] = metrics.get('requests_total', 0) + 1
        if response.status_code >= 500:
            metrics['errors_total'] = metrics.get('errors_total', 0) + 1
        return response


def capture_exception(error, extra=None):
    """Capture an exception to Sentry with extra context."""
    try:
        import sentry_sdk
        with sentry_sdk.push_scope() as scope:
            if extra:
                for key, value in extra.items():
                    scope.set_extra(key, value)
            sentry_sdk.capture_exception(error)
    except Exception:
        pass


def capture_message(message, level='info', extra=None):
    """Capture a message to Sentry."""
    try:
        import sentry_sdk
        with sentry_sdk.push_scope() as scope:
            if extra:
                for key, value in extra.items():
                    scope.set_extra(key, value)
            sentry_sdk.capture_message(message, level=level)
    except Exception:
        pass


def monitor_endpoint(func):
    """Decorator to add monitoring context to a Flask endpoint."""
    @wraps(func)
    def wrapper(*args, **kwargs):
        start = time.time()
        try:
            result = func(*args, **kwargs)
            elapsed = (time.time() - start) * 1000
            if elapsed > 5000:
                capture_message(
                    f'Slow endpoint: {func.__name__} took {elapsed:.0f}ms',
                    level='warning'
                )
            return result
        except Exception as e:
            capture_exception(e, extra={'endpoint': func.__name__})
            raise
    return wrapper
