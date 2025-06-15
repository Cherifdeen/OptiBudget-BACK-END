from rest_framework import serializers
from django.contrib.auth import authenticate
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from .models import CustomUser, UserPreferences

class UserPreferencesSerializer(serializers.ModelSerializer):
    """
    Serializer pour les préférences utilisateur
    """
    class Meta:
        model = UserPreferences
        fields = ['notifications_email', 'theme']


class CustomUserSerializer(serializers.ModelSerializer):
    """
    Serializer principal pour le modèle CustomUser
    """
    preferences = UserPreferencesSerializer(read_only=True)
    password = serializers.CharField(write_only=True, style={'input_type': 'password'})
    password_confirm = serializers.CharField(write_only=True, style={'input_type': 'password'})
    full_name = serializers.SerializerMethodField()
    
    class Meta:
        model = CustomUser
        fields = [
            'id', 'username', 'email', 'first_name', 'last_name', 'full_name',
            'phone', 'nom_entr', 'date_naiss', 'img_profil', 'compte', 
            'profession', 'pays', 'devise', 'langue', 'statut_compte',
            'password', 'password_confirm', 'preferences', 'date_joined', 'last_login'
        ]
        read_only_fields = ['id', 'date_joined', 'last_login']
        extra_kwargs = {
            'password': {'write_only': True},
            'email': {'required': True},
        }
    
    def get_full_name(self, obj):
        """Retourne le nom complet de l'utilisateur"""
        return obj.get_full_name()
    
    def validate_email(self, value):
        """Validation de l'email pour éviter les doublons"""
        if CustomUser.objects.filter(email=value).exists():
            raise serializers.ValidationError("Un utilisateur avec cet email existe déjà.")
        return value
    
    def validate_username(self, value):
        """Validation du nom d'utilisateur"""
        if CustomUser.objects.filter(username=value).exists():
            raise serializers.ValidationError("Ce nom d'utilisateur est déjà pris.")
        return value
    
    def validate(self, attrs):
        """Validation globale du serializer"""
        # Vérification des mots de passe
        if attrs.get('password') != attrs.get('password_confirm'):
            raise serializers.ValidationError("Les mots de passe ne correspondent pas.")
        
        # Validation du mot de passe Django
        password = attrs.get('password')
        if password:
            try:
                validate_password(password)
            except ValidationError as e:
                raise serializers.ValidationError({'password': list(e.messages)})
        
        # Validation pour les comptes entreprise
        if attrs.get('compte') == 'entreprise' and not attrs.get('nom_entr'):
            raise serializers.ValidationError({
                'nom_entr': "Le nom de l'entreprise est requis pour les comptes entreprise."
            })
        
        return attrs
    
    def create(self, validated_data):
        """Création d'un nouvel utilisateur"""
        validated_data.pop('password_confirm')
        password = validated_data.pop('password')
        
        user = CustomUser.objects.create_user(
            password=password,
            **validated_data
        )
        
        # Création automatique des préférences utilisateur
        UserPreferences.objects.create(user=user)
        
        return user
    
    def update(self, instance, validated_data):
        """Mise à jour d'un utilisateur existant"""
        password = validated_data.pop('password', None)
        validated_data.pop('password_confirm', None)
        
        # Mise à jour des champs
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        
        # Mise à jour du mot de passe si fourni
        if password:
            instance.set_password(password)
        
        instance.save()
        return instance


class UserRegistrationSerializer(serializers.ModelSerializer):
    """
    Serializer spécialisé pour l'inscription des utilisateurs
    """
    password = serializers.CharField(write_only=True, style={'input_type': 'password'})
    password_confirm = serializers.CharField(write_only=True, style={'input_type': 'password'})
    
    class Meta:
        model = CustomUser
        fields = [
            'username', 'email', 'first_name', 'last_name', 'phone',
            'compte', 'nom_entr', 'pays', 'devise', 'langue',
            'password', 'password_confirm'
        ]
        extra_kwargs = {
            'email': {'required': True},
            'first_name': {'required': True},
            'last_name': {'required': True},
        }
    
    def validate_email(self, value):
        if CustomUser.objects.filter(email=value).exists():
            raise serializers.ValidationError("Un utilisateur avec cet email existe déjà.")
        return value
    
    def validate_username(self, value):
        if CustomUser.objects.filter(username=value).exists():
            raise serializers.ValidationError("Ce nom d'utilisateur est déjà pris.")
        return value
    
    def validate(self, attrs):
        if attrs.get('password') != attrs.get('password_confirm'):
            raise serializers.ValidationError("Les mots de passe ne correspondent pas.")
        
        password = attrs.get('password')
        if password:
            try:
                validate_password(password)
            except ValidationError as e:
                raise serializers.ValidationError({'password': list(e.messages)})
        
        if attrs.get('compte') == 'entreprise' and not attrs.get('nom_entr'):
            raise serializers.ValidationError({
                'nom_entr': "Le nom de l'entreprise est requis pour les comptes entreprise."
            })
        
        return attrs
    
    def create(self, validated_data):
        validated_data.pop('password_confirm')
        password = validated_data.pop('password')
        
        user = CustomUser.objects.create_user(
            password=password,
            **validated_data
        )
        
        # Création des préférences par défaut
        UserPreferences.objects.create(user=user)
        
        return user


class UserLoginSerializer(serializers.Serializer):
    """
    Serializer pour l'authentification des utilisateurs
    """
    username = serializers.CharField()
    password = serializers.CharField(style={'input_type': 'password'})
    
    def validate(self, attrs):
        username = attrs.get('username')
        password = attrs.get('password')
        
        if username and password:
            # Permettre la connexion par email ou nom d'utilisateur
            if '@' in username:
                try:
                    user = CustomUser.objects.get(email=username)
                    username = user.username
                except CustomUser.DoesNotExist:
                    raise serializers.ValidationError("Email ou mot de passe incorrect.")
            
            user = authenticate(username=username, password=password)
            
            if user:
                if not user.is_active:
                    raise serializers.ValidationError("Ce compte est désactivé.")
                if not user.statut_compte:
                    raise serializers.ValidationError("Ce compte est suspendu.")
                attrs['user'] = user
                return attrs
            else:
                raise serializers.ValidationError("Nom d'utilisateur ou mot de passe incorrect.")
        else:
            raise serializers.ValidationError("Le nom d'utilisateur et le mot de passe sont requis.")


class UserProfileSerializer(serializers.ModelSerializer):
    """
    Serializer pour le profil utilisateur (lecture seule principalement)
    """
    preferences = UserPreferencesSerializer(read_only=True)
    full_name = serializers.SerializerMethodField()
    
    class Meta:
        model = CustomUser
        fields = [
            'id', 'username', 'email', 'first_name', 'last_name', 'full_name',
            'phone', 'nom_entr', 'date_naiss', 'img_profil', 'compte', 
            'profession', 'pays', 'devise', 'langue', 'preferences',
            'date_joined', 'last_login'
        ]
        read_only_fields = ['id', 'username', 'date_joined', 'last_login']
    
    def get_full_name(self, obj):
        return obj.get_full_name()


class UserUpdateSerializer(serializers.ModelSerializer):
    """
    Serializer pour la mise à jour du profil utilisateur
    """
    class Meta:
        model = CustomUser
        fields = [
            'first_name', 'last_name', 'email', 'phone', 'nom_entr', 
            'date_naiss', 'img_profil', 'profession', 'pays', 'devise', 'langue'
        ]
    
    def validate_email(self, value):
        # Permettre à l'utilisateur de garder son email actuel
        if self.instance and self.instance.email == value:
            return value
        
        if CustomUser.objects.filter(email=value).exists():
            raise serializers.ValidationError("Un utilisateur avec cet email existe déjà.")
        return value
    
    def validate(self, attrs):
        # Validation pour les comptes entreprise
        compte = getattr(self.instance, 'compte', None)
        if compte == 'entreprise':
            nom_entr = attrs.get('nom_entr') or getattr(self.instance, 'nom_entr', None)
            if not nom_entr:
                raise serializers.ValidationError({
                    'nom_entr': "Le nom de l'entreprise est requis pour les comptes entreprise."
                })
        
        return attrs


class PasswordChangeSerializer(serializers.Serializer):
    """
    Serializer pour le changement de mot de passe
    """
    old_password = serializers.CharField(style={'input_type': 'password'})
    new_password = serializers.CharField(style={'input_type': 'password'})
    confirm_password = serializers.CharField(style={'input_type': 'password'})
    
    def validate_old_password(self, value):
        user = self.context['request'].user
        if not user.check_password(value):
            raise serializers.ValidationError("L'ancien mot de passe est incorrect.")
        return value
    
    def validate_new_password(self, value):
        try:
            validate_password(value)
        except ValidationError as e:
            raise serializers.ValidationError(list(e.messages))
        return value
    
    def validate(self, attrs):
        if attrs.get('new_password') != attrs.get('confirm_password'):
            raise serializers.ValidationError("Les nouveaux mots de passe ne correspondent pas.")
        return attrs
    
    def save(self):
        user = self.context['request'].user
        user.set_password(self.validated_data['new_password'])
        user.save()
        return user


class UserListSerializer(serializers.ModelSerializer):
    """
    Serializer pour la liste des utilisateurs (admin)
    """
    full_name = serializers.SerializerMethodField()
    
    class Meta:
        model = CustomUser
        fields = [
            'id', 'username', 'email', 'full_name', 'compte', 
            'pays', 'statut_compte', 'is_active', 'date_joined'
        ]
    
    def get_full_name(self, obj):
        return obj.get_full_name()


class UserPreferencesUpdateSerializer(serializers.ModelSerializer):
    """
    Serializer pour mettre à jour les préférences utilisateur
    """
    class Meta:
        model = UserPreferences
        fields = ['notifications_email', 'theme']


# Serializer pour les choix des champs (utile pour les formulaires dynamiques)
class UserChoicesSerializer(serializers.Serializer):
    """
    Serializer pour récupérer les choix disponibles pour les champs
    """
    def to_representation(self, instance):
        return {
            'compte_choices': dict(CustomUser.TYPE_COMPTE),
            'pays_choices': dict(CustomUser.PAYS),
            'devise_choices': dict(CustomUser.DEVISES),
            'langue_choices': dict(CustomUser.LANGUES),
            'theme_choices': dict(UserPreferences.THEMES) if hasattr(UserPreferences, 'THEMES') else {}
        }