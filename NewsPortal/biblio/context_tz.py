import pytz
from django.utils import timezone
from django.conf import settings

def get_timezone(request):
    return {
        'current_time': timezone.now(),
        'timezones': pytz.common_timezones,
        'TIME_ZONE': request.session.get('django_timezone', settings.TIME_ZONE)
    }