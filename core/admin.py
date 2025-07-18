from django.contrib import admin
from leaflet.admin import LeafletGeoAdmin
from core.models import Initiative

admin.site.register(Initiative, LeafletGeoAdmin)