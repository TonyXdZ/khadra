from django.contrib import admin
from leaflet.admin import LeafletGeoAdmin
from users.models import Profile, Country, City

admin.site.register(Country, LeafletGeoAdmin)
admin.site.register(City, LeafletGeoAdmin)
admin.site.register(Profile, LeafletGeoAdmin)