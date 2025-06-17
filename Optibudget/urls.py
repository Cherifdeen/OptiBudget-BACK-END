
from django.contrib import admin
from django.urls import path, include
from budgetManager.admin import admin_site 
urlpatterns = [
    
    path('admin/', admin.site.urls),
    # path('admin/', admin_site.urls),
    path('api-auth/', include('rest_framework.urls')),
    path('OptiAdmin/', include('optibudget_admin.urls')),
    path('api/', include([
        path('accounts/', include('accounts.urls')),
        path('budgetManager/', include('budgetManager.urls')),
    ])),
]



