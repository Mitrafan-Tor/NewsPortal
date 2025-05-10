import pytz
from django.utils import timezone
from django.conf import settings

# def get_timezone(request):
#     return {
#         'current_time': timezone.now(),
#         'timezones': pytz.common_timezones,
#         'TIME_ZONE': request.session.get('django_timezone', settings.TIME_ZONE)
#     }

def get_timezone(request):
    tzname = request.session.get('django_timezone', settings.TIME_ZONE)
    local_time = timezone.localtime(timezone.now(), pytz.timezone(tzname))

    return {
        'current_time': local_time,
        'timezones': pytz.common_timezones,
        'TIME_ZONE': tzname
    }