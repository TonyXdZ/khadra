from django.contrib import admin
from users.models import Profile, Country, City

admin.site.register(Country)
admin.site.register(City)
admin.site.register(Profile)