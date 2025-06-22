from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404
from django.db.models import Q, Sum
from django.utils import timezone
from datetime import datetime, timedelta
from django.db import transaction
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.db.models import Sum, Count, Q
from django.utils import timezone
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
from .models import Budget, CategorieDepense, Depense, Entree, PaiementEmploye
from .serializers import BudgetSerializer, CategorieDepenseSerializer, DepenseSerializer, EntreeSerializer
from django.db import transaction
from decimal import Decimal
import logging
from .models import (
    Budget, CategorieDepense, Depense, Entree, Employe, 
    Notification, Conseil, PaiementEmploye, MontantSalaire
)
from .serializers import (
    BudgetSerializer, CategorieDepenseSerializer, DepenseSerializer,
    EntreeSerializer, NotificationSerializer, ConseilSerializer,
    EmployeSerializer, PaiementEmployeSerializer, MontantSalaireSerializer
)
from .customPagination import CustomCursorPagination



class BudgetViewSet(viewsets.ModelViewSet):
    """ViewSet pour la gestion des budgets avec les pagination """
    serializer_class = BudgetSerializer
    permission_classes = [IsAuthenticated]
    pagination_class = CustomCursorPagination
    
    def get_queryset(self):
        """Retourner seulement les budgets de l'utilisateur connecté"""
        return Budget.objects.filter(user=self.request.user).order_by('-created_at')
    
    @action(detail=True, methods=['get'])
    def categories(self, request, pk=None):
        """Récupérer toutes les catégories d'un budget"""
        budget = self.get_object()
        categories = CategorieDepense.objects.filter(id_budget=budget, user=request.user)
        serializer = CategorieDepenseSerializer(categories, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['get'])
    def depenses(self, request, pk=None):
        """Récupérer toutes les dépenses d'un budget"""
        budget = self.get_object()
        depenses = Depense.objects.filter(id_budget=budget, user=request.user)
        serializer = DepenseSerializer(depenses, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['get'])
    def resume(self, request, pk=None):
        """Résumé du budget avec statistiques"""
        budget = self.get_object()
        
        # Calculs des statistiques
        total_depenses = Depense.objects.filter(
            id_budget=budget, user=request.user
        ).aggregate(total=Sum('montant'))['total'] or 0
        
        total_categories = CategorieDepense.objects.filter(
            id_budget=budget, user=request.user
        ).count()
        
        montant_utilise = budget.montant_initial - budget.montant
        pourcentage_utilise = (montant_utilise / budget.montant_initial * 100) if budget.montant_initial > 0 else 0
        
        data = {
            'budget': BudgetSerializer(budget).data,
            'statistiques': {
                'montant_initial': budget.montant_initial,
                'montant_restant': budget.montant,
                'montant_utilise': montant_utilise,
                'pourcentage_utilise': round(pourcentage_utilise, 2),
                'nombre_categories': total_categories,
                'total_depenses': total_depenses
            }
        }
        
        return Response(data)


class CategorieDepenseViewSet(viewsets.ModelViewSet):
    """ViewSet pour la gestion des catégories de dépenses"""
    serializer_class = CategorieDepenseSerializer
    permission_classes = [IsAuthenticated]
    pagination_class = CustomCursorPagination
    
    def get_queryset(self):
        """Retourner seulement les catégories de l'utilisateur connecté"""
        queryset = CategorieDepense.objects.filter(user=self.request.user).order_by('-created_at')
        # Filtrer par budget si spécifié
        budget_id = self.request.query_params.get('budget_id')
        if budget_id:
            queryset = queryset.filter(id_budget_id=budget_id)
        return queryset
    
    @transaction.atomic
    def destroy(self, request, *args, **kwargs):
        """
        Supprimer une catégorie et ajouter le montant initial au budget parent
        """
        categorie = self.get_object()
        
        # Récupérer le budget parent
        budget = categorie.id_budget
        
        # Récupérer le montant initial de la catégorie
        montant_initial = categorie.montant_initial
        
        # Ajouter le montant initial au budget parent
        budget.montant += montant_initial
        budget.save()
        
        # Supprimer la catégorie
        self.perform_destroy(categorie)
        
        return Response(status=status.HTTP_204_NO_CONTENT)
    
    @action(detail=True, methods=['get'])
    def depenses(self, request, pk=None):
        """Récupérer toutes les dépenses d'une catégorie"""
        categorie = self.get_object()
        depenses = Depense.objects.filter(id_cat_depense=categorie, user=request.user)
        serializer = DepenseSerializer(depenses, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['get'])
    def stats(self, request, pk=None):
        """Récupérer les statistiques d'une catégorie"""
        categorie = self.get_object()
        
        # Paramètres de période (optionnels)
        periode = request.query_params.get('periode', 'all')  # all, month, week, year
        
        # Base queryset des dépenses
        depenses_qs = Depense.objects.filter(
            id_cat_depense=categorie, 
            user=request.user
        )
        
        # Filtrer par période si spécifié
        now = timezone.now()
        if periode == 'week':
            start_date = now - timedelta(days=7)
            depenses_qs = depenses_qs.filter(date_depense__gte=start_date)
        elif periode == 'month':
            start_date = now - timedelta(days=30)
            depenses_qs = depenses_qs.filter(date_depense__gte=start_date)
        elif periode == 'year':
            start_date = now - timedelta(days=365)
            depenses_qs = depenses_qs.filter(date_depense__gte=start_date)
        
        # Calculs statistiques
        stats_data = depenses_qs.aggregate(
            total_depense=Sum('montant') or 0,
            nombre_depenses=Count('id'),
            depense_moyenne=Avg('montant') or 0,
        )
        
        # Montant restant dans la catégorie
        montant_restant = categorie.montant_initial - stats_data['total_depense']
        
        # Pourcentage utilisé
        pourcentage_utilise = 0
        if categorie.montant_initial > 0:
            pourcentage_utilise = (stats_data['total_depense'] / categorie.montant_initial) * 100
        
        # Dépenses par jour (pour les graphiques)
        depenses_par_jour = depenses_qs.extra(
            select={'jour': 'date(date_depense)'}
        ).values('jour').annotate(
            total_jour=Sum('montant'),
            nombre_depenses_jour=Count('id')
        ).order_by('jour')
        
        # Top 5 des plus grosses dépenses
        top_depenses = depenses_qs.order_by('-montant')[:5].values(
            'id', 'libelle', 'montant', 'date_depense'
        )
        
        response_data = {
            'categorie_info': {
                'id': categorie.id,
                'nom': categorie.nom,
                'montant_initial': float(categorie.montant_initial),
                'couleur': categorie.couleur,
            },
            'periode': periode,
            'resume': {
                'total_depense': float(stats_data['total_depense']),
                'montant_restant': float(montant_restant),
                'nombre_depenses': stats_data['nombre_depenses'],
                'depense_moyenne': float(stats_data['depense_moyenne']),
                'pourcentage_utilise': round(pourcentage_utilise, 2),
            },
            'depenses_par_jour': list(depenses_par_jour),
            'top_depenses': list(top_depenses),
            'statut': {
                'est_depassee': montant_restant < 0,
                'est_proche_limite': pourcentage_utilise > 80,
            }
        }
        
        return Response(response_data)
    
    @action(detail=False, methods=['get'])
    def stats_globales(self, request):
        """Statistiques globales pour toutes les catégories de l'utilisateur"""
        queryset = self.get_queryset()
        
        # Paramètres de période
        periode = request.query_params.get('periode', 'month')
        
        now = timezone.now()
        start_date = now
        if periode == 'week':
            start_date = now - timedelta(days=7)
        elif periode == 'month':
            start_date = now - timedelta(days=30)
        elif periode == 'year':
            start_date = now - timedelta(days=365)
        
        stats_par_categorie = []
        total_budget = 0
        total_depense = 0
        
        for categorie in queryset:
            # Dépenses de la catégorie pour la période
            depenses_qs = Depense.objects.filter(
                id_cat_depense=categorie,
                user=request.user,
                date_depense__gte=start_date
            )
            
            categorie_stats = depenses_qs.aggregate(
                total=Sum('montant') or 0,
                count=Count('id')
            )
            
            montant_restant = categorie.montant_initial - categorie_stats['total']
            pourcentage = 0
            if categorie.montant_initial > 0:
                pourcentage = (categorie_stats['total'] / categorie.montant_initial) * 100
            
            stats_par_categorie.append({
                'id': categorie.id,
                'nom': categorie.nom,
                'couleur': categorie.couleur,
                'montant_initial': float(categorie.montant_initial),
                'total_depense': float(categorie_stats['total']),
                'montant_restant': float(montant_restant),
                'nombre_depenses': categorie_stats['count'],
                'pourcentage_utilise': round(pourcentage, 2),
                'est_depassee': montant_restant < 0,
            })
            
            total_budget += categorie.montant_initial
            total_depense += categorie_stats['total']
        
        # Trier par pourcentage utilisé (décroissant)
        stats_par_categorie.sort(key=lambda x: x['pourcentage_utilise'], reverse=True)
        
        response_data = {
            'periode': periode,
            'resume_global': {
                'total_budget': float(total_budget),
                'total_depense': float(total_depense),
                'total_restant': float(total_budget - total_depense),
                'nombre_categories': len(stats_par_categorie),
                'pourcentage_global': round((total_depense / total_budget * 100), 2) if total_budget > 0 else 0,
            },
            'categories': stats_par_categorie,
            'alertes': {
                'categories_depassees': [c for c in stats_par_categorie if c['est_depassee']],
                'categories_proches_limite': [c for c in stats_par_categorie if c['pourcentage_utilise'] > 80 and not c['est_depassee']],
            }
        }
        
        return Response(response_data)  


