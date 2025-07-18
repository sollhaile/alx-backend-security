from celery import shared_task
from django.utils import timezone
from datetime import timedelta
from ip_tracking.models import SuspiciousIP
from django.core.cache import cache
from django.conf import settings

SENSITIVE_PATHS = ['/admin', '/login']

@shared_task
def detect_anomalies():
    request_logs = cache.get('ip_request_log', {})

    for ip, requests in request_logs.items():
        request_count = len(requests)

        # Check for high volume
        if request_count > 100:
            SuspiciousIP.objects.get_or_create(
                ip_address=ip,
                reason='Exceeded 100 requests/hour'
            )

        # Check for access to sensitive paths
        for path in requests:
            if path in SENSITIVE_PATHS:
                SuspiciousIP.objects.get_or_create(
                    ip_address=ip,
                    reason=f"Accessed sensitive path: {path}"
                )
                break

    # Reset logs
    cache.set('ip_request_log', {}, timeout=None)

