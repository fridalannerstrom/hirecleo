"""
URL configuration for project_cleo project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from django.contrib.auth import views as auth_views
from django.conf import settings
from django.conf.urls.static import static
from django.http import HttpResponse
from django.contrib import admin
from django.urls import path, include
from users import views as user_views
from django.contrib.auth import views as auth_views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', auth_views.LoginView.as_view(template_name='auth-login-basic.html'), name='login'),
    path('accounts/', include('django.contrib.auth.urls')),
    path('', include('core.urls')),  # Dashboard, kandidater, etc
    path('candidates/', include('candidates.urls')),
    path('generator/', include('generator.urls')),
    path('jobs/', include('jobs.urls')),
    path('compare-candidates/', include('comparator.urls')),
    path('testanalyzer/', include('testanalyzer.urls')),
    path('users/', include('users.urls')),

    # Root-nivå-vyer från users
    path('dashboard/', user_views.dashboard, name='dashboard'),
    path('login/', auth_views.LoginView.as_view(template_name='auth-login-basic.html'), name='login'),
    path('logout/', user_views.logout_view, name='logout'),
    path('skapa-konto/', user_views.RegisterView.as_view(), name='register'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)