class DepenseViewSet(viewsets.ModelViewSet):
    """ViewSet pour la gestion des dépenses"""
    serializer_class = DepenseSerializer
    permission_classes = [IsAuthenticated]
    pagination_class = CustomCursorPagination
    
    def get_queryset(self):
        """Retourner seulement les dépenses de l'utilisateur connecté"""
        queryset = Depense.objects.filter(user=self.request.user).order_by('-created_at')
        # Filtrer par catégorie si spécifié
        categorie_id = self.request.query_params.get('categorie_id')
        if categorie_id:
            queryset = queryset.filter(id_cat_depense_id=categorie_id)
        # Filtrer par budget si spécifié
        budget_id = self.request.query_params.get('budget_id')
        if budget_id:
            queryset = queryset.filter(id_budget_id=budget_id)
        return queryset
    
    @transaction.atomic
    def destroy(self, request, *args, **kwargs):
        """
        Supprimer une dépense et ajouter le montant à la catégorie de dépense
        """
        depense = self.get_object()
        
        # Récupérer le montant de la dépense
        montant_depense = depense.montant
        
        # Ajouter le montant à la catégorie de dépense si elle existe
        if depense.id_cat_depense:
            categorie = depense.id_cat_depense
            categorie.montant += montant_depense
            categorie.save()
        
        # Supprimer la dépense
        self.perform_destroy(depense)
        
        return Response(status=status.HTTP_204_NO_CONTENT)

class EntreeViewSet(viewsets.ModelViewSet):
    """ViewSet pour la gestion des entrées"""
    serializer_class = EntreeSerializer
    permission_classes = [IsAuthenticated]
    pagination_class = CustomCursorPagination
    
    def get_queryset(self):
        """Retourner seulement les entrées de l'utilisateur connecté"""
        return Entree.objects.filter(user=self.request.user).order_by('-created_at')
    
    @action(detail=False, methods=['get'])
    def statistiques(self, request):
        """Statistiques des entrées de l'utilisateur"""
        # Entrées du mois en cours
        debut_mois = timezone.now().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        entrees_mois = Entree.objects.filter(
            user=request.user,
            created_at__gte=debut_mois
        ).aggregate(total=Sum('montant'))['total'] or 0
        
        # Total des entrées
        total_entrees = Entree.objects.filter(
            user=request.user
        ).aggregate(total=Sum('montant'))['total'] or 0
        
        # Nombre d'entrées
        nombre_entrees = Entree.objects.filter(user=request.user).count()
        
        data = {
            'entrees_mois_courant': entrees_mois,
            'total_entrees': total_entrees,
            'nombre_entrees': nombre_entrees,
            'moyenne_entree': round(total_entrees / nombre_entrees, 2) if nombre_entrees > 0 else 0
        }
        
        return Response(data)


