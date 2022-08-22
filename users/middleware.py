from django.utils import timezone
import zoneinfo


class TimezoneMiddleware:
    """Middleware to apply timezone settings"""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.user.is_authenticated:
            tzname = request.user.profile.timezone
            if tzname:
                timezone.activate(zoneinfo.ZoneInfo(tzname))
            else:
                timezone.deactivate()
        return self.get_response(request)
