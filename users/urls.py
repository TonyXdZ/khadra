from django.urls import path
from users import views

urlpatterns = [
    path('profile/new/', views.ProfileCreateView.as_view(), name='create-profile'),
    path('profile/', views.MyProfileView.as_view(), name='profile'),
    path('profile/update/', views.ProfileUpdateView.as_view(), name='profile-update'),
]