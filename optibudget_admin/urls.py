from django.urls import path
from .views import login, profil, searchAccount, resetPassword, signup, changePassword, dashboardadmin, parametre

urlpatterns = [
    path('login/',login, name='login'),
    path('profil/',profil, name='profil'),
    path('resetPassword/',resetPassword, name='resetPassword'),
    path('searchAccount/',searchAccount, name='searchAccount'),
    path('signup/',signup, name='signup'),
    path('changePassword/',changePassword, name='changePassword'),
    path('dashboardadmin/',dashboardadmin, name='dashboardadmin'),
    path('parametre/',parametre, name='parametre'),
]
 