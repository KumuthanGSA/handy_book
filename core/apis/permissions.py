# Third party imports
from rest_framework.permissions import BasePermission

# Create your custom permissions here
class IsAuthenticatedAndAdmin(BasePermission):
    """
    Allows access only to authenticated users who are in the ADMIN group.
    """
    def has_permission(self, request, view):
        # Check if the user is authenticated
        if not request.user.is_authenticated:
            return False
        
        # Check if the user is in the ADMIN group
        return request.user.is_superuser
    

class IsAuthenticatedAndInUserGroup(BasePermission):
    """
    Allows access only to authenticated users who are in the USER group.
    """
    def has_permission(self, request, view):
        # Check if the user is authenticated
        if not request.user.is_authenticated:
            return False
        
        # Check if the user is in the ADMIN group
        return request.user.groups.filter(name='USER').exists()