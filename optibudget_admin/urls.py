from django.urls import path
from . import views

app_name = 'optibudget_admin'

urlpatterns = [
    path('login/', views.login, name='login'),
    path('profil/', views.profil, name='profil'),
    path('reset-password/', views.resetPassword, name='reset_password'),
    path('search-account/', views.searchAccount, name='search_account'),
    path('change-password/', views.changePassword, name='change_password'),
    path('signup/', views.signup, name='signup'),
    path('admin/dashboard/', views.dashboardadmin, name='dashboardadmin'),
    path('admin/parametre/', views.parametre, name='parametre'),
]
