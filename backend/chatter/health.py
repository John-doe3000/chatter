"""
Health check views for Docker healthchecks.
"""
from django.http import JsonResponse
from django.views import View
from django.db import connection
from django.core.cache import cache


class HealthCheckView(View):
    """
    Health check endpoint for Docker healthchecks.
    Returns 200 if the application and database are healthy.
    """
    
    def get(self, request):
        # Check database connection
        try:
            with connection.cursor() as cursor:
                cursor.execute("SELECT 1")
                cursor.fetchone()
            db_status = "healthy"
        except Exception as e:
            db_status = f"unhealthy: {str(e)}"
        
        # Check cache (optional)
        try:
            cache.set('healthcheck', 'ok', 10)
            cache_status = "healthy" if cache.get('healthcheck') == 'ok' else "unhealthy"
        except Exception:
            cache_status = "unavailable"
        
        status = 200 if db_status == "healthy" else 503
        
        return JsonResponse({
            "status": "healthy" if status == 200 else "unhealthy",
            "database": db_status,
            "cache": cache_status,
        }, status=status)