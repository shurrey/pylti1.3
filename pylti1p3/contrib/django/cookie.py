import django

from pylti1p3.cookie import CookieService
try:
    import Cookie
except ImportError:
    import http.cookies as Cookie

# Add support for the SameSite attribute (obsolete when PY37 is unsupported).
# # pylint: disable=protected-access
if 'samesite' not in Cookie.Morsel._reserved:
    Cookie.Morsel._reserved.setdefault('samesite', 'SameSite')


class DjangoCookieService(CookieService):
    _request = None
    _cookie_data_to_set = None

    def __init__(self, request):
        self._request = request
        self._cookie_data_to_set = {}

    def _get_key(self, key):
        return self._cookie_prefix + '-' + key

    def get_cookie(self, name):
        return self._request.get_cookie(self._get_key(name))

    def set_cookie(self, name, value, exp=3600):
        self._cookie_data_to_set = {
            'key': self._get_key(name),
            'value': value,
            'exp': exp,
        }

    def update_response(self, response):
        if self._cookie_data_to_set:
            key = self._cookie_data_to_set['key']
            kwargs = {
                'value': self._cookie_data_to_set['value'],
                'max_age': self._cookie_data_to_set['exp'],
                'secure': self._request.is_secure(),
                'httponly': True,
                'path': '/'
            }

            if self._request.is_secure():
                # samesite argument was added in Django 2.1, but samesite could be set as None only from Django 3.1
                # https://github.com/django/django/pull/11894
                django_support_samesite_none = django.VERSION[0] > 3 \
                                               or (django.VERSION[0] == 3 and django.VERSION[1] >= 1)

                # SameSite=None and Secure=True are required to work inside iframes
                if django_support_samesite_none:
                    kwargs['samesite'] = 'None'
                    response.set_cookie(key, **kwargs)
                else:
                    response.set_cookie(key, **kwargs)
                    response.cookies[key]['samesite'] = 'None'
            else:
                response.set_cookie(key, **kwargs)
