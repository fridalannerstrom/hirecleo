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
from hello_world import views as index_views
from django.contrib.auth import views as auth_views
from django.conf import settings
from django.conf.urls.static import static
from django.http import HttpResponse

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', auth_views.LoginView.as_view(template_name='auth-login-basic.html'), name='login'),
    path('accounts/', include('django.contrib.auth.urls')),
    path('', include('hello_world.urls')),  # Dashboard, kandidater, etc
    path('api/', include('hello_world.api_urls')),  # API-endpoints separerade
    path("api/test/", lambda request: HttpResponse("Hej från test!")),
    path('candidates/', include('candidates.urls')),
    path('generator/', include('generator.urls')),
    path('jobs/', include('jobs.urls')),
    path('compare-candidates/', include('comparator.urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)