# ============================================================
# accounts/urls.py
# ============================================================
from django.urls import path
from django.contrib.auth import views as auth_views
from .views import (
    RegisterView,
    UserLoginView,
    UserLogoutView,
    ProfileView,
    EditProfileView,
    BecomeSellerView,
    ChangePasswordView,
    PublicProfileView,
)

app_name = "accounts"

urlpatterns = [
    path("register/", RegisterView.as_view(), name="register"),
    path("login/", UserLoginView.as_view(), name="login"),
    path("logout/", UserLogoutView.as_view(), name="logout"),
    path("profile/", ProfileView.as_view(), name="profile"),
    path("profile/<str:username>/", PublicProfileView.as_view(), name="public_profile"),
    path("profile/edit/", EditProfileView.as_view(), name="edit_profile"),
    path("become-seller/", BecomeSellerView.as_view(), name="become_seller"),
    path("change-password/", ChangePasswordView.as_view(), name="change_password"),

    # ── Password reset (Django built-in) ──────────────────────────
    path("password-reset/",
        auth_views.PasswordResetView.as_view(
            template_name="accounts/password_reset.html",
            email_template_name="accounts/password_reset_email.txt",
            html_email_template_name="accounts/password_reset_email.html",
            subject_template_name="accounts/password_reset_subject.txt",
            success_url="/accounts/password-reset/done/",
        ),
        name="password_reset",
    ),
    path("password-reset/done/",
        auth_views.PasswordResetDoneView.as_view(
            template_name="accounts/password_reset_done.html",
        ),
        name="password_reset_done",
    ),
    path("password-reset/<uidb64>/<token>/",
        auth_views.PasswordResetConfirmView.as_view(
            template_name="accounts/password_reset_confirm.html",
            success_url="/accounts/password-reset/complete/",
        ),
        name="password_reset_confirm",
    ),
    path("password-reset/complete/",
        auth_views.PasswordResetCompleteView.as_view(
            template_name="accounts/password_reset_complete.html",
        ),
        name="password_reset_complete",
    ),
]
