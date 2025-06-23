from django.http import JsonResponse
from django.urls import resolve
from optibudget_admin.models import ClientKey
import re
from django.conf import settings
from django.utils.deprecation import MiddlewareMixin
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.utils.functional import SimpleLazyObject
from django.contrib.auth.models import AnonymousUser
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework_simplejwt.exceptions import InvalidToken, TokenError
from rest_framework_simplejwt.tokens import AccessToken
import json


class CSRFExemptionMiddleware(MiddlewareMixin):
    """Middleware pour exclure certaines routes de la protection CSRF"""
    
    def process_request(self, request):
        # Vérifier si l'URL actuelle doit être exemptée de CSRF
        if hasattr(settings, 'CSRF_EXEMPT_URLS'):
            for pattern in settings.CSRF_EXEMPT_URLS:
                if re.match(pattern, request.path):
                    # Marquer la requête comme exemptée de CSRF
                    request._dont_enforce_csrf_checks = True
                    break
        
        return None


class ClientKeyMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response
        
        # URLs exemptées totalement (pas besoin de clé même hors navigateur)
        self.free_exempt_urls = [
            'optibudget_admin:login',
            'optibudget_admin:profil',
            'optibudget_admin:reset_password',
            'optibudget_admin:search_account',
            'optibudget_admin:change_password',
            'optibudget_admin:signup',
            'optibudget_admin:dashboardadmin',
            'optibudget_admin:parametre',
            'accounts:password_reset_api',
        ]

        # URLs spéciales : clé obligatoire hors navigateur
        self.browser_allowed_urls = [
            'accounts:verify_email',
            'accounts:password_reset_request',
            'accounts:password_reset_confirm',
            'accounts:login',
            'accounts:token_refresh',
            'accounts:user-choices',
            'accounts:register',
            'accounts:password_reset_done',
            'accounts:password_reset_complete',
            'accounts:email_verifiation_success',
        ]

    def __call__(self, request):
        path = request.path
        
        # Exclure l'admin (facultatif)
        if path.startswith('/admin/'):
            return self.get_response(request)

        # Exclure spécifiquement la route password-reset API
        if path == '/api/accounts/password-reset/':
            return self.get_response(request)

        try:
            match = resolve(path)
            url_name = match.url_name
        except Exception:
            url_name = None

        # Cas 1 : URLs exemptées totalement (libres)
        if url_name in self.free_exempt_urls:
            return self.get_response(request)

        # Cas 2 : URLs spéciales "user-register/login/logout"
        if url_name in self.browser_allowed_urls:
            if self.is_browser_request(request):
                # Requête venant d'un navigateur -> OK sans clé
                return self.get_response(request)
            else:
                # Requête non navigateur -> clé obligatoire
                client_key = request.headers.get('X-Client-Key')
                if not client_key:
                    return JsonResponse({'detail': 'Clé client manquante.'}, status=401)
                try:
                    client = ClientKey.objects.get(key=client_key, is_active=True)
                except ClientKey.DoesNotExist:
                    return JsonResponse({'detail': 'Clé client invalide ou inactive.'}, status=403)
                request.client_key = client
                return self.get_response(request)

        # Cas 3 : Pour toutes les autres URLs

        # Autoriser les requêtes GET sans clé, comme avant
        if request.method == 'GET':
            return self.get_response(request)

        # Autoriser toutes les requêtes provenant d'un navigateur classique
        if self.is_browser_request(request):
            return self.get_response(request)

        # Exiger la clé client pour les autres requêtes (API, scripts, etc.)
        client_key = request.headers.get('X-Client-Key')
        if not client_key:
            return JsonResponse({'detail': 'Clé client manquante.'}, status=401)
        try:
            client = ClientKey.objects.get(key=client_key, is_active=True)
        except ClientKey.DoesNotExist:
            return JsonResponse({'detail': 'Clé client invalide ou inactive.'}, status=403)
        request.client_key = client
        return self.get_response(request)

    def is_browser_request(self, request):
        """
        Détecte si la requête provient d'un navigateur web classique.
        On s'appuie sur le header User-Agent qui contient des signatures de navigateurs.
        """
        user_agent = request.headers.get('User-Agent', '').lower()
        if not user_agent:
            return False

        browsers_signatures = [
            'mozilla',  
            'chrome',
            'safari',
            'firefox',
            'edge',
            'opera',
            'msie', 
            'trident',  
        ]

        return any(signature in user_agent for signature in browsers_signatures)
