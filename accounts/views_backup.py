from django.contrib.auth import login, logout
from django.contrib.auth.tokens import default_token_generator
from django.conf import settings
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes, force_str
from django.shortcuts import get_object_or_404, render, redirect
from django.contrib import messages
from django.contrib.auth.forms import SetPasswordForm
from django.contrib.auth.views import PasswordResetView as DjangoPasswordResetView
from django.contrib.auth.views import PasswordResetDoneView as DjangoPasswordResetDoneView
from django.contrib.auth.views import PasswordResetConfirmView as DjangoPasswordResetConfirmView
from django.contrib.auth.views import PasswordResetCompleteView as DjangoPasswordResetCompleteView
from django.urls import reverse_lazy
from rest_framework import status, permissions, generics
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.authtoken.models import Token
from rest_framework.pagination import PageNumberPagination
from rest_framework.filters import SearchFilter, OrderingFilter
from django_filters.rest_framework import DjangoFilterBackend
from django.contrib.auth import authenticate
from tasks.sendMail import send_email_task
from Optibudget.settings import DEFAULT_FROM_EMAIL
from django.contrib.auth.models import User
from django.utils.crypto import get_random_string
from django.core.mail import send_mail
from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework_simplejwt.tokens import RefreshToken
from django.utils import timezone
from datetime import timedelta
import uuid
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from Optibudget.swagger_config import JWT_SECURITY
from .utils import send_password_reset_request_email, send_password_reset_success_email, send_password_changed_email
from django import forms

from .models import CustomUser, UserPreferences, UserDevice, LoginAttempt
from .serializers import (
    CustomUserSerializer, UserRegistrationSerializer,
    UserProfileSerializer, UserPreferencesSerializer,
    UserListSerializer, UserPreferencesUpdateSerializer,
    UserChoicesSerializer, CustomTokenObtainPairSerializer, DeviceRegistrationSerializer,
    ChangePasswordSerializer, EmailVerificationSerializer, PasswordResetRequestSerializer, PasswordResetConfirmSerializer, LoginAttemptSerializer, UserDeviceSerializer
)


class StandardResultsSetPagination(PageNumberPagination):
    """Pagination personnalisée"""
    page_size = 20
    page_size_query_param = 'page_size'
    max_page_size = 100


class CustomTokenObtainPairView(TokenObtainPairView):
    """Vue personnalisée pour l'obtention de tokens JWT"""
    serializer_class = CustomTokenObtainPairSerializer


class UserRegistrationView(generics.CreateAPIView):
    """Vue pour l'inscription d'un nouvel utilisateur"""
    queryset = CustomUser.objects.all()
    serializer_class = UserRegistrationSerializer
    permission_classes = [permissions.AllowAny]
    
    @swagger_auto_schema(
        operation_description="Inscription d'un nouvel utilisateur",
        operation_summary="Créer un nouveau compte utilisateur",
        request_body=UserRegistrationSerializer,
        responses={
            201: openapi.Response(
                description="Utilisateur créé avec succès",
                schema=UserRegistrationSerializer
            ),
            400: openapi.Response(
                description="Données invalides",
                examples={
                    "application/json": {
                        "username": ["Ce nom d'utilisateur existe déjà."],
                        "email": ["Cette adresse email existe déjà."],
                        "password": ["Ce mot de passe est trop court."]
                    }
                }
            )
        },
        tags=["Authentification"],
        security=[]  # Pas d'authentification requise pour l'inscription
    )
    def post(self, request, *args, **kwargs):
        return super().post(request, *args, **kwargs)
    
    def perform_create(self, serializer):
        user = serializer.save()
        
        # Envoyer l'email de vérification
        self.send_verification_email(user)
        
        return user
    
    def send_verification_email(self, user):
        """Envoie un email de vérification"""
        subject = 'Vérifiez votre adresse email - Optibudget'
        html_message = render_to_string('emails/email_verification.html', {
            'user': user,
            'verification_url': f"{self.request.scheme}://{self.request.get_host()}/api/accounts/verify-email/{user.email_verification_token}/"
        })
        plain_message = strip_tags(html_message)
        
        send_mail(
            subject,
            plain_message,
            DEFAULT_FROM_EMAIL,
            [user.email],
            html_message=html_message,
            fail_silently=False,
        )


