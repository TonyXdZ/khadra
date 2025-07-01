from django.urls import path
from users import views

urlpatterns = [
    path('profile/new/', views.ProfileCreateView.as_view(), name='create-profile'),
]