class NotificationViewSet(viewsets.ModelViewSet):
    """ViewSet pour la gestion des notifications"""
    serializer_class = NotificationSerializer
    permission_classes = [IsAuthenticated]
    pagination_class = CustomCursorPagination

    def get_queryset(self):
        """Retourner seulement les notifications de l'utilisateur connecté"""
        return Notification.objects.filter(user=self.request.user).filter(~Q(type_notification='LOG')).order_by('-created_at')
    
    @action(detail=False, methods=['get'])
    def non_lues(self, request):
        """Récupérer les notifications non lues"""
        notifications = Notification.objects.filter(
            user=request.user,
            viewed=False  # Changed from is_read=False to viewed=False
        ).order_by('-created_at')
        serializer = self.get_serializer(notifications, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def marquer_lue(self, request, pk=None):
        """Marquer une notification comme lue"""
        notification = self.get_object()
        notification.viewed = True  # Changed from is_read=True to viewed=True
        notification.save()
        return Response({'status': 'notification marquée comme lue'})
    
    @action(detail=False, methods=['post'])
    def marquer_toutes_lues(self, request):
        """Marquer toutes les notifications comme lues"""
        Notification.objects.filter(user=request.user, viewed=False).update(viewed=True)
        # Changed from is_read=False to viewed=False and is_read=True to viewed=True
        return Response({'status': 'toutes les notifications marquées comme lues'})

class ConseilViewSet(viewsets.ModelViewSet):
    """ViewSet pour la gestion des conseils"""
    serializer_class = ConseilSerializer
    permission_classes = [IsAuthenticated]
    pagination_class = CustomCursorPagination
    
    def get_queryset(self):
        """Retourner seulement les conseils de l'utilisateur connecté"""
        return Conseil.objects.filter(user=self.request.user).order_by('-created_at')
    
    @action(detail=False, methods=['get'])
    def recents(self, request):
        """Récupérer les conseils récents (7 derniers jours)"""
        date_limite = timezone.now() - timedelta(days=7)
        conseils = Conseil.objects.filter(
            user=request.user,
            created_at__gte=date_limite
        ).order_by('-created_at')
        serializer = self.get_serializer(conseils, many=True)
        return Response(serializer.data)


class EmployeViewSet(viewsets.ModelViewSet):
    """ViewSet pour la gestion des employés (comptes entreprise uniquement)"""
    serializer_class = EmployeSerializer
    permission_classes = [IsAuthenticated]
    pagination_class = CustomCursorPagination
    
    def get_queryset(self):
        """Retourner seulement les employés de l'utilisateur connecté"""
        return Employe.objects.filter(user=self.request.user).order_by('nom', 'prenom')
    
    @action(detail=True, methods=['get'])
    def paiements(self, request, pk=None):
        """Récupérer tous les paiements d'un employé"""
        employe = self.get_object()
        paiements = PaiementEmploye.objects.filter(id_employe=employe, user=request.user)
        serializer = PaiementEmployeSerializer(paiements, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'], url_path='par_statut/(?P<statut>[^/.]+)')
    def par_statut(self, request, statut=None):
        """Récupérer les employés par statut"""
        # Vérifier que le statut est valide
        statuts_valides = ['ES', 'EC', 'ER', 'LC', 'HS', 'DM']
        if statut not in statuts_valides:
            return Response(
                {'error': f'Statut invalide. Statuts valides: {statuts_valides}'}, 
                status=400
            )
        
        employes = Employe.objects.filter(user=request.user, actif=statut)
        serializer = self.get_serializer(employes, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def actifs(self, request):
        """Récupérer les employés actifs (En service uniquement)"""
        employes = Employe.objects.filter(user=request.user, actif='ES')
        serializer = self.get_serializer(employes, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def desactiver(self, request, pk=None):
        """Désactiver un employé"""
        employe = self.get_object()
        # Fix: Set actif to 'HS' (Hors service) instead of is_active=False
        employe.actif = 'HS'
        employe.save()
        return Response({'status': 'employé désactivé'})
    
    @action(detail=True, methods=['post'])
    def activer(self, request, pk=None):
        """Activer un employé"""
        employe = self.get_object()
        # Fix: Set actif to 'ES' (En service) instead of is_active=True
        employe.actif = 'ES'
        employe.save()
        return Response({'status': 'employé activé'})
    @action(detail=False, methods=['get'])
    def par_statut(self, request, statut=None):
        """Récupérer les employés par statut"""
        # Vérifier que le statut est valide
        statuts_valides = ['ES', 'EC', 'ER', 'LC', 'HS', 'DM']
        if statut not in statuts_valides:
            return Response(
                {'error': f'Statut invalide. Statuts valides: {statuts_valides}'}, 
                status=400
            )
        
        employes = Employe.objects.filter(user=request.user, actif=statut)
        serializer = self.get_serializer(employes, many=True)
        return Response(serializer.data)
    



logger = logging.getLogger(__name__)

class PaiementEmployeViewSet(viewsets.ModelViewSet):
    """ViewSet pour la gestion des paiements d'employés"""
    serializer_class = PaiementEmployeSerializer
    permission_classes = [IsAuthenticated]
    pagination_class = CustomCursorPagination
    
    def get_queryset(self):
        """Retourner seulement les paiements de l'utilisateur connecté"""
        queryset = PaiementEmploye.objects.filter(user=self.request.user).order_by('-date_paiement')
        
        # Filtre par employé si spécifié
        employe_id = self.request.query_params.get('employe_id')
        if employe_id:
            queryset = queryset.filter(id_employe_id=employe_id)
            
        # Filtre par budget si spécifié
        budget_id = self.request.query_params.get('budget_id')
        if budget_id:
            queryset = queryset.filter(id_budget_id=budget_id)
            
        return queryset

    @action(detail=False, methods=['post'])
    def paiement_global(self, request):
        """
        Effectuer le paiement global de tous les employés actifs
        
        Paramètres attendus:
        - budget_id: ID du budget sur lequel imputer les salaires
        - periode: optionnel, période de paiement (format: 'YYYY-MM')
        - type_employes: optionnel, liste des types d'employés à payer
        """
        try:
            # Récupération des paramètres
            budget_id = request.data.get('budget_id')
            periode = request.data.get('periode')  # Format: 'YYYY-MM'
            type_employes = request.data.get('type_employes', [])  # Liste des types à payer
            
            if not budget_id:
                return Response(
                    {'error': 'Le budget_id est requis'}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Vérification de l'existence du budget
            try:
                budget = Budget.objects.get(id=budget_id, user=request.user)
            except Budget.DoesNotExist:
                return Response(
                    {'error': 'Budget non trouvé'}, 
                    status=status.HTTP_404_NOT_FOUND
                )
            
            # Vérification que le budget est actif
            if not budget.actif:
                return Response(
                    {'error': 'Le budget n\'est pas actif'}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Récupération des employés actifs
            employes_query = Employe.objects.filter(
                user=request.user,
                actif='ES'  # En service
            )
            
            # Filtrer par types d'employés si spécifié
            if type_employes:
                employes_query = employes_query.filter(type_employe__in=type_employes)
            
            employes = employes_query.all()
            
            if not employes.exists():
                return Response(
                    {'error': 'Aucun employé actif trouvé'}, 
                    status=status.HTTP_404_NOT_FOUND
                )
            
            # Récupération des paramètres de salaire
            try:
                montant_salaire = MontantSalaire.objects.get(user=request.user)
            except MontantSalaire.DoesNotExist:
                return Response(
                    {'error': 'Configuration des salaires non trouvée'}, 
                    status=status.HTTP_404_NOT_FOUND
                )
            
            # Calcul des salaires et création des paiements
            paiements_crees = []
            depenses_creees = []
            total_paiements = Decimal('0.00')
            
            with transaction.atomic():
                for employe in employes:
                    # Calcul du salaire selon le type d'employé
                    salaire_base = self._calculer_salaire_employe(employe, montant_salaire)
                    
                    if salaire_base <= 0:
                        continue
                    
                    # Vérification des paiements existants pour cette période
                    if periode:
                        debut_periode = timezone.datetime.strptime(f"{periode}-01", "%Y-%m-%d")
                        fin_periode = debut_periode.replace(
                            month=debut_periode.month % 12 + 1 if debut_periode.month < 12 else 1,
                            year=debut_periode.year + (1 if debut_periode.month == 12 else 0)
                        )
                        
                        paiement_existant = PaiementEmploye.objects.filter(
                            id_employe=employe,
                            user=request.user,
                            date_paiement__gte=debut_periode,
                            date_paiement__lt=fin_periode
                        ).exists()
                        
                        if paiement_existant:
                            continue  # Employé déjà payé pour cette période
                    
                    # Création du paiement
                    paiement = PaiementEmploye.objects.create(
                        id_employe=employe,
                        montant=salaire_base,
                        type_paiement='SALAIRE',
                        description=f"Salaire {periode if periode else timezone.now().strftime('%Y-%m')} - {employe.nom} {employe.prenom}",
                        id_budget=budget,
                        user=request.user
                    )
                    paiements_crees.append(paiement)
                    
                    # Création de la dépense correspondante dans le budget
                    depense = Depense.objects.create(
                        nom=f"Salaire - {employe.nom} {employe.prenom}",
                        montant=salaire_base,
                        type_depense='SL',  # Salaires
                        description=f"Paiement salaire {periode if periode else timezone.now().strftime('%Y-%m')} - Ref: {paiement.id}",
                        id_budget=budget,  # Le budget où sera imputée la dépense
                        user=request.user
                    )
                    # Lier la dépense au paiement si nécessaire (optionnel)
                    # paiement.id_depense = depense  # Si vous ajoutez ce champ au modèle
                    depenses_creees.append(depense)
                    
                    total_paiements += Decimal(str(salaire_base))
                
                # Mise à jour du montant du budget
                budget.montant -= float(total_paiements)
                budget.save()
                
                # Vérification du solde du budget après déduction
                if budget.montant < 0:
                    logger.warning(f"ATTENTION: Budget {budget.nom} (ID: {budget.id}) en déficit de {abs(budget.montant)} FCFA après paiement des salaires")
                    
                    # Créer une notification d'alerte pour déficit
                    Notification.objects.create(
                        message=f"ALERTE: Budget '{budget.nom}' en déficit de {abs(budget.montant)} FCFA après paiement des salaires",
                        type_notification='WARNING',
                        user=request.user
                    )
                
                # Création d'une notification de succès avec détails du budget
                Notification.objects.create(
                    message=f"Paiement global effectué sur budget '{budget.nom}': {len(paiements_crees)} employés payés pour un total de {total_paiements} FCFA. Solde restant: {budget.montant} FCFA",
                    type_notification='SUCCESS',
                    user=request.user
                )
            
            # Préparation de la réponse avec informations détaillées du budget
            response_data = {
                'success': True,
                'message': f'Paiement global effectué avec succès sur le budget "{budget.nom}"',
                'details': {
                    'budget_id': str(budget.id),
                    'budget_nom': budget.nom,
                    'montant_initial_budget': budget.montant + float(total_paiements),  # Montant avant paiement
                    'montant_paiements': float(total_paiements),
                    'solde_budget_restant': budget.montant,
                    'nombre_employes_payes': len(paiements_crees),
                    'nombre_depenses_creees': len(depenses_creees),
                    'periode': periode if periode else timezone.now().strftime('%Y-%m'),
                    'date_paiement': timezone.now().isoformat(),
                    'budget_suffisant': budget.montant >= 0
                },
                'paiements': [
                    {
                        'paiement_id': str(p.id),
                        'employe_id': str(p.id_employe.id),
                        'employe_nom': f"{p.id_employe.nom} {p.id_employe.prenom}",
                        'type_employe': p.id_employe.get_type_employe_display(),
                        'montant': p.montant,
                        'budget_id': str(p.id_budget.id),
                        'budget_nom': p.id_budget.nom,
                        'date_paiement': p.date_paiement.isoformat()
                    } for p in paiements_crees
                ],
                'depenses': [
                    {
                        'depense_id': str(d.id),
                        'nom': d.nom,
                        'montant': d.montant,
                        'budget_id': str(d.id_budget.id),
                        'budget_nom': d.id_budget.nom,
                        'type_depense': d.get_type_depense_display()
                    } for d in depenses_creees
                ]
            }
            
            return Response(response_data, status=status.HTTP_201_CREATED)
            
        except Exception as e:
            logger.error(f"Erreur lors du paiement global: {str(e)}")
            return Response(
                {'error': f'Erreur lors du paiement: {str(e)}'}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    def _calculer_salaire_employe(self, employe, montant_salaire):
        """
        Calculer le salaire d'un employé selon son type
        """
        type_map = {
            'DIR': 'direction',
            'CAD': 'cadre', 
            'EMP': 'employe',
            'OUV': 'ouvrier',
            'CON': 'cf',  # Consultant/Freelance
            'STA': 'stagiaire',
            'INT': 'intermediaire',
            'AUT': 'autre'
        }
        
        type_salaire = type_map.get(employe.type_employe, 'autre')
        salaire_field = f'salaire_{type_salaire}'
        
        return getattr(montant_salaire, salaire_field, 0.0)
    
    @action(detail=False, methods=['get'])
    def preview_paiement_global(self, request):
        """
        Prévisualiser le paiement global sans l'exécuter
        """
        try:
            budget_id = request.query_params.get('budget_id')
            type_employes = request.query_params.getlist('type_employes')
            
            if not budget_id:
                return Response(
                    {'error': 'Le budget_id est requis'}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Vérification du budget
            try:
                budget = Budget.objects.get(id=budget_id, user=request.user)
            except Budget.DoesNotExist:
                return Response(
                    {'error': 'Budget non trouvé'}, 
                    status=status.HTTP_404_NOT_FOUND
                )
            
            # Récupération des employés
            employes_query = Employe.objects.filter(
                user=request.user,
                actif='ES'
            )
            
            if type_employes:
                employes_query = employes_query.filter(type_employe__in=type_employes)
            
            employes = employes_query.all()
            
            # Récupération des paramètres de salaire
            try:
                montant_salaire = MontantSalaire.objects.get(user=request.user)
            except MontantSalaire.DoesNotExist:
                return Response(
                    {'error': 'Configuration des salaires non trouvée'}, 
                    status=status.HTTP_404_NOT_FOUND
                )
            
            # Calcul du preview
            preview_data = []
            total_preview = Decimal('0.00')
            
            for employe in employes:
                salaire = self._calculer_salaire_employe(employe, montant_salaire)
                if salaire > 0:
                    preview_data.append({
                        'employe_id': str(employe.id),
                        'employe_nom': f"{employe.nom} {employe.prenom}",
                        'type_employe': employe.get_type_employe_display(),
                        'salaire': salaire
                    })
                    total_preview += Decimal(str(salaire))
            
            response_data = {
                'budget_nom': budget.nom,
                'budget_montant_actuel': budget.montant,
                'total_paiements_prevus': float(total_preview),
                'solde_apres_paiement': budget.montant - float(total_preview),
                'nombre_employes': len(preview_data),
                'employes': preview_data,
                'suffisant': budget.montant >= float(total_preview)
            }
            
            return Response(response_data)
            
        except Exception as e:
            logger.error(f"Erreur lors du preview: {str(e)}")
            return Response(
                {'error': f'Erreur lors du preview: {str(e)}'}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=False, methods=['get'])
    def statistiques(self, request):
        """Statistiques des paiements d'employés"""
        # Paiements du mois en cours
        debut_mois = timezone.now().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        paiements_mois = PaiementEmploye.objects.filter(
            user=request.user,
            date_paiement__gte=debut_mois
        ).aggregate(total=Sum('montant'))['total'] or 0
        
        # Total des paiements
        total_paiements = PaiementEmploye.objects.filter(
            user=request.user
        ).aggregate(total=Sum('montant'))['total'] or 0
        
        # Nombre de paiements
        nombre_paiements = PaiementEmploye.objects.filter(user=request.user).count()
        
        # Nombre d'employés payés ce mois
        employes_payes_mois = PaiementEmploye.objects.filter(
            user=request.user,
            date_paiement__gte=debut_mois
        ).values('id_employe').distinct().count()
        
        data = {
            'paiements_mois_courant': paiements_mois,
            'total_paiements': total_paiements,
            'nombre_paiements': nombre_paiements,
            'employes_payes_mois': employes_payes_mois,
            'moyenne_paiement': round(total_paiements / nombre_paiements, 2) if nombre_paiements > 0 else 0
        }
        
        return Response(data)

    @action(detail=False, methods=['get'])
    def par_employe(self, request):
        """Grouper les paiements par employé"""
        paiements = PaiementEmploye.objects.filter(user=request.user).select_related('id_employe')
        
        # Grouper par employé
        employes_paiements = {}
        for paiement in paiements:
            employe_id = paiement.id_employe.id
            employe_nom = f"{paiement.id_employe.nom} {paiement.id_employe.prenom}"
            
            if employe_id not in employes_paiements:
                employes_paiements[employe_id] = {
                    'employe_id': employe_id,
                    'employe_nom': employe_nom,
                    'total_paiements': 0,
                    'nombre_paiements': 0,
                    'dernier_paiement': None
                }
            
            employes_paiements[employe_id]['total_paiements'] += paiement.montant
            employes_paiements[employe_id]['nombre_paiements'] += 1
            
            if (employes_paiements[employe_id]['dernier_paiement'] is None or
                paiement.date_paiement > employes_paiements[employe_id]['dernier_paiement']):
                employes_paiements[employe_id]['dernier_paiement'] = paiement.date_paiement
        
        return Response(list(employes_paiements.values()))




class MontantSalaireViewSet(viewsets.ModelViewSet):
    """ViewSet pour la gestion des montants de salaire"""
    serializer_class = MontantSalaireSerializer
    permission_classes = [IsAuthenticated]
    pagination_class = CustomCursorPagination
    
    def get_queryset(self):
        """Retourner seulement la configuration de l'utilisateur connecté"""
        return MontantSalaire.objects.filter(user=self.request.user)
    
    def list(self, request, *args, **kwargs):
        """Récupérer ou créer la configuration des montants de salaire"""
        montant_salaire, created = MontantSalaire.objects.get_or_create(
            user=request.user,
            defaults={
                'salaire_mensuel': 0,
                'salaire_hebdomadaire': 0,
                'salaire_journalier': 0,
                'salaire_horaire': 0
            }
        )
        serializer = self.get_serializer(montant_salaire)
        return Response(serializer.data)
    
    def create(self, request, *args, **kwargs):
        """Créer ou mettre à jour la configuration"""
        try:
            montant_salaire = MontantSalaire.objects.get(user=request.user)
            serializer = self.get_serializer(montant_salaire, data=request.data, partial=True)
        except MontantSalaire.DoesNotExist:
            serializer = self.get_serializer(data=request.data)
        
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_200_OK)
    
    @action(detail=False, methods=['post'])
    def calculer(self, request):
        """Calculer automatiquement les autres montants basés sur un montant de référence"""
        montant_type = request.data.get('type')  # 'mensuel', 'hebdomadaire', 'journalier', 'horaire'
        montant_value = request.data.get('montant', 0)
        
        if not montant_type or montant_value <= 0:
            return Response(
                {'error': 'Type et montant requis'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Calculs basés sur des moyennes standard
        if montant_type == 'mensuel':
            mensuel = montant_value
            hebdomadaire = montant_value / 4.33  # ~4.33 semaines par mois
            journalier = montant_value / 30  # 30 jours par mois
            horaire = montant_value / (30 * 8)  # 8h par jour
        elif montant_type == 'hebdomadaire':
            hebdomadaire = montant_value
            mensuel = montant_value * 4.33
            journalier = montant_value / 7
            horaire = montant_value / (7 * 8)
        elif montant_type == 'journalier':
            journalier = montant_value
            mensuel = montant_value * 30
            hebdomadaire = montant_value * 7
            horaire = montant_value / 8
        elif montant_type == 'horaire':
            horaire = montant_value
            journalier = montant_value * 8
            hebdomadaire = montant_value * 8 * 7
            mensuel = montant_value * 8 * 30
        else:
            return Response(
                {'error': 'Type invalide'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        data = {
            'salaire_mensuel': round(mensuel, 2),
            'salaire_hebdomadaire': round(hebdomadaire, 2),
            'salaire_journalier': round(journalier, 2),
            'salaire_horaire': round(horaire, 2)
        }
        
        return Response(data)
    
    @action(detail=False, methods=['post'])
    def sauvegarder_calcul(self, request):
        """Calculer et sauvegarder automatiquement les montants"""
        montant_type = request.data.get('type')
        montant_value = request.data.get('montant', 0)
        
        if not montant_type or montant_value <= 0:
            return Response(
                {'error': 'Type et montant requis'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Effectuer les calculs (même logique que l'action calculer)
        if montant_type == 'mensuel':
            mensuel = montant_value
            hebdomadaire = montant_value / 4.33
            journalier = montant_value / 30
            horaire = montant_value / (30 * 8)
        elif montant_type == 'hebdomadaire':
            hebdomadaire = montant_value
            mensuel = montant_value * 4.33
            journalier = montant_value / 7
            horaire = montant_value / (7 * 8)
        elif montant_type == 'journalier':
            journalier = montant_value
            mensuel = montant_value * 30
            hebdomadaire = montant_value * 7
            horaire = montant_value / 8
        elif montant_type == 'horaire':
            horaire = montant_value
            journalier = montant_value * 8
            hebdomadaire = montant_value * 8 * 7
            mensuel = montant_value * 8 * 30
        else:
            return Response(
                {'error': 'Type invalide'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Sauvegarder dans la base de données
        montant_salaire, created = MontantSalaire.objects.get_or_create(
            user=request.user,
            defaults={
                'salaire_mensuel': round(mensuel, 2),
                'salaire_hebdomadaire': round(hebdomadaire, 2),
                'salaire_journalier': round(journalier, 2),
                'salaire_horaire': round(horaire, 2)
            }
        )
        
        if not created:
            montant_salaire.salaire_mensuel = round(mensuel, 2)
            montant_salaire.salaire_hebdomadaire = round(hebdomadaire, 2)
            montant_salaire.salaire_journalier = round(journalier, 2)
            montant_salaire.salaire_horaire = round(horaire, 2)
            montant_salaire.save()
        
        serializer = self.get_serializer(montant_salaire)
        return Response(serializer.data)


def check_entreprise_account(user):
    """
    Vérifie si l'utilisateur a un compte entreprise
    """
    return user.compte == 'entreprise'

def get_date_range(period):
    """
    Calcule la plage de dates selon la période spécifiée
    Formats acceptés: '1d', '3d', '1w', '1m', 'january-december', 'custom:YYYY-MM-DD:YYYY-MM-DD'
    """
    today = timezone.now().date()
    
    if period == '1d':
        start_date = today
        end_date = today + timedelta(days=1)
    elif period == '3d':
        start_date = today - timedelta(days=2)
        end_date = today + timedelta(days=1)
    elif period == '1w':
        start_date = today - timedelta(days=7)
        end_date = today + timedelta(days=1)
    elif period == '1m':
        start_date = today - relativedelta(months=1)
        end_date = today + timedelta(days=1)
    elif period == 'january-december':
        current_year = today.year
        start_date = datetime(current_year, 1, 1).date()
        end_date = datetime(current_year, 12, 31).date()
    elif period.startswith('custom:'):
        # Format: custom:YYYY-MM-DD:YYYY-MM-DD
        try:
            _, start_str, end_str = period.split(':')
            start_date = datetime.strptime(start_str, '%Y-%m-%d').date()
            end_date = datetime.strptime(end_str, '%Y-%m-%d').date()
        except ValueError:
            raise ValueError("Format de période personnalisée invalide. Utilisez 'custom:YYYY-MM-DD:YYYY-MM-DD'")
    else:
        raise ValueError("Période non supportée")
    
    return start_date, end_date

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def budget_statistics(request, budget_id):
    """
    Vue 1: Statistiques détaillées d'un budget spécifique
    """
    try:
        # Récupérer les paramètres
        period = request.GET.get('period', '1m')
        start_date, end_date = get_date_range(period)
        
        # Vérifier que le budget existe et appartient à l'utilisateur
        budget = Budget.objects.filter(id=budget_id, user=request.user).first()
        if not budget:
            return Response(
                {'error': 'Budget non trouvé'}, 
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Statistiques du budget
        budget_data = BudgetSerializer(budget).data
        
        # Catégories de dépenses avec leurs dépenses
        categories = CategorieDepense.objects.filter(
            id_budget=budget,
            created_at__date__range=[start_date, end_date]
        )
        
        categories_stats = []
        for categorie in categories:
            # Dépenses de cette catégorie dans la période
            depenses_categorie = Depense.objects.filter(
                id_cat_depense=categorie,
                created_at__date__range=[start_date, end_date]
            )
            
            depenses_data = DepenseSerializer(depenses_categorie, many=True).data
            total_depenses = depenses_categorie.aggregate(Sum('montant'))['montant__sum'] or 0
            
            categories_stats.append({
                'categorie': CategorieDepenseSerializer(categorie).data,
                'depenses': depenses_data,
                'total_depenses': total_depenses,
                'nombre_depenses': depenses_categorie.count(),
                'pourcentage_utilise': (total_depenses / categorie.montant_initial * 100) if categorie.montant_initial > 0 else 0
            })
        
        # Dépenses directes (sans catégorie)
        depenses_directes = Depense.objects.filter(
            id_budget=budget,
            id_cat_depense__isnull=True,
            created_at__date__range=[start_date, end_date]
        )
        
        # Entrées dans la période (seulement pour les comptes entreprise)
        entrees_data = {}
        total_entrees = 0
        if check_entreprise_account(request.user):
            entrees = Entree.objects.filter(
                id_budget=budget,
                created_at__date__range=[start_date, end_date]
            )
            total_entrees = entrees.aggregate(Sum('montant'))['montant__sum'] or 0
            entrees_data = {
                'entrees': EntreeSerializer(entrees, many=True).data,
                'total': total_entrees,
                'nombre': entrees.count()
            }
        else:
            entrees_data = {
                'message': 'Accès aux entrées réservé aux comptes entreprise',
                'total': 0,
                'nombre': 0
            }
        
        # Paiements employés dans la période
        paiements = PaiementEmploye.objects.filter(
            id_budget=budget,
            created_at__date__range=[start_date, end_date]
        )
        
        # Calculs des totaux
        total_depenses_directes = depenses_directes.aggregate(Sum('montant'))['montant__sum'] or 0
        total_paiements = paiements.aggregate(Sum('montant'))['montant__sum'] or 0
        total_depenses_categories = sum([cat['total_depenses'] for cat in categories_stats])
        total_depenses_global = total_depenses_directes + total_depenses_categories + total_paiements
        
        # Résumé des statistiques
        statistics = {
            'budget': budget_data,
            'periode': {
                'debut': start_date,
                'fin': end_date,
                'duree_jours': (end_date - start_date).days
            },
            'categories_depenses': categories_stats,
            'depenses_directes': {
                'depenses': DepenseSerializer(depenses_directes, many=True).data,
                'total': total_depenses_directes,
                'nombre': depenses_directes.count()
            },
            'entrees': entrees_data,
            'paiements_employes': {
                'total': total_paiements,
                'nombre': paiements.count()
            },
            'resume': {
                'montant_initial': budget.montant_initial,
                'montant_actuel': budget.montant,
                'total_depenses': total_depenses_global,
                'total_entrees': total_entrees,
                'pourcentage_utilise': (total_depenses_global / budget.montant_initial * 100) if budget.montant_initial > 0 else 0,
                'solde_theorique': budget.montant_initial - total_depenses_global + total_entrees
            }
        }
        
        return Response(statistics, status=status.HTTP_200_OK)
        
    except ValueError as e:
        return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
    except Exception as e:
        return Response({'error': 'Erreur interne du serveur'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def all_budgets_statistics(request):
    """
    Vue 2: Statistiques pour tous les budgets de l'utilisateur
    """
    try:
        period = request.GET.get('period', '1m')
        start_date, end_date = get_date_range(period)
        
        budgets = Budget.objects.filter(user=request.user)
        
        budgets_stats = []
        total_montant_initial = 0
        total_montant_actuel = 0
        total_depenses_global = 0
        total_entrees_global = 0
        
        for budget in budgets:
            # Statistiques par budget
            depenses_budget = Depense.objects.filter(
                id_budget=budget,
                created_at__date__range=[start_date, end_date]
            )
            
            paiements_budget = PaiementEmploye.objects.filter(
                id_budget=budget,
                created_at__date__range=[start_date, end_date]
            )
            
            total_depenses = depenses_budget.aggregate(Sum('montant'))['montant__sum'] or 0
            total_paiements = paiements_budget.aggregate(Sum('montant'))['montant__sum'] or 0
            total_budget_depenses = total_depenses + total_paiements
            
            # Gestion des entrées selon le type de compte
            total_entrees = 0
            entrees_count = 0
            if check_entreprise_account(request.user):
                entrees_budget = Entree.objects.filter(
                    id_budget=budget,
                    created_at__date__range=[start_date, end_date]
                )
                total_entrees = entrees_budget.aggregate(Sum('montant'))['montant__sum'] or 0
                entrees_count = entrees_budget.count()
            
            budgets_stats.append({
                'budget': BudgetSerializer(budget).data,
                'statistiques': {
                    'total_depenses': total_budget_depenses,
                    'total_entrees': total_entrees,
                    'nombre_depenses': depenses_budget.count(),
                    'nombre_entrees': entrees_count,
                    'nombre_paiements': paiements_budget.count(),
                    'pourcentage_utilise': (total_budget_depenses / budget.montant_initial * 100) if budget.montant_initial > 0 else 0,
                    'solde_theorique': budget.montant_initial - total_budget_depenses + total_entrees
                }
            })
            
            # Totaux globaux
            total_montant_initial += budget.montant_initial
            total_montant_actuel += budget.montant
            total_depenses_global += total_budget_depenses
            total_entrees_global += total_entrees
        
        return Response({
            'periode': {
                'debut': start_date,
                'fin': end_date,
                'duree_jours': (end_date - start_date).days
            },
            'budgets': budgets_stats,
            'resume_global': {
                'nombre_budgets': budgets.count(),
                'montant_initial_total': total_montant_initial,
                'montant_actuel_total': total_montant_actuel,
                'total_depenses_global': total_depenses_global,
                'total_entrees_global': total_entrees_global,
                'pourcentage_utilise_global': (total_depenses_global / total_montant_initial * 100) if total_montant_initial > 0 else 0,
                'solde_theorique_global': total_montant_initial - total_depenses_global + total_entrees_global,
                'type_compte': request.user.compte
            }
        }, status=status.HTTP_200_OK)
        
    except ValueError as e:
        return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
    except Exception as e:
        return Response({'error': 'Erreur interne du serveur'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def category_statistics(request, category_id):
    """
    Vue 3: Statistiques détaillées d'une catégorie de dépense
    """
    try:
        period = request.GET.get('period', '1m')
        start_date, end_date = get_date_range(period)
        
        # Vérifier que la catégorie existe et appartient à l'utilisateur
        categorie = CategorieDepense.objects.filter(id=category_id, user=request.user).first()
        if not categorie:
            return Response(
                {'error': 'Catégorie non trouvée'}, 
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Dépenses de cette catégorie dans la période
        depenses = Depense.objects.filter(
            id_cat_depense=categorie,
            created_at__date__range=[start_date, end_date]
        )
        
        # Statistiques par type de dépense
        stats_par_type = depenses.values('type_depense').annotate(
            total=Sum('montant'),
            nombre=Count('id')
        )
        
        # Évolution temporelle (par jour)
        evolution_quotidienne = []
        current_date = start_date
        while current_date <= end_date:
            depenses_jour = depenses.filter(created_at__date=current_date)
            total_jour = depenses_jour.aggregate(Sum('montant'))['montant__sum'] or 0
            evolution_quotidienne.append({
                'date': current_date,
                'total_depenses': total_jour,
                'nombre_depenses': depenses_jour.count()
            })
            current_date += timedelta(days=1)
        
        total_depenses = depenses.aggregate(Sum('montant'))['montant__sum'] or 0
        
        return Response({
            'categorie': CategorieDepenseSerializer(categorie).data,
            'budget_parent': BudgetSerializer(categorie.id_budget).data,
            'periode': {
                'debut': start_date,
                'fin': end_date,
                'duree_jours': (end_date - start_date).days
            },
            'depenses': DepenseSerializer(depenses, many=True).data,
            'statistiques': {
                'total_depenses': total_depenses,
                'nombre_depenses': depenses.count(),
                'pourcentage_utilise': (total_depenses / categorie.montant_initial * 100) if categorie.montant_initial > 0 else 0,
                'montant_restant': categorie.montant,
                'depense_moyenne': total_depenses / depenses.count() if depenses.count() > 0 else 0,
                'depense_quotidienne_moyenne': total_depenses / (end_date - start_date).days if (end_date - start_date).days > 0 else 0
            },
            'repartition_par_type': list(stats_par_type),
            'evolution_quotidienne': evolution_quotidienne
        }, status=status.HTTP_200_OK)
        
    except ValueError as e:
        return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
    except Exception as e:
        return Response({'error': 'Erreur interne du serveur'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def global_financial_report(request):
    """
    Vue 4: Bilan financier global de tous les budgets
    """
    try:
        period = request.GET.get('period', '1m')
        start_date, end_date = get_date_range(period)
        
        # Tous les budgets de l'utilisateur
        budgets = Budget.objects.filter(user=request.user)
        
        # Totaux globaux
        total_budgets_initial = budgets.aggregate(Sum('montant_initial'))['montant_initial__sum'] or 0
        total_budgets_actuel = budgets.aggregate(Sum('montant'))['montant__sum'] or 0
        
        # Dépenses globales dans la période
        all_depenses = Depense.objects.filter(
            id_budget__in=budgets,
            created_at__date__range=[start_date, end_date]
        )
        
        # Paiements globaux dans la période
        all_paiements = PaiementEmploye.objects.filter(
            id_budget__in=budgets,
            created_at__date__range=[start_date, end_date]
        )
        
        total_depenses = all_depenses.aggregate(Sum('montant'))['montant__sum'] or 0
        total_paiements = all_paiements.aggregate(Sum('montant'))['montant__sum'] or 0
        
        # Gestion des entrées selon le type de compte
        total_entrees = 0
        all_entrees = None
        if check_entreprise_account(request.user):
            all_entrees = Entree.objects.filter(
                id_budget__in=budgets,
                created_at__date__range=[start_date, end_date]
            )
            total_entrees = all_entrees.aggregate(Sum('montant'))['montant__sum'] or 0
        
        # Statistiques par type de budget
        stats_par_type_budget = budgets.values('type_budget').annotate(
            nombre=Count('id'),
            montant_total=Sum('montant_initial'),
            montant_restant=Sum('montant')
        )
        
        # Répartition des dépenses par type
        stats_depenses_par_type = all_depenses.values('type_depense').annotate(
            total=Sum('montant'),
            nombre=Count('id')
        )
        
        # Budgets avec alerte (moins de 10% restant)
        budgets_alerte = budgets.filter(
            montant__lt=models.F('montant_initial') * 0.1
        )
        
        # Budgets épuisés
        budgets_epuises = budgets.filter(montant__lte=0)
        
        # Évolution mensuelle (si période > 1 mois)
        evolution_mensuelle = []
        if (end_date - start_date).days > 31:
            current_month = start_date.replace(day=1)
            while current_month <= end_date:
                next_month = current_month + relativedelta(months=1)
                
                depenses_mois = all_depenses.filter(
                    created_at__date__gte=current_month,
                    created_at__date__lt=next_month
                ).aggregate(Sum('montant'))['montant__sum'] or 0
                
                entrees_mois = 0
                if check_entreprise_account(request.user) and all_entrees:
                    entrees_mois = all_entrees.filter(
                        created_at__date__gte=current_month,
                        created_at__date__lt=next_month
                    ).aggregate(Sum('montant'))['montant__sum'] or 0
                
                evolution_mensuelle.append({
                    'mois': current_month.strftime('%Y-%m'),
                    'depenses': depenses_mois,
                    'entrees': entrees_mois,
                    'solde': entrees_mois - depenses_mois
                })
                
                current_month = next_month
        
        response_data = {
            'periode': {
                'debut': start_date,
                'fin': end_date,
                'duree_jours': (end_date - start_date).days
            },
            'resume_financier': {
                'nombre_budgets_total': budgets.count(),
                'montant_initial_total': total_budgets_initial,
                'montant_actuel_total': total_budgets_actuel,
                'total_depenses_periode': total_depenses,
                'total_paiements_periode': total_paiements,
                'solde_global': total_budgets_actuel,
                'pourcentage_utilise_global': ((total_budgets_initial - total_budgets_actuel) / total_budgets_initial * 100) if total_budgets_initial > 0 else 0,
                'type_compte': request.user.compte
            },
            'alertes': {
                'budgets_en_alerte': budgets_alerte.count(),
                'budgets_epuises': budgets_epuises.count(),
                'budgets_alerte_details': BudgetSerializer(budgets_alerte, many=True).data,
                'budgets_epuises_details': BudgetSerializer(budgets_epuises, many=True).data
            },
            'statistiques_detaillees': {
                'repartition_budgets_par_type': list(stats_par_type_budget),
                'repartition_depenses_par_type': list(stats_depenses_par_type),
                'nombre_transactions': {
                    'depenses': all_depenses.count(),
                    'paiements': all_paiements.count()
                },
                'moyennes': {
                    'depense_moyenne': total_depenses / all_depenses.count() if all_depenses.count() > 0 else 0,
                    'depense_quotidienne_moyenne': total_depenses / (end_date - start_date).days if (end_date - start_date).days > 0 else 0
                }
            },
            'evolution_mensuelle': evolution_mensuelle if evolution_mensuelle else None
        }
        
        # Ajouter les données d'entrées seulement pour les comptes entreprise
        if check_entreprise_account(request.user):
            response_data['resume_financier']['total_entrees_periode'] = total_entrees
            response_data['resume_financier']['flux_net_periode'] = total_entrees - total_depenses - total_paiements
            response_data['statistiques_detaillees']['nombre_transactions']['entrees'] = all_entrees.count()
            response_data['statistiques_detaillees']['moyennes']['entree_moyenne'] = total_entrees / all_entrees.count() if all_entrees.count() > 0 else 0
        else:
            response_data['resume_financier']['message_entrees'] = 'Accès aux entrées réservé aux comptes entreprise'
            response_data['resume_financier']['flux_net_periode'] = -total_depenses - total_paiements
        
        return Response(response_data, status=status.HTTP_200_OK)
        
    except ValueError as e:
        return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
    except Exception as e:
        return Response({'error': 'Erreur interne du serveur'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)