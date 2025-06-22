## 📊 Endpoints API

### Endpoints REST principaux (via router)

- `/api/budget/budgets/` : CRUD sur les budgets
- `/api/budget/categories-depense/` : CRUD sur les catégories de dépense
- `/api/budget/depenses/` : CRUD sur les dépenses
- `/api/budget/entrees/` : CRUD sur les entrées (entreprise uniquement)
- `/api/budget/notifications/` : CRUD sur les notifications
- `/api/budget/conseils/` : CRUD sur les conseils IA
- `/api/budget/employes/` : CRUD sur les employés (entreprise uniquement)
- `/api/budget/paiements-employes/` : CRUD sur les paiements d'employés (entreprise uniquement)
- `/api/budget/montants-salaire/` : CRUD sur la configuration des salaires (entreprise uniquement)

### Endpoints personnalisés et actions avancées

- `/api/budget/budgets/{id}/categories/` : Catégories d'un budget
- `/api/budget/budgets/{id}/depenses/` : Dépenses d'un budget
- `/api/budget/budgets/{id}/resume/` : Statistiques et résumé d'un budget
- `/api/budget/budgets/export_csv/` : Export CSV de tous les budgets
- `/api/budget/budgets/export_json/` : Export JSON de tous les budgets
- `/api/budget/budgets/rapport_complet/` : Rapport complet de tous les budgets
- `/api/budget/categories-depense/{id}/depenses/` : Dépenses d'une catégorie
- `/api/budget/categories-depense/{id}/stats/` : Statistiques d'une catégorie
- `/api/budget/categories-depense/stats-globales/` : Statistiques globales sur toutes les catégories
- `/api/budget/depenses/?categorie_id=...&budget_id=...` : Filtrage des dépenses par catégorie ou budget
- `/api/budget/entrees/statistiques/` : Statistiques sur les entrées (entreprise)
- `/api/budget/notifications/non-lues/` : Notifications non lues
- `/api/budget/notifications/marquer-toutes-lues/` : Marquer toutes les notifications comme lues
- `/api/budget/notifications/{id}/marquer_lue/` : Marquer une notification comme lue
- `/api/budget/conseils/recents/` : Conseils IA récents
- `/api/budget/employes/actifs/` : Employés actifs (entreprise)
- `/api/budget/employes/par_statut/{statut}/` : Employés par statut (entreprise)
- `/api/budget/employes/export_csv/` : Export CSV des employés (entreprise)
- `/api/budget/employes/rapport_complet/` : Rapport complet des employés (entreprise)
- `/api/budget/employes/{id}/paiements/` : Paiements d'un employé (entreprise)
- `/api/budget/paiements-employes/paiement-global/` : Paiement global de tous les employés (entreprise)
- `/api/budget/paiements-employes/preview-paiement-global/` : Aperçu du paiement global (entreprise)
- `/api/budget/paiements-employes/statistiques/` : Statistiques sur les paiements (entreprise)
- `/api/budget/paiements-employes/par-employe/` : Paiements groupés par employé (entreprise)
- `/api/budget/montants-salaire/calculer/` : Calcul automatique des montants de salaire (entreprise)
- `/api/budget/montants-salaire/sauvegarder_calcul/` : Sauvegarde des calculs de salaire (entreprise)
- `/api/budget/budgets/<uuid:budget_id>/statistiques/` : Statistiques détaillées d'un budget
- `/api/budget/budgets/statistiques-globales/` : Statistiques globales sur tous les budgets
- `/api/budget/categories/<uuid:category_id>/statistiques/` : Statistiques détaillées d'une catégorie
- `/api/budget/rapport-financier-global/` : Rapport financier global de l'utilisateur
- `/api/budget/test-conseils/` : Générer un conseil IA de test selon le type de compte

Chaque endpoint respecte les permissions et restrictions selon le type de compte (particulier ou entreprise). Voir la documentation détaillée pour les paramètres et exemples de réponse.
