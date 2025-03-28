# current_user_middleware.py
import threading

_thread_locals = threading.local()

def get_current_user():
    """Return the current user if available, else None."""
    return getattr(_thread_locals, 'user', None)

class CurrentUserMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        _thread_locals.user = request.user
        response = self.get_response(request)
        return response
