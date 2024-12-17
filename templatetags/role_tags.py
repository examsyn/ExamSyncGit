from django import template
from ..models import UserRole, Role

register = template.Library()

@register.filter
def has_role(user, role_name):
    try:
        role = Role.objects.get(role_name=role_name)
        return UserRole.objects.filter(user=user, role=role).exists()
    except Role.DoesNotExist:
        return False
