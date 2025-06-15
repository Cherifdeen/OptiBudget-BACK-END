# authentication.py
from django.utils import timezone
from datetime import timedelta
from rest_framework.authentication import TokenAuthentication
from rest_framework.exceptions import AuthenticationFailed

class ExpiringTokenAuthentication(TokenAuthentication):
    def authenticate_credentials(self, key):
        model = self.get_model()
        try:
            token = model.objects.select_related('user').get(key=key)
        except model.DoesNotExist:
            raise AuthenticationFailed('Token invalide.')

        if not token.user.is_active:
            raise AuthenticationFailed('Utilisateur inactif ou supprimé.')

        # Vérifier l'expiration (ex: 24 heures)
        if token.created < timezone.now() - timedelta(hours=24):
            token.delete()  # ✅ Suppression immédiate du token expiré
            raise AuthenticationFailed('Token expiré.')

        return (token.user, token)