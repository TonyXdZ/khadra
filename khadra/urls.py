from django.contrib import admin
from django.conf import settings
from django.conf.urls.static import static
from django.urls import path, include
from core.views import HomeView, CreateInitiativeView, InitiativeDetails

urlpatterns = [
    path('', HomeView.as_view(), name='home'),
    path('initiative/new/', CreateInitiativeView.as_view(), name='create-initiative'),
    path('initiative/<pk>/', InitiativeDetails.as_view(), name='initiative-detail'),
    path('admin/', admin.site.urls),
    path('accounts/', include('allauth.urls')),
    path('users/', include('users.urls'))
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)