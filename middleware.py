from django.shortcuts import redirect
from django.urls import reverse

class Redirect404Middleware:
    """
    Middleware to redirect to the login page if a 404 error occurs.
    """
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        
        if response.status_code == 404:
            return redirect(reverse('login_page'))
        
        return response
