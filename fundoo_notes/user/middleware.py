from .models import Log
from django.db.models import F

class RequestLoggingMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Extract method and URL from the request
        method = request.method
        url = request.get_full_path()

        # Try to find an existing log entry with the same method and URL
        log_entry, created = Log.objects.get_or_create(method=method, url=url)

        if not created:
            # Increment count if the log entry already exists
            log_entry.count = F('count') + 1
            log_entry.save(update_fields=['count'])

        # Continue processing the request
        response = self.get_response(request)
        return response