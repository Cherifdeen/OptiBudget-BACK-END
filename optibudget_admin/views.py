from django.shortcuts import render
from django.http import HttpResponse

# Create your views here.
def login(request):
    return render (request, 'accounts/login.html') 

def profil(request):
    return render (request, 'accounts/profil.html')

def resetPassword(request):
    return render (request, 'accounts/resetPassword.html')

def searchAccount(request):
    return render (request, 'accounts/searchAccount.html')

def changePassword(request):
    return render (request, 'accounts/changePassword.html')

def signup(request):
    return render (request, 'accounts/signup.html')

def dashboardadmin(request):
    return render (request, 'admin/dashboardadmin.html')

def parametre(request):
    return render (request, 'admin/parametre.html')
