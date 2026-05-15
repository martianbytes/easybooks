# ============================================================
# accounts/urls.py
# ============================================================
from django.urls import path
from .views import RegisterView, UserLoginView, UserLogoutView, ProfileView, EditProfileView, BecomeSellerView

app_name = 'accounts'

urlpatterns = [
    path('register/', RegisterView.as_view(), name='register'),
    path('login/', UserLoginView.as_view(), name='login'),
    path('logout/', UserLogoutView.as_view(), name='logout'),
    path('profile/', ProfileView.as_view(), name='profile'),
    path('profile/edit/', EditProfileView.as_view(), name='edit_profile'),
    path('become-seller/', BecomeSellerView.as_view(), name='become_seller'),
]