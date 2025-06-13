from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404
from django.db.models import Q, Sum
from django.utils import timezone
from datetime import datetime, timedelta

from .models import (
    Budget, CategorieDepense, Depense, Entree, Employe, 
    Notification, Conseil, PaiementEmploye, MontantSalaire
)
from .serializers import (
    BudgetSerializer, CategorieDepenseSerializer, DepenseSerializer,
    EntreeSerializer, NotificationSerializer, ConseilSerializer,
    EmployeSerializer, PaiementEmployeSerializer, MontantSalaireSerializer
)


class BudgetViewSet(viewsets.ModelViewSet):
    """ViewSet pour la gestion des budgets"""
    serializer_class = BudgetSerializer
    permission_classes = [IsAuthenticated]
    
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
    
    def get_queryset(self):
        """Retourner seulement les catégories de l'utilisateur connecté"""
        queryset = CategorieDepense.objects.filter(user=self.request.user).order_by('-created_at')
        
        # Filtrer par budget si spécifié
        budget_id = self.request.query_params.get('budget_id')
        if budget_id:
            queryset = queryset.filter(id_budget_id=budget_id)
            
        return queryset
    
    @action(detail=True, methods=['get'])
    def depenses(self, request, pk=None):
        """Récupérer toutes les dépenses d'une catégorie"""
        categorie = self.get_object()
        depenses = Depense.objects.filter(id_cat_depense=categorie, user=request.user)
        serializer = DepenseSerializer(depenses, many=True)
        return Response(serializer.data)


class DepenseViewSet(viewsets.ModelViewSet):
    """ViewSet pour la gestion des dépenses"""
    serializer_class = DepenseSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        """Retourner seulement les dépenses de l'utilisateur connecté"""
        queryset = Depense.objects.filter(user=self.request.user).order_by('-created_at')
        
        # Filtres optionnels
        budget_id = self.request.query_params.get('budget_id')
        categorie_id = self.request.query_params.get('categorie_id')
        
        if budget_id:
            queryset = queryset.filter(id_budget_id=budget_id)
        if categorie_id:
            queryset = queryset.filter(id_cat_depense_id=categorie_id)
            
        return queryset
    
    @action(detail=False, methods=['get'])
    def statistiques(self, request):
        """Statistiques des dépenses de l'utilisateur"""
        # Dépenses du mois en cours
        debut_mois = timezone.now().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        depenses_mois = Depense.objects.filter(
            user=request.user,
            created_at__gte=debut_mois
        ).aggregate(total=Sum('montant'))['total'] or 0
        
        # Total des dépenses
        total_depenses = Depense.objects.filter(
            user=request.user
        ).aggregate(total=Sum('montant'))['total'] or 0
        
        # Nombre de dépenses
        nombre_depenses = Depense.objects.filter(user=request.user).count()
        
        data = {
            'depenses_mois_courant': depenses_mois,
            'total_depenses': total_depenses,
            'nombre_depenses': nombre_depenses,
            'moyenne_depense': round(total_depenses / nombre_depenses, 2) if nombre_depenses > 0 else 0
        }
        
        return Response(data)


class EntreeViewSet(viewsets.ModelViewSet):
    """ViewSet pour la gestion des entrées"""
    serializer_class = EntreeSerializer
    permission_classes = [IsAuthenticated]
    
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
    
    def get_queryset(self):
        """Retourner seulement les notifications de l'utilisateur connecté"""
        return Notification.objects.filter(user=self.request.user).order_by('-created_at')
    
    @action(detail=False, methods=['get'])
    def non_lues(self, request):
        """Récupérer les notifications non lues"""
        notifications = Notification.objects.filter(
            user=request.user,
            is_read=False
        ).order_by('-created_at')
        serializer = self.get_serializer(notifications, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def marquer_lue(self, request, pk=None):
        """Marquer une notification comme lue"""
        notification = self.get_object()
        notification.is_read = True
        notification.save()
        return Response({'status': 'notification marquée comme lue'})
    
    @action(detail=False, methods=['post'])
    def marquer_toutes_lues(self, request):
        """Marquer toutes les notifications comme lues"""
        Notification.objects.filter(user=request.user, is_read=False).update(is_read=True)
        return Response({'status': 'toutes les notifications marquées comme lues'})


class ConseilViewSet(viewsets.ModelViewSet):
    """ViewSet pour la gestion des conseils"""
    serializer_class = ConseilSerializer
    permission_classes = [IsAuthenticated]
    
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


# Sérialiseurs pour les comptes entreprise uniquement
class EmployeViewSet(viewsets.ModelViewSet):
    """ViewSet pour la gestion des employés (comptes entreprise uniquement)"""
    serializer_class = EmployeSerializer
    permission_classes = [IsAuthenticated]
    
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
    
    @action(detail=False, methods=['get'])
    def actifs(self, request):
        """Récupérer les employés actifs"""
        employes = Employe.objects.filter(user=request.user, is_active=True)
        serializer = self.get_serializer(employes, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def desactiver(self, request, pk=None):
        """Désactiver un employé"""
        employe = self.get_object()
        employe.is_active = False
        employe.save()
        return Response({'status': 'employé désactivé'})
    
    @action(detail=True, methods=['post'])
    def activer(self, request, pk=None):
        """Activer un employé"""
        employe = self.get_object()
        employe.is_active = True
        employe.save()
        return Response({'status': 'employé activé'})


class PaiementEmployeViewSet(viewsets.ModelViewSet):
    """ViewSet pour la gestion des paiements d'employés"""
    serializer_class = PaiementEmployeSerializer
    permission_classes = [IsAuthenticated]
    
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