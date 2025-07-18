# ip_tracking/views.py

from django.http import JsonResponse
from django_ratelimit.decorators import ratelimit

@ratelimit(key='ip', rate='10/m', method='POST', block=True)
@ratelimit(key='ip', rate='5/m', method='GET', block=True)
def login_view(request):
    if getattr(request, 'limited', False):
        return JsonResponse({'error': 'Too many requests'}, status=429)

    # Simulated login logic
    return JsonResponse({'message': 'Login attempt'})
