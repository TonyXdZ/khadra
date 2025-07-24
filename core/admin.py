from django.contrib import admin
from leaflet.admin import LeafletGeoAdmin
from core.models import Initiative, InitiativeReview

admin.site.register(Initiative, LeafletGeoAdmin)
admin.site.register(InitiativeReview)