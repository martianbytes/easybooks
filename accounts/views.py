from django.contrib import messages
from django.contrib.auth.models import User
from django.contrib.auth.views import LoginView as DjangoLoginView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy
from django.views.generic import CreateView, DetailView, UpdateView
from django.http import HttpResponseRedirect

from .forms import UserRegistrationForm, UserProfileForm
from .models import UserProfile


class RegisterView(CreateView):
    model = User
    form_class = UserRegistrationForm
    template_name = "accounts/register.html"
    success_url = reverse_lazy("accounts:login")

    def form_valid(self, form):
        user = form.save()
        UserProfile.objects.get_or_create(user=user, defaults={"role": "buyer"})
        messages.success(self.request, "Account created successfully.")
        return HttpResponseRedirect(self.get_success_url())


class UserLoginView(DjangoLoginView):
    template_name = "accounts/login.html"
    redirect_authenticated_user = True


class UserProfileView(LoginRequiredMixin, DetailView):
    model = UserProfile
    template_name = "accounts/profile.html"
    context_object_name = "profile"

    def get_object(self, queryset=None):
        profile, _ = UserProfile.objects.get_or_create(
            user=self.request.user,
            defaults={"role": "buyer"},
        )
        return profile


class EditProfileView(LoginRequiredMixin, UpdateView):
    model = UserProfile
    form_class = UserProfileForm
    template_name = "accounts/edit-profile.html"
    success_url = reverse_lazy("accounts:profile")

    def get_object(self, queryset=None):
        profile, _ = UserProfile.objects.get_or_create(
            user=self.request.user,
            defaults={"role": "buyer"},
        )
        return profile

    def form_valid(self, form):
        messages.success(self.request, "Profile updated successfully.")
        return super().form_valid(form)