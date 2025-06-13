# permissions.py
from rest_framework.permissions import BasePermission


class IsEntrepriseUser(BasePermission):
    """
    Permission personnalisée pour vérifier si l'utilisateur a un compte entreprise
    """
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        
        # Supposons que votre CustomUser a un champ 'type_compte'
        return getattr(request.user, 'type_compte', None) == 'entreprise'


class IsParticulierUser(BasePermission):
    """
    Permission personnalisée pour vérifier si l'utilisateur a un compte particulier
    """
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        
        return getattr(request.user, 'type_compte', None) == 'particulier'