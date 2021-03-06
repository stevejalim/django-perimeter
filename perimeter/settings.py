# -*- coding: utf-8 -*-
# perimeter settings file
from os import environ

from django.conf import settings

CAST_AS_BOOL = lambda x: x in (True, 'true', 'True')
CAST_AS_INT = lambda x: int(x)


def get_setting(setting_name, default_value, cast_func=lambda x: x):
    """Return setting from django.conf or os.environ.

    This function will look up a setting in the os.environ first, and
    then if not found there, the django.conf.settings. Values from env
    vars are strings by default, so the cast_func can be used to convert
    strings into booleans or integers etc.

    Args:
        setting_name: string - the name of the setting to fetch
        cast_func: function - a function that is applied to the value,
            commonly used to cast string values to a bool, int etc.
        default_value: value to use if the setting_name is not found

    """
    return cast_func(
        environ.get(setting_name) or
        getattr(settings, setting_name, default_value)
    )


# if False, the middleware will be disabled
PERIMETER_ENABLED = get_setting('PERIMETER_ENABLED', False, cast_func=CAST_AS_BOOL)
# request.session key used to store user's token
PERIMETER_SESSION_KEY = get_setting('PERIMETER_SESSION_KEY', "perimeter")
# default expiry, in days, of a token
PERIMETER_DEFAULT_EXPIRY = get_setting('PERIMETER_DEFAULT_EXPIRY', 7, cast_func=CAST_AS_INT)

if settings.DEBUG:
    print "PERIMETER_ENABLED: ", PERIMETER_ENABLED
    print "PERIMETER_DEFAULT_EXPIRY: ", PERIMETER_DEFAULT_EXPIRY
