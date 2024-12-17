# decorators.py
from django.http import HttpResponseForbidden
from functools import wraps
from django.shortcuts import redirect
from .models import UserRole

import logging

logger = logging.getLogger(__name__)

def role_required(required_role):
    def decorator(view_func):
        @wraps(view_func)
        def _wrapped_view(request, *args, **kwargs):
            if not request.user.is_authenticated:
                logger.debug(f'User not authenticated. Redirecting to select_login_page.')
                return redirect('select_login_page')
            
            user_roles = UserRole.objects.filter(user=request.user).values_list('role__role_name', flat=True)
            if required_role.lower() not in [r.lower() for r in user_roles]:
                logger.debug(f'User does not have required role: {required_role}. Redirecting to unauthorized page.')
                return redirect('unauthorized')
            
            return view_func(request, *args, **kwargs)
        return _wrapped_view
    return decorator


def guest_required(view_func):
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        if request.user.is_authenticated:
            # Redirect to a default page or dashboard based on the user's role
            user_roles = UserRole.objects.filter(user=request.user).values_list('role__role_name', flat=True)
            if 'administrator' in [r.lower() for r in user_roles]:
                return redirect('dashboard_administrator')
            elif 'scheduler' in [r.lower() for r in user_roles]:
                return redirect('dashboard_scheduler')
            elif 'dean' in [r.lower() for r in user_roles]:
                return redirect('dashboard_dean')
            elif 'faculty' in [r.lower() for r in user_roles]:
                return redirect('dashboard_faculty')
            elif 'bayanihan leader' in [r.lower() for r in user_roles]:
                return redirect('dashboard_faculty')
            return redirect('select_login_page')  # Redirect to a default page if no specific role is found
        return view_func(request, *args, **kwargs)
    return _wrapped_view
