# ============================================================
# accounts/forms.py
# ============================================================
from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm
from .models import Profile, SellerReview


class UserRegistrationForm(UserCreationForm):
    """Form for user registration."""

    email = forms.EmailField(required=True)
    first_name = forms.CharField(max_length=100, required=False)
    last_name = forms.CharField(max_length=100, required=False)

    class Meta:
        model = User
        fields = [
            "username",
            "email",
            "first_name",
            "last_name",
            "password1",
            "password2",
        ]


class ProfileUpdateForm(forms.ModelForm):
    """Form for updating user profile."""

    class Meta:
        model = Profile
        fields = ["avatar", "bio", "phone", "city", "district"]


class SellerReviewForm(forms.ModelForm):
    """Form for creating seller reviews."""

    class Meta:
        model = SellerReview
        fields = ["rating", "comment"]
