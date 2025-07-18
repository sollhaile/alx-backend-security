from django.http import HttpResponseForbidden
from .models import BlockedIP, RequestLog
from django.utils.deprecation import MiddlewareMixin
from django.utils.timezone import now
from django.core.cache import cache
import requests
API_KEY = '67543ff90df84db8a763f20b582737ab'  # Get from https://ipgeolocation.io/

class IPGeolocationMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        ip = self.get_client_ip(request)
        cache_key = f'geo_{ip}'
        geo_data = cache.get(cache_key)

        if not geo_data:
            try:
                response = requests.get(
                    f'https://api.ipgeolocation.io/ipgeo?apiKey={API_KEY}&ip={ip}'
                )
                geo_data = response.json()
                cache.set(cache_key, geo_data, 24 * 3600)  # 24 hours
            except Exception as e:
                geo_data = {}

        request.country = geo_data.get('country_name')
        request.city = geo_data.get('city')

        response = self.get_response(request)
        return response

    def get_client_ip(self, request):
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip

class IPLogMiddleware(MiddlewareMixin):
    def process_request(self, request):
        ip = self.get_client_ip(request)
        
        # Check if IP is blocked
        if BlockedIP.objects.filter(ip_address=ip).exists():
            return HttpResponseForbidden("Access denied.")

        # Get geo info from previous middleware if available
        country = getattr(request, 'country', None)
        city = getattr(request, 'city', None)

        # Log the request with geo data
        RequestLog.objects.create(
            ip_address=ip,
            timestamp=now(),
            path=request.path,
            country=country,
            city=city
        )

    def get_client_ip(self, request):
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip