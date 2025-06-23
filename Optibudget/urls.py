from django.contrib import admin
from django.urls import path, include, re_path
from budgetManager.admin import admin_site 
from rest_framework import permissions
from drf_yasg.views import get_schema_view
from drf_yasg import openapi

# Configuration de la documentation Swagger
schema_view = get_schema_view(
    openapi.Info(
        title="OptiBudget API",
        default_version='v1',
        description="""
        # API OptiBudget - Gestion de Budget Intelligente
        
        ## Description
        API REST pour la gestion de budget avec conseils IA intégrés. 
        Cette API permet de gérer des budgets personnels et d'entreprise avec des fonctionnalités avancées.
        
        ## Fonctionnalités principales
        - **Gestion des budgets** : Création, modification et suivi des budgets
        - **Catégorisation des dépenses** : Organisation des dépenses par catégories
        - **Conseils IA** : Recommandations intelligentes basées sur les habitudes de dépenses
        - **Rapports et statistiques** : Analyses détaillées des finances
        - **Gestion des employés** : Fonctionnalités avancées pour les comptes entreprise
        
        ## Authentification
        
        ### JWT (JSON Web Tokens)
        L'API utilise l'authentification JWT. Incluez le token dans l'en-tête Authorization :
        ```
        Authorization: Bearer <votre_token_jwt>
        ```
        
        ### Clés Client (X-Client-Key)
        Pour les requêtes provenant d'applications externes, scripts ou API, une clé client est requise :
        ```
        X-Client-Key: <votre_clé_client>
        ```
        
        **Règles d'utilisation des clés client :**
        - **Navigateur web** : Pas de clé client requise (détection automatique)
        - **API externe/Scripts** : Clé client obligatoire
        - **Requêtes GET** : Généralement autorisées sans clé
        - **Endpoints publics** : Pas de clé requise (login, inscription, etc.)
        
        **Endpoints exemptés de clé client :**
        - `/api/accounts/login/`
        - `/api/accounts/signup/`
        - `/api/accounts/password-reset/`
        - `/admin/`
        - `/swagger/`
        - `/redoc/`
        
        **Endpoints nécessitant une clé client (pour API externe) :**
        - Tous les endpoints de gestion de budget
        - Endpoints de profil utilisateur
        - Endpoints de rapports et statistiques
        
        ## Codes de statut
        - `200` : Succès
        - `201` : Ressource créée
        - `400` : Données invalides
        - `401` : Non authentifié (JWT manquant ou clé client manquante)
        - `403` : Accès interdit (clé client invalide ou inactive)
        - `404` : Ressource non trouvée
        - `500` : Erreur serveur
        
        ## Pagination
        La plupart des endpoints de liste supportent la pagination avec les paramètres :
        - `page` : Numéro de page (défaut: 1)
        - `page_size` : Éléments par page (défaut: 20, max: 100)
        
        ## Filtrage et tri
        Les endpoints de liste supportent :
        - `search` : Recherche textuelle
        - `ordering` : Tri par champ (préfixer avec '-' pour tri décroissant)
        
        ## Exemples d'utilisation
        
        ### Requête avec JWT uniquement (navigateur)
        ```bash
        GET /api/budgetManager/budgets/
        Authorization: Bearer <token_jwt>
        ```
        
        ### Requête avec clé client (API externe)
        ```bash
        POST /api/budgetManager/budgets/
        Authorization: Bearer <token_jwt>
        X-Client-Key: <clé_client>
        Content-Type: application/json
        
        {
            "nom": "Budget Mensuel",
            "montant_initial": 1000.00
        }
        ```
        
        ### Requête publique (pas d'authentification)
        ```bash
        POST /api/accounts/login/
        Content-Type: application/json
        
        {
            "username": "utilisateur",
            "password": "motdepasse"
        }
        ```
        """,
        terms_of_service="https://www.optibudget.com/terms/",
        contact=openapi.Contact(
            email="contact@optibudget.com",
            name="Support OptiBudget",
            url="https://www.optibudget.com/support"
        ),
        license=openapi.License(
            name="MIT License",
            url="https://opensource.org/licenses/MIT"
        ),
    ),
    public=True,
    permission_classes=(permissions.AllowAny,),
)

urlpatterns = [
    
    path('admin/', admin.site.urls),
    # path('admin/', admin_site.urls),
    path('api-auth/', include('rest_framework.urls')),
    path('OptiAdmin/', include('optibudget_admin.urls')),
    
    # Documentation API
    re_path(r'^swagger(?P<format>\.json|\.yaml)$', schema_view.without_ui(cache_timeout=0), name='schema-json'),
    re_path(r'^swagger/$', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),
    re_path(r'^redoc/$', schema_view.with_ui('redoc', cache_timeout=0), name='schema-redoc'),
    
    # URLs des templates de réinitialisation de mot de passe (sans namespace)
    path('', include('accounts.urls')),
    
    path('api/', include([
        path('accounts/', include('accounts.urls', namespace='api_accounts')),
        path('budgetManager/', include('budgetManager.urls')),
    ])),
]