class UserLoginView(APIView):
    """
    Vue pour la connexion des utilisateurs
    """
    permission_classes = [permissions.AllowAny]
    
    def post(self, request):
        email = request.data.get('email')
        password = request.data.get('password')
        
        if not email or not password:
            return Response({
                'error': 'Email et mot de passe requis'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Authentification
        user = authenticate(email=email, password=password)
        
        if user:
            # Connexion de l'utilisateur
            login(request, user)
            
            # Récupération ou création du token
            token, created = Token.objects.get_or_create(user=user)
            
            response_data = {
                'message': 'Connexion réussie',
                'user': UserProfileSerializer(user).data,
                'token': token.key
            }
            
            return Response(response_data, status=status.HTTP_200_OK)
        else:
            return Response({
                'error': 'Email ou mot de passe incorrect'
            }, status=status.HTTP_400_BAD_REQUEST)


class UserLogoutView(APIView):
    """
    Vue pour la déconnexion des utilisateurs
    """
    permission_classes = [permissions.IsAuthenticated]
    
    def post(self, request):
        try:
            # Suppression du token
            request.user.auth_token.delete()
        except:
            pass
        
        # Déconnexion
        logout(request)
        
        return Response(
            {'message': 'Déconnexion réussie'}, 
            status=status.HTTP_200_OK
        )


class UserProfileView(generics.RetrieveUpdateAPIView):
    """Vue pour le profil utilisateur"""
    serializer_class = UserProfileSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    @swagger_auto_schema(
        operation_description="Récupérer le profil de l'utilisateur connecté",
        operation_summary="Obtenir le profil utilisateur",
        responses={
            200: openapi.Response(
                description="Profil utilisateur récupéré avec succès",
                schema=UserProfileSerializer
            ),
            401: "Non authentifié"
        },
        tags=["Profil Utilisateur"],
        security=JWT_SECURITY  # Authentification JWT requise
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)
    
    @swagger_auto_schema(
        operation_description="Mettre à jour le profil de l'utilisateur connecté",
        operation_summary="Modifier le profil utilisateur",
        request_body=UserProfileSerializer,
        responses={
            200: openapi.Response(
                description="Profil utilisateur mis à jour avec succès",
                schema=UserProfileSerializer
            ),
            400: "Données invalides",
            401: "Non authentifié"
        },
        tags=["Profil Utilisateur"],
        security=JWT_SECURITY  # Authentification JWT requise
    )
    def put(self, request, *args, **kwargs):
        return super().put(request, *args, **kwargs)
    
    @swagger_auto_schema(
        operation_description="Mettre à jour partiellement le profil de l'utilisateur connecté",
        operation_summary="Modifier partiellement le profil utilisateur",
        request_body=UserProfileSerializer,
        responses={
            200: openapi.Response(
                description="Profil utilisateur mis à jour avec succès",
                schema=UserProfileSerializer
            ),
            400: "Données invalides",
            401: "Non authentifié"
        },
        tags=["Profil Utilisateur"],
        security=JWT_SECURITY  # Authentification JWT requise
    )
    def patch(self, request, *args, **kwargs):
        return super().patch(request, *args, **kwargs)
    
    def get_object(self):
        return self.request.user


class PasswordChangeView(APIView):
    """
    Vue pour changer le mot de passe
    """
    permission_classes = [permissions.IsAuthenticated]
    
    def post(self, request):
        serializer = PasswordChangeSerializer(
            data=request.data,
            context={'request': request}
        )
        if serializer.is_valid():
            serializer.save()
            return Response({
                'message': 'Mot de passe changé avec succès'
            })
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class PasswordVerificationView(APIView):
    """
    Vue pour vérifier si le mot de passe saisi par l'utilisateur est correct
    """
    permission_classes = [permissions.IsAuthenticated]
    
    def post(self, request):
        """
        Vérifier le mot de passe de l'utilisateur connecté
        """
        password = request.data.get('password')
        
        if not password:
            return Response(
                {'error': 'Le mot de passe est requis'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Vérification du mot de passe avec authenticate
        user = authenticate(
            username=request.user.username, 
            password=password
        )
        
        if user is not None:
            return Response({
                'valid': True,
                'message': 'Mot de passe correct'
            })
        else:
            return Response({
                'valid': False,
                'message': 'Mot de passe incorrect'
            }, status=status.HTTP_400_BAD_REQUEST)
        

class UserPreferencesView(generics.RetrieveUpdateAPIView):
    """Vue pour les préférences utilisateur"""
    serializer_class = UserPreferencesSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_object(self):
        user = self.request.user
        preferences, created = UserPreferences.objects.get_or_create(user=user)
        return preferences


class UserListView(generics.ListAPIView):
    """
    Vue pour lister les utilisateurs (admin seulement)
    """
    queryset = CustomUser.objects.all()
    serializer_class = UserListSerializer
    permission_classes = [permissions.IsAdminUser]
    pagination_class = StandardResultsSetPagination
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    
    # Filtres
    filterset_fields = ['compte', 'pays', 'statut_compte', 'is_active']
    search_fields = ['username', 'email', 'first_name', 'last_name']
    ordering_fields = ['date_joined', 'username', 'email']
    ordering = ['-date_joined']


class UserDetailView(generics.RetrieveUpdateDestroyAPIView):
    """
    Vue pour récupérer, mettre à jour ou supprimer un utilisateur spécifique (admin)
    """
    queryset = CustomUser.objects.all()
    permission_classes = [permissions.IsAdminUser]
    
    def get_serializer_class(self):
        # Éviter les erreurs lors de la génération du schéma Swagger
        if getattr(self, 'swagger_fake_view', False):
            return UserProfileSerializer
            
        if self.request.method == 'GET':
            return UserProfileSerializer
        return UserProfileSerializer  # Utiliser UserProfileSerializer au lieu de UserUpdateSerializer
    
    def destroy(self, request, *args, **kwargs):
        """Désactiver l'utilisateur au lieu de le supprimer"""
        user = self.get_object()
        user.is_active = False
        user.save()
        return Response({
            'message': 'Utilisateur désactivé avec succès'
        })


class UserActivationView(APIView):
    """
    Vue pour activer/désactiver un utilisateur (admin)
    """
    permission_classes = [permissions.IsAdminUser]
    
    def post(self, request, pk):
        user = get_object_or_404(CustomUser, pk=pk)
        action = request.data.get('action')  # 'activate' ou 'deactivate'
        
        if action == 'activate':
            user.is_active = True
            user.statut_compte = True
            message = 'Utilisateur activé avec succès'
        elif action == 'deactivate':
            user.is_active = False
            user.statut_compte = False
            message = 'Utilisateur désactivé avec succès'
        else:
            return Response(
                {'error': 'Action non valide'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        user.save()
        return Response({
            'message': message,
            'user': UserListSerializer(user).data
        })


class UserStatsView(APIView):
    """
    Vue pour les statistiques des utilisateurs (admin)
    """
    permission_classes = [permissions.IsAdminUser]
    
    def get(self, request):
        stats = {
            'total_users': CustomUser.objects.count(),
            'active_users': CustomUser.objects.filter(is_active=True).count(),
            'inactive_users': CustomUser.objects.filter(is_active=False).count(),
            'enterprise_accounts': CustomUser.objects.filter(compte='entreprise').count(),
            'individual_accounts': CustomUser.objects.filter(compte='particulier').count(),
            'users_by_country': dict(
                CustomUser.objects.values_list('pays')
                .annotate(count=models.Count('pays'))
                .order_by('-count')
            )
        }
        return Response(stats)


class UserChoicesView(APIView):
    """
    Vue pour récupérer les choix disponibles pour les formulaires
    """
    permission_classes = [permissions.AllowAny]
    
    def get(self, request):
        serializer = UserChoicesSerializer()
        return Response(serializer.to_representation(None))


# Vues basées sur les fonctions pour des cas spécifiques

@api_view(['POST'])
@permission_classes([permissions.AllowAny])
def check_username_availability(request):
    """
    Vérifier la disponibilité d'un nom d'utilisateur
    """
    username = request.data.get('username')
    if not username:
        return Response(
            {'error': 'Le nom d\'utilisateur est requis'}, 
            status=status.HTTP_400_BAD_REQUEST
        )
    
    is_available = not CustomUser.objects.filter(username=username).exists()
    return Response({
        'username': username,
        'available': is_available
    })


@api_view(['POST'])
@permission_classes([permissions.AllowAny])
def check_email_availability(request):
    """
    Vérifier la disponibilité d'un email
    """
    email = request.data.get('email')
    if not email:
        return Response(
            {'error': 'L\'email est requis'}, 
            status=status.HTTP_400_BAD_REQUEST
        )
    
    is_available = not CustomUser.objects.filter(email=email).exists()
    return Response({
        'email': email,
        'available': is_available
    })


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def upload_profile_image(request):
    """
    Upload d'image de profil
    """
    if 'image' not in request.FILES:
        return Response(
            {'error': 'Aucune image fournie'}, 
            status=status.HTTP_400_BAD_REQUEST
        )
    
    user = request.user
    user.img_profil = request.FILES['image']
    user.save()
    
    return Response({
        'message': 'Image de profil mise à jour avec succès',
        'image_url': user.img_profil.url if user.img_profil else None
    })


@api_view(['DELETE'])
@permission_classes([permissions.IsAuthenticated])
def delete_profile_image(request):
    """
    Supprimer l'image de profil
    """
    user = request.user
    if user.img_profil:
        user.img_profil.delete()
        user.img_profil = None
        user.save()
    
    return Response({
        'message': 'Image de profil supprimée avec succès'
    })


@api_view(['POST'])
@permission_classes([permissions.AllowAny])
def password_reset_request(request):
    """
    Demande de réinitialisation de mot de passe
    """
    email = request.data.get('email')
    if not email:
        return Response(
            {'error': 'L\'email est requis'}, 
            status=status.HTTP_400_BAD_REQUEST
        )
    
    try:
        user = CustomUser.objects.get(email=email)
        
        # Génération du token de réinitialisation
        token = default_token_generator.make_token(user)
        uid = urlsafe_base64_encode(force_bytes(user.pk))
        
        # Envoi de l'email avec notre fonction personnalisée
        reset_url = f"{self.request.scheme}://{self.request.get_host()}/accounts/reset-password/{uid}/{token}/"
        send_password_reset_request_email(user, reset_url)
        
        return Response({
            'message': 'Un email de réinitialisation a été envoyé'
        })
    
    except CustomUser.DoesNotExist:
        # Pour des raisons de sécurité, on ne révèle pas si l'email existe
        return Response({
            'message': 'Si cet email existe, un lien de réinitialisation a été envoyé'
        })


@api_view(['POST'])
@permission_classes([permissions.AllowAny])
def password_reset_confirm(request, uidb64, token):
    """
    Confirmation de réinitialisation de mot de passe
    """
    try:
        uid = force_str(urlsafe_base64_decode(uidb64))
        user = CustomUser.objects.get(pk=uid)
    except (TypeError, ValueError, OverflowError, CustomUser.DoesNotExist):
        user = None
    
    if user and default_token_generator.check_token(user, token):
        new_password = request.data.get('new_password')
        if not new_password:
            return Response(
                {'error': 'Le nouveau mot de passe est requis'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Validation du mot de passe
        try:
            from django.contrib.auth.password_validation import validate_password
            validate_password(new_password)
        except Exception as e:
            return Response(
                {'error': str(e)}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        user.set_password(new_password)
        user.save()
        
        # Envoyer l'email de confirmation avec template HTML
        send_password_reset_success_email(user)
        
        return Response({
            'message': 'Mot de passe réinitialisé avec succès'
        })
    
    return Response(
        {'error': 'Lien de réinitialisation invalide'}, 
        status=status.HTTP_400_BAD_REQUEST
    )


class EmailVerificationView(APIView):
    """Vue pour la vérification d'email"""
    permission_classes = [permissions.AllowAny]
    
    def get(self, request, token):
        try:
            user = CustomUser.objects.get(email_verification_token=token)
            user.is_email_verified = True
            user.email_verification_token = uuid.uuid4()
            user.save()
            
            return Response({
                'message': 'Email vérifié avec succès. Vous pouvez maintenant vous connecter.'
            }, status=status.HTTP_200_OK)
        except CustomUser.DoesNotExist:
            return Response({
                'error': 'Token de vérification invalide.'
            }, status=status.HTTP_400_BAD_REQUEST)


class DeviceListView(generics.ListAPIView):
    """Vue pour lister les appareils de l'utilisateur"""
    serializer_class = UserDeviceSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        return UserDevice.objects.filter(user=self.request.user, is_active=True)


class DeviceRegistrationView(generics.CreateAPIView):
    """Vue pour enregistrer un nouvel appareil"""
    serializer_class = DeviceRegistrationSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class DeviceDeactivateView(APIView):
    """Vue pour désactiver un appareil"""
    permission_classes = [permissions.IsAuthenticated]
    
    def post(self, request, device_id):
        try:
            device = UserDevice.objects.get(
                device_id=device_id,
                user=request.user
            )
            device.is_active = False
            device.save()
            
            return Response({
                'message': 'Appareil désactivé avec succès.'
            }, status=status.HTTP_200_OK)
        except UserDevice.DoesNotExist:
            return Response({
                'error': 'Appareil non trouvé.'
            }, status=status.HTTP_404_NOT_FOUND)


class DeviceTrustView(APIView):
    """Vue pour marquer un appareil comme de confiance"""
    permission_classes = [permissions.IsAuthenticated]
    
    def post(self, request, device_id):
        try:
            device = UserDevice.objects.get(
                device_id=device_id,
                user=request.user
            )
            device.is_trusted = not device.is_trusted
            device.save()
            
            status_text = "de confiance" if device.is_trusted else "non de confiance"
            return Response({
                'message': f'Appareil marqué comme {status_text}.'
            }, status=status.HTTP_200_OK)
        except UserDevice.DoesNotExist:
            return Response({
                'error': 'Appareil non trouvé.'
            }, status=status.HTTP_404_NOT_FOUND)


class ChangePasswordView(APIView):
    """Vue pour changer le mot de passe"""
    permission_classes = [permissions.IsAuthenticated]
    
    def post(self, request):
        serializer = ChangePasswordSerializer(data=request.data, context={'request': request})
        if serializer.is_valid():
            user = request.user
            user.set_password(serializer.validated_data['new_password'])
            user.save()
            
            # Invalider tous les tokens existants
            RefreshToken.for_user(user)
            
            return Response({
                'message': 'Mot de passe changé avec succès. Veuillez vous reconnecter.'
            }, status=status.HTTP_200_OK)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class PasswordResetRequestView(APIView):
    """Vue pour demander une réinitialisation de mot de passe"""
    permission_classes = [permissions.AllowAny]
    
    def post(self, request):
        serializer = PasswordResetRequestSerializer(data=request.data)
        if serializer.is_valid():
            email = serializer.validated_data['email']
            try:
                user = CustomUser.objects.get(email=email)
                
                # Envoyer l'email de réinitialisation
                self.send_reset_email(user)
                
                return Response({
                    'message': 'Un email de réinitialisation a été envoyé.'
                }, status=status.HTTP_200_OK)
            except CustomUser.DoesNotExist:
                # Ne pas révéler si l'email existe ou non
                return Response({
                    'message': 'Un email de réinitialisation a été envoyé.'
                }, status=status.HTTP_200_OK)
        
from django.contrib.auth import login, logout
from django.contrib.auth.tokens import default_token_generator
from django.conf import settings
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes, force_str
from django.shortcuts import get_object_or_404, render, redirect
from django.contrib import messages
from django.contrib.auth.forms import SetPasswordForm
from django.contrib.auth.views import PasswordResetView as DjangoPasswordResetView
from django.contrib.auth.views import PasswordResetDoneView as DjangoPasswordResetDoneView
from django.contrib.auth.views import PasswordResetConfirmView as DjangoPasswordResetConfirmView
from django.contrib.auth.views import PasswordResetCompleteView as DjangoPasswordResetCompleteView
from django.urls import reverse_lazy
from rest_framework import status, permissions, generics
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.authtoken.models import Token
from rest_framework.pagination import PageNumberPagination
from rest_framework.filters import SearchFilter, OrderingFilter
from django_filters.rest_framework import DjangoFilterBackend
from django.contrib.auth import authenticate
from tasks.sendMail import send_email_task
from Optibudget.settings import DEFAULT_FROM_EMAIL
from django.contrib.auth.models import User
from django.utils.crypto import get_random_string
from django.core.mail import send_mail
from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework_simplejwt.tokens import RefreshToken
from django.utils import timezone
from datetime import timedelta
import uuid
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from Optibudget.swagger_config import JWT_SECURITY
from .utils import send_password_reset_request_email, send_password_reset_success_email, send_password_changed_email
from django import forms

from .models import CustomUser, UserPreferences, UserDevice, LoginAttempt
from .serializers import (
    CustomUserSerializer, UserRegistrationSerializer,
    UserProfileSerializer, UserPreferencesSerializer,
    UserListSerializer, UserPreferencesUpdateSerializer,
    UserChoicesSerializer, CustomTokenObtainPairSerializer, DeviceRegistrationSerializer,
    ChangePasswordSerializer, EmailVerificationSerializer, PasswordResetRequestSerializer, PasswordResetConfirmSerializer, LoginAttemptSerializer, UserDeviceSerializer
)


class StandardResultsSetPagination(PageNumberPagination):
    """Pagination personnalisée"""
    page_size = 20
    page_size_query_param = 'page_size'
    max_page_size = 100


class CustomTokenObtainPairView(TokenObtainPairView):
    """Vue personnalisée pour l'obtention de tokens JWT"""
    serializer_class = CustomTokenObtainPairSerializer


class UserRegistrationView(generics.CreateAPIView):
    """Vue pour l'inscription d'un nouvel utilisateur"""
    queryset = CustomUser.objects.all()
    serializer_class = UserRegistrationSerializer
    permission_classes = [permissions.AllowAny]
    
    @swagger_auto_schema(
        operation_description="Inscription d'un nouvel utilisateur",
        operation_summary="Créer un nouveau compte utilisateur",
        request_body=UserRegistrationSerializer,
        responses={
            201: openapi.Response(
                description="Utilisateur créé avec succès",
                schema=UserRegistrationSerializer
            ),
            400: openapi.Response(
                description="Données invalides",
                examples={
                    "application/json": {
                        "username": ["Ce nom d'utilisateur existe déjà."],
                        "email": ["Cette adresse email existe déjà."],
                        "password": ["Ce mot de passe est trop court."]
                    }
                }
            )
        },
        tags=["Authentification"],
        security=[]  # Pas d'authentification requise pour l'inscription
    )
    def post(self, request, *args, **kwargs):
        return super().post(request, *args, **kwargs)
    
    def perform_create(self, serializer):
        user = serializer.save()
        
        # Envoyer l'email de vérification
        self.send_verification_email(user)
        
        return user
    
    def send_verification_email(self, user):
        """Envoie un email de vérification"""
        subject = 'Vérifiez votre adresse email - Optibudget'
        html_message = render_to_string('emails/email_verification.html', {
            'user': user,
            'verification_url': f"{self.request.scheme}://{self.request.get_host()}/api/accounts/verify-email/{user.email_verification_token}/"
        })
        plain_message = strip_tags(html_message)
        
        send_mail(
            subject,
            plain_message,
            DEFAULT_FROM_EMAIL,
            [user.email],
            html_message=html_message,
            fail_silently=False,
        )


class UserLoginView(APIView):
    """
    Vue pour la connexion des utilisateurs
    """
    permission_classes = [permissions.AllowAny]
    
    def post(self, request):
        email = request.data.get('email')
        password = request.data.get('password')
        
        if not email or not password:
            return Response({
                'error': 'Email et mot de passe requis'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Authentification
        user = authenticate(email=email, password=password)
        
        if user:
            # Connexion de l'utilisateur
            login(request, user)
            
            # Récupération ou création du token
            token, created = Token.objects.get_or_create(user=user)
            
            response_data = {
                'message': 'Connexion réussie',
                'user': UserProfileSerializer(user).data,
                'token': token.key
            }
            
            return Response(response_data, status=status.HTTP_200_OK)
        else:
            return Response({
                'error': 'Email ou mot de passe incorrect'
            }, status=status.HTTP_400_BAD_REQUEST)


class UserLogoutView(APIView):
    """
    Vue pour la déconnexion des utilisateurs
    """
    permission_classes = [permissions.IsAuthenticated]
    
    def post(self, request):
        try:
            # Suppression du token
            request.user.auth_token.delete()
        except:
            pass
        
        # Déconnexion
        logout(request)
        
        return Response(
            {'message': 'Déconnexion réussie'}, 
            status=status.HTTP_200_OK
        )


class UserProfileView(generics.RetrieveUpdateAPIView):
    """Vue pour le profil utilisateur"""
    serializer_class = UserProfileSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    @swagger_auto_schema(
        operation_description="Récupérer le profil de l'utilisateur connecté",
        operation_summary="Obtenir le profil utilisateur",
        responses={
            200: openapi.Response(
                description="Profil utilisateur récupéré avec succès",
                schema=UserProfileSerializer
            ),
            401: "Non authentifié"
        },
        tags=["Profil Utilisateur"],
        security=JWT_SECURITY  # Authentification JWT requise
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)
    
    @swagger_auto_schema(
        operation_description="Mettre à jour le profil de l'utilisateur connecté",
        operation_summary="Modifier le profil utilisateur",
        request_body=UserProfileSerializer,
        responses={
            200: openapi.Response(
                description="Profil utilisateur mis à jour avec succès",
                schema=UserProfileSerializer
            ),
            400: "Données invalides",
            401: "Non authentifié"
        },
        tags=["Profil Utilisateur"],
        security=JWT_SECURITY  # Authentification JWT requise
    )
    def put(self, request, *args, **kwargs):
        return super().put(request, *args, **kwargs)
    
    @swagger_auto_schema(
        operation_description="Mettre à jour partiellement le profil de l'utilisateur connecté",
        operation_summary="Modifier partiellement le profil utilisateur",
        request_body=UserProfileSerializer,
        responses={
            200: openapi.Response(
                description="Profil utilisateur mis à jour avec succès",
                schema=UserProfileSerializer
            ),
            400: "Données invalides",
            401: "Non authentifié"
        },
        tags=["Profil Utilisateur"],
        security=JWT_SECURITY  # Authentification JWT requise
    )
    def patch(self, request, *args, **kwargs):
        return super().patch(request, *args, **kwargs)
    
    def get_object(self):
        return self.request.user


class PasswordChangeView(APIView):
    """
    Vue pour changer le mot de passe
    """
    permission_classes = [permissions.IsAuthenticated]
    
    def post(self, request):
        serializer = PasswordChangeSerializer(
            data=request.data,
            context={'request': request}
        )
        if serializer.is_valid():
            serializer.save()
            return Response({
                'message': 'Mot de passe changé avec succès'
            })
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class PasswordVerificationView(APIView):
    """
    Vue pour vérifier si le mot de passe saisi par l'utilisateur est correct
    """
    permission_classes = [permissions.IsAuthenticated]
    
    def post(self, request):
        """
        Vérifier le mot de passe de l'utilisateur connecté
        """
        password = request.data.get('password')
        
        if not password:
            return Response(
                {'error': 'Le mot de passe est requis'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Vérification du mot de passe avec authenticate
        user = authenticate(
            username=request.user.username, 
            password=password
        )
        
        if user is not None:
            return Response({
                'valid': True,
                'message': 'Mot de passe correct'
            })
        else:
            return Response({
                'valid': False,
                'message': 'Mot de passe incorrect'
            }, status=status.HTTP_400_BAD_REQUEST)
        

class UserPreferencesView(generics.RetrieveUpdateAPIView):
    """Vue pour les préférences utilisateur"""
    serializer_class = UserPreferencesSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_object(self):
        user = self.request.user
        preferences, created = UserPreferences.objects.get_or_create(user=user)
        return preferences


class UserListView(generics.ListAPIView):
    """
    Vue pour lister les utilisateurs (admin seulement)
    """
    queryset = CustomUser.objects.all()
    serializer_class = UserListSerializer
    permission_classes = [permissions.IsAdminUser]
    pagination_class = StandardResultsSetPagination
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    
    # Filtres
    filterset_fields = ['compte', 'pays', 'statut_compte', 'is_active']
    search_fields = ['username', 'email', 'first_name', 'last_name']
    ordering_fields = ['date_joined', 'username', 'email']
    ordering = ['-date_joined']


class UserDetailView(generics.RetrieveUpdateDestroyAPIView):
    """
    Vue pour récupérer, mettre à jour ou supprimer un utilisateur spécifique (admin)
    """
    queryset = CustomUser.objects.all()
    permission_classes = [permissions.IsAdminUser]
    
    def get_serializer_class(self):
        # Éviter les erreurs lors de la génération du schéma Swagger
        if getattr(self, 'swagger_fake_view', False):
            return UserProfileSerializer
            
        if self.request.method == 'GET':
            return UserProfileSerializer
        return UserProfileSerializer  # Utiliser UserProfileSerializer au lieu de UserUpdateSerializer
    
    def destroy(self, request, *args, **kwargs):
        """Désactiver l'utilisateur au lieu de le supprimer"""
        user = self.get_object()
        user.is_active = False
        user.save()
        return Response({
            'message': 'Utilisateur désactivé avec succès'
        })


class UserActivationView(APIView):
    """
    Vue pour activer/désactiver un utilisateur (admin)
    """
    permission_classes = [permissions.IsAdminUser]
    
    def post(self, request, pk):
        user = get_object_or_404(CustomUser, pk=pk)
        action = request.data.get('action')  # 'activate' ou 'deactivate'
        
        if action == 'activate':
            user.is_active = True
            user.statut_compte = True
            message = 'Utilisateur activé avec succès'
        elif action == 'deactivate':
            user.is_active = False
            user.statut_compte = False
            message = 'Utilisateur désactivé avec succès'
        else:
            return Response(
                {'error': 'Action non valide'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        user.save()
        return Response({
            'message': message,
            'user': UserListSerializer(user).data
        })


class UserStatsView(APIView):
    """
    Vue pour les statistiques des utilisateurs (admin)
    """
    permission_classes = [permissions.IsAdminUser]
    
    def get(self, request):
        stats = {
            'total_users': CustomUser.objects.count(),
            'active_users': CustomUser.objects.filter(is_active=True).count(),
            'inactive_users': CustomUser.objects.filter(is_active=False).count(),
            'enterprise_accounts': CustomUser.objects.filter(compte='entreprise').count(),
            'individual_accounts': CustomUser.objects.filter(compte='particulier').count(),
            'users_by_country': dict(
                CustomUser.objects.values_list('pays')
                .annotate(count=models.Count('pays'))
                .order_by('-count')
            )
        }
        return Response(stats)


class UserChoicesView(APIView):
    """
    Vue pour récupérer les choix disponibles pour les formulaires
    """
    permission_classes = [permissions.AllowAny]
    
    def get(self, request):
        serializer = UserChoicesSerializer()
        return Response(serializer.to_representation(None))


# Vues basées sur les fonctions pour des cas spécifiques

@api_view(['POST'])
@permission_classes([permissions.AllowAny])
def check_username_availability(request):
    """
    Vérifier la disponibilité d'un nom d'utilisateur
    """
    username = request.data.get('username')
    if not username:
        return Response(
            {'error': 'Le nom d\'utilisateur est requis'}, 
            status=status.HTTP_400_BAD_REQUEST
        )
    
    is_available = not CustomUser.objects.filter(username=username).exists()
    return Response({
        'username': username,
        'available': is_available
    })


@api_view(['POST'])
@permission_classes([permissions.AllowAny])
def check_email_availability(request):
    """
    Vérifier la disponibilité d'un email
    """
    email = request.data.get('email')
    if not email:
        return Response(
            {'error': 'L\'email est requis'}, 
            status=status.HTTP_400_BAD_REQUEST
        )
    
    is_available = not CustomUser.objects.filter(email=email).exists()
    return Response({
        'email': email,
        'available': is_available
    })


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def upload_profile_image(request):
    """
    Upload d'image de profil
    """
    if 'image' not in request.FILES:
        return Response(
            {'error': 'Aucune image fournie'}, 
            status=status.HTTP_400_BAD_REQUEST
        )
    
    user = request.user
    user.img_profil = request.FILES['image']
    user.save()
    
    return Response({
        'message': 'Image de profil mise à jour avec succès',
        'image_url': user.img_profil.url if user.img_profil else None
    })


@api_view(['DELETE'])
@permission_classes([permissions.IsAuthenticated])
def delete_profile_image(request):
    """
    Supprimer l'image de profil
    """
    user = request.user
    if user.img_profil:
        user.img_profil.delete()
        user.img_profil = None
        user.save()
    
    return Response({
        'message': 'Image de profil supprimée avec succès'
    })


@api_view(['POST'])
@permission_classes([permissions.AllowAny])
def password_reset_request(request):
    """
    Demande de réinitialisation de mot de passe
    """
    email = request.data.get('email')
    if not email:
        return Response(
            {'error': 'L\'email est requis'}, 
            status=status.HTTP_400_BAD_REQUEST
        )
    
    try:
        user = CustomUser.objects.get(email=email)
        
        # Génération du token de réinitialisation
        token = default_token_generator.make_token(user)
        uid = urlsafe_base64_encode(force_bytes(user.pk))
        
        # Envoi de l'email avec notre fonction personnalisée
        reset_url = f"{self.request.scheme}://{self.request.get_host()}/accounts/reset-password/{uid}/{token}/"
        send_password_reset_request_email(user, reset_url)
        
        return Response({
            'message': 'Un email de réinitialisation a été envoyé'
        })
    
    except CustomUser.DoesNotExist:
        # Pour des raisons de sécurité, on ne révèle pas si l'email existe
        return Response({
            'message': 'Si cet email existe, un lien de réinitialisation a été envoyé'
        })


@api_view(['POST'])
@permission_classes([permissions.AllowAny])
def password_reset_confirm(request, uidb64, token):
    """
    Confirmation de réinitialisation de mot de passe
    """
    try:
        uid = force_str(urlsafe_base64_decode(uidb64))
        user = CustomUser.objects.get(pk=uid)
    except (TypeError, ValueError, OverflowError, CustomUser.DoesNotExist):
        user = None
    
    if user and default_token_generator.check_token(user, token):
        new_password = request.data.get('new_password')
        if not new_password:
            return Response(
                {'error': 'Le nouveau mot de passe est requis'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Validation du mot de passe
        try:
            from django.contrib.auth.password_validation import validate_password
            validate_password(new_password)
        except Exception as e:
            return Response(
                {'error': str(e)}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        user.set_password(new_password)
        user.save()
        
        # Envoyer l'email de confirmation avec template HTML
        send_password_reset_success_email(user)
        
        return Response({
            'message': 'Mot de passe réinitialisé avec succès'
        })
    
    return Response(
        {'error': 'Lien de réinitialisation invalide'}, 
        status=status.HTTP_400_BAD_REQUEST
    )


class EmailVerificationView(APIView):
    """Vue pour la vérification d'email"""
    permission_classes = [permissions.AllowAny]
    
    def get(self, request, token):
        try:
            user = CustomUser.objects.get(email_verification_token=token)
            user.is_email_verified = True
            user.email_verification_token = uuid.uuid4()
            user.save()
            
            return Response({
                'message': 'Email vérifié avec succès. Vous pouvez maintenant vous connecter.'
            }, status=status.HTTP_200_OK)
        except CustomUser.DoesNotExist:
            return Response({
                'error': 'Token de vérification invalide.'
            }, status=status.HTTP_400_BAD_REQUEST)


class DeviceListView(generics.ListAPIView):
    """Vue pour lister les appareils de l'utilisateur"""
    serializer_class = UserDeviceSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        return UserDevice.objects.filter(user=self.request.user, is_active=True)


class DeviceRegistrationView(generics.CreateAPIView):
    """Vue pour enregistrer un nouvel appareil"""
    serializer_class = DeviceRegistrationSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class DeviceDeactivateView(APIView):
    """Vue pour désactiver un appareil"""
    permission_classes = [permissions.IsAuthenticated]
    
    def post(self, request, device_id):
        try:
            device = UserDevice.objects.get(
                device_id=device_id,
                user=request.user
            )
            device.is_active = False
            device.save()
            
            return Response({
                'message': 'Appareil désactivé avec succès.'
            }, status=status.HTTP_200_OK)
        except UserDevice.DoesNotExist:
            return Response({
                'error': 'Appareil non trouvé.'
            }, status=status.HTTP_404_NOT_FOUND)


class DeviceTrustView(APIView):
    """Vue pour marquer un appareil comme de confiance"""
    permission_classes = [permissions.IsAuthenticated]
    
    def post(self, request, device_id):
        try:
            device = UserDevice.objects.get(
                device_id=device_id,
                user=request.user
            )
            device.is_trusted = not device.is_trusted
            device.save()
            
            status_text = "de confiance" if device.is_trusted else "non de confiance"
            return Response({
                'message': f'Appareil marqué comme {status_text}.'
            }, status=status.HTTP_200_OK)
        except UserDevice.DoesNotExist:
            return Response({
                'error': 'Appareil non trouvé.'
            }, status=status.HTTP_404_NOT_FOUND)


class ChangePasswordView(APIView):
    """Vue pour changer le mot de passe"""
    permission_classes = [permissions.IsAuthenticated]
    
    def post(self, request):
        serializer = ChangePasswordSerializer(data=request.data, context={'request': request})
        if serializer.is_valid():
            user = request.user
            user.set_password(serializer.validated_data['new_password'])
            user.save()
            
            # Invalider tous les tokens existants
            RefreshToken.for_user(user)
            
            return Response({
                'message': 'Mot de passe changé avec succès. Veuillez vous reconnecter.'
            }, status=status.HTTP_200_OK)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class PasswordResetRequestView(APIView):
    """Vue pour demander une réinitialisation de mot de passe"""
    permission_classes = [permissions.AllowAny]
    
    def post(self, request):
        serializer = PasswordResetRequestSerializer(data=request.data)
        if serializer.is_valid():
            email = serializer.validated_data['email']
            try:
                user = CustomUser.objects.get(email=email)
                
                # Générer un token de réinitialisation
                reset_token = get_random_string(64)
                user.email_verification_token = uuid.uuid4()
                user.save()
                
                # Envoyer l'email de réinitialisation
                reset_url = f"{self.request.scheme}://{self.request.get_host()}/accounts/reset-password/{user.email_verification_token}/{reset_token}/"
                send_password_reset_request_email(user, reset_url)
                
                return Response({
                    'message': 'Un email de réinitialisation a été envoyé.'
                }, status=status.HTTP_200_OK)
            except CustomUser.DoesNotExist:
                # Ne pas révéler si l'email existe ou non
                return Response({
                    'message': 'Un email de réinitialisation a été envoyé.'
                }, status=status.HTTP_200_OK)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    def send_reset_email(self, user):
        """Envoie un email de réinitialisation de mot de passe"""
        # Générer un token de réinitialisation
        token = default_token_generator.make_token(user)
        uid = urlsafe_base64_encode(force_bytes(user.pk))
        
        subject = 'Réinitialisation de mot de passe - Optibudget'
        reset_url = f"{self.request.scheme}://{self.request.get_host()}/accounts/reset-password/{uid}/{token}/"
        html_message = render_to_string('emails/password_reset.html', {
            'user': user,
            'reset_url': reset_url
        })
        plain_message = strip_tags(html_message)
        
        send_mail(
            subject,
            plain_message,
            DEFAULT_FROM_EMAIL,
            [user.email],
            html_message=html_message,
            fail_silently=False,
        )


class PasswordResetConfirmView(APIView):
    """Vue pour confirmer la réinitialisation de mot de passe"""
    permission_classes = [permissions.AllowAny]
    
    def post(self, request, token):
        serializer = PasswordResetConfirmSerializer(data=request.data)
        if serializer.is_valid():
            try:
                user = CustomUser.objects.get(email_verification_token=token)
                user.set_password(serializer.validated_data['new_password'])
                user.email_verification_token = uuid.uuid4()
                user.save()
                
                return Response({
                    'message': 'Mot de passe réinitialisé avec succès.'
                }, status=status.HTTP_200_OK)
            except CustomUser.DoesNotExist:
                return Response({
                    'error': 'Token de réinitialisation invalide.'
                }, status=status.HTTP_400_BAD_REQUEST)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class LoginAttemptsView(generics.ListAPIView):
    """Vue pour lister les tentatives de connexion"""
    serializer_class = LoginAttemptSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        return LoginAttempt.objects.filter(user=self.request.user)[:50]


class LogoutView(APIView):
    """Vue pour la déconnexion"""
    permission_classes = [permissions.IsAuthenticated]
    
    def post(self, request):
        try:
            refresh_token = request.data.get('refresh_token')
            if refresh_token:
                token = RefreshToken(refresh_token)
                token.blacklist()
            
            return Response({
                'message': 'Déconnexion réussie.'
            }, status=status.HTTP_200_OK)
        except Exception:
            return Response({
                'message': 'Une erreur est survenue lors de la déconnexion.'
            }, status=status.HTTP_200_OK)


class LogoutAllDevicesView(APIView):
    """Vue pour déconnecter tous les appareils"""
    permission_classes = [permissions.IsAuthenticated]
    
    def post(self, request):
        user = request.user
        
        # Désactiver tous les appareils
        UserDevice.objects.filter(user=user).update(is_active=False)
        
        # Blacklister tous les tokens de rafraîchissement
        for device in user.devices.all():
            # Note: Cette implémentation nécessiterait de stocker les refresh tokens
            # avec les appareils pour une implémentation complète
            pass
        
        return Response({
            'message': 'Tous les appareils ont été déconnectés.'
        }, status=status.HTTP_200_OK)


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def user_stats(request):
    """Vue pour les statistiques utilisateur"""
    user = request.user
    
    stats = {
        'total_devices': user.devices.filter(is_active=True).count(),
        'trusted_devices': user.devices.filter(is_active=True, is_trusted=True).count(),
        'failed_login_attempts': user.failed_login_attempts,
        'is_account_locked': user.is_account_locked(),
        'last_activity': user.last_activity,
        'is_email_verified': user.is_email_verified,
    }
    
    return Response(stats)


# ============================================================================
# VUES DJANGO CLASSIQUES POUR LA RÉINITIALISATION DE MOT DE PASSE
# ============================================================================

class PasswordResetRequestForm(forms.Form):
    """Formulaire personnalisé pour la demande de réinitialisation de mot de passe"""
    email = forms.EmailField(
        label='Adresse email',
        widget=forms.EmailInput(attrs={
            'class': 'pl-10 pr-4 py-2 border border-gray-300 rounded-lg w-full focus:outline-none focus:ring focus:ring-blue-200',
            'placeholder': 'votre@email.com'
        })
    )


class PasswordResetRequestTemplateView(DjangoPasswordResetView):
    """Vue pour demander une réinitialisation de mot de passe (template)"""
    template_name = 'accounts/password_reset_request.html'
    email_template_name = 'emails/password_reset.html'
    subject_template_name = 'emails/password_reset_subject.txt'
    success_url = reverse_lazy('accounts:password_reset_done')
    form_class = PasswordResetRequestForm
    
    def form_valid(self, form):
        """Override pour utiliser notre modèle CustomUser"""
        email = form.cleaned_data['email']
        try:
            user = CustomUser.objects.get(email=email)
            # Générer un token de réinitialisation
            token = default_token_generator.make_token(user)
            uid = urlsafe_base64_encode(force_bytes(user.pk))
            
            # Envoyer l'email avec notre fonction personnalisée
            reset_url = f"{self.request.scheme}://{self.request.get_host()}/accounts/reset-password/{uid}/{token}/"
            send_password_reset_request_email(user, reset_url)
            
            messages.success(self.request, 'Un email de réinitialisation a été envoyé à votre adresse email.')
        except CustomUser.DoesNotExist:
            # Pour des raisons de sécurité, on ne révèle pas si l'email existe
            messages.success(self.request, 'Si cet email existe, un lien de réinitialisation a été envoyé.')
        
        return super().form_valid(form)


class PasswordResetDoneTemplateView(DjangoPasswordResetDoneView):
    """Vue pour afficher la confirmation d'envoi d'email"""
    template_name = 'accounts/password_reset_done.html'


class PasswordResetConfirmTemplateView(DjangoPasswordResetConfirmView):
    """Vue pour confirmer la réinitialisation de mot de passe (template)"""
    template_name = 'accounts/password_reset_confirm.html'
    success_url = reverse_lazy('accounts:password_reset_complete')
    form_class = SetPasswordForm
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['validlink'] = self.validlink
        return context
    
    def form_valid(self, form):
        """Override pour utiliser notre modèle CustomUser et envoyer l'email de confirmation"""
        user = form.user
        form.save()
        
        # Envoyer l'email de confirmation
        send_password_reset_success_email(user)
        
        messages.success(self.request, 'Votre mot de passe a été réinitialisé avec succès.')
        return super().form_valid(form)


class PasswordResetCompleteTemplateView(DjangoPasswordResetCompleteView):
    """Vue pour afficher la confirmation de réinitialisation complète"""
    template_name = 'accounts/password_reset_complete.html'