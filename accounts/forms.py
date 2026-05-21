# ============================================================
# accounts/forms.py
# ============================================================
import re
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
    # ── Individual field validation ───────────────────────────────────────

    def clean_username(self):
        """
        Validates username.
        - Strip extra spaces
        - Minimum 3 characters
        - Maximum 30 characters
        - Only letters, numbers, and underscores allowed
        - No spaces allowed
        """
        username = self.cleaned_data.get("username") or ""
        username = username.strip()

        if len(username) < 3:
            raise forms.ValidationError(
                "Username must be at least 3 characters long."
            )

        if len(username) > 30:
            raise forms.ValidationError(
                "Username cannot exceed 30 characters."
            )

        # Only letters, numbers, and underscores
        if not re.match(r"^[a-zA-Z0-9_]+$", username):
            raise forms.ValidationError(
                "Username can only contain letters, numbers, and underscores. "
                "No spaces or special characters allowed."
            )

        return username

    def clean_email(self):
        """
        Validates email.
        - Django already checks email format ✅
        - We add: check if email is already registered
        """
        email = self.cleaned_data.get("email") or ""
        email = email.strip().lower()

        # Check if this email is already used by another user
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError(
                "This email address is already registered. "
                "Please use a different email or login instead."
            )

        return email

    def clean_first_name(self):
        """
        Validates first name.
        - Optional field — skip if empty
        - If provided: minimum 2 characters
        - Letters, spaces and hyphens only
        """
        first_name = self.cleaned_data.get("first_name") or ""
        first_name = first_name.strip()

        # Optional — if empty skip all checks
        if not first_name:
            return first_name

        if len(first_name) < 2:
            raise forms.ValidationError(
                "First name must be at least 2 characters long."
            )

        if not re.match(r"^[a-zA-Z\s\-]+$", first_name):
            raise forms.ValidationError(
                "First name can only contain letters, spaces, and hyphens."
            )

        return first_name

    def clean_last_name(self):
        """
        Validates last name.
        - Optional field — skip if empty
        - If provided: minimum 2 characters
        - Letters, spaces and hyphens only
        """
        last_name = self.cleaned_data.get("last_name") or ""
        last_name = last_name.strip()

        # Optional — if empty skip all checks
        if not last_name:
            return last_name

        if len(last_name) < 2:
            raise forms.ValidationError(
                "Last name must be at least 2 characters long."
            )

        if not re.match(r"^[a-zA-Z\s\-]+$", last_name):
            raise forms.ValidationError(
                "Last name can only contain letters, spaces, and hyphens."
            )

        return last_name

class ProfileUpdateForm(forms.ModelForm):
    """Form for updating user profile — with styled widget attrs."""

    class Meta:
        model = Profile
        fields = ["avatar", "bio", "phone", "city", "district"]
        widgets = {
            "bio": forms.Textarea(
                attrs={
                    "placeholder": "Tell readers a little about yourself…",
                    "rows": 4,
                }
            ),
            "phone": forms.TextInput(
                attrs={
                    "placeholder": "e.g. +977 98xxxxxxxx",
                    "type": "tel",
                }
            ),
            "city": forms.TextInput(
                attrs={
                    "placeholder": "e.g. Bharatpur",
                }
            ),
            "district": forms.TextInput(
                attrs={
                    "placeholder": "e.g. Chitwan",
                }
            ),
        }


class SellerReviewForm(forms.ModelForm):
    """Form for creating seller reviews."""

    class Meta:
        model = SellerReview
        fields = ["rating", "comment"]
