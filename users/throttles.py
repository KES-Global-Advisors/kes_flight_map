from rest_framework.throttling import SimpleRateThrottle

class UsernameLoginThrottle(SimpleRateThrottle):
    scope = 'login'

    def get_cache_key(self, request, view):
        # If user is already authenticated, skip throttling or return None
        if request.user and request.user.is_authenticated:
            return None

        # Attempt to read the username from the parsed request data
        username = request.data.get('username')
        if not username:
            return None  # no username => no throttling or fallback if you prefer

        # Return a cache key that is unique per username
        return self.cache_format % {
            'scope': self.scope,
            'ident': username
        }
