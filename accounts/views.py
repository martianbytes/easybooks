# ============================================================
# accounts/views.py
# ============================================================
from django.contrib import messages
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.views import LoginView, LogoutView, PasswordChangeView
from django.urls import reverse_lazy
from django.views.generic import CreateView, DetailView, UpdateView
from django.shortcuts import redirect
from .forms import UserRegistrationForm, ProfileUpdateForm
from .models import Profile
from django.views import View
from django.http import HttpResponseRedirect


class RegisterView(CreateView):
    model = User
    form_class = UserRegistrationForm
    template_name = "accounts/register.html"
    success_url = reverse_lazy("accounts:login")

    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            return redirect("books:home")
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        user = form.save()
        messages.success(self.request, "Account created! Please log in.")
        return super().form_valid(form)


class UserLoginView(LoginView):
    template_name = "accounts/login.html"
    redirect_authenticated_user = True

    def get_success_url(self):
        return reverse_lazy("books:home")


class UserLogoutView(LogoutView):
    next_page = "books:home"

    def dispatch(self, request, *args, **kwargs):
        messages.success(request, "Logged out successfully!")
        return super().dispatch(request, *args, **kwargs)


class ProfileView(LoginRequiredMixin, DetailView):
    model = Profile
    template_name = "accounts/profile.html"
    context_object_name = "profile"

    def get_object(self, queryset=None):
        return self.request.user.profile  # type: ignore

    def get_context_data(self, **kwargs):
        from books.models import Transaction
        from django.db.models import Sum, Max, Min, Count
        from django.db.models.functions import TruncMonth
        from django.utils import timezone
        import json

        ctx = super().get_context_data(**kwargs)
        user = self.request.user

        # ── Sales analytics (completed only) ─────────────────────────
        sales_qs = Transaction.objects.filter(seller=user, status='completed')
        sales_agg = sales_qs.aggregate(
            total_earned=Sum('price'),
            highest_sale=Max('price'),
            lowest_sale=Min('price'),
            total_sales=Count('id'),
        )

        # ── Purchase analytics (completed only) ──────────────────────
        purchases_qs = Transaction.objects.filter(buyer=user, status='completed')
        purchases_agg = purchases_qs.aggregate(
            total_spent=Sum('price'),
            highest_purchase=Max('price'),
            lowest_purchase=Min('price'),
            total_purchases=Count('id'),
        )

        # ── Monthly chart data (last 6 months) ───────────────────────
        six_months_ago = timezone.now() - timezone.timedelta(days=180)

        sales_by_month = (
            sales_qs.filter(created_at__gte=six_months_ago)
            .annotate(month=TruncMonth('created_at'))
            .values('month')
            .annotate(total=Sum('price'), count=Count('id'))
            .order_by('month')
        )
        purchases_by_month = (
            purchases_qs.filter(created_at__gte=six_months_ago)
            .annotate(month=TruncMonth('created_at'))
            .values('month')
            .annotate(total=Sum('price'), count=Count('id'))
            .order_by('month')
        )

        # Build unified month labels
        months_set = set()
        for r in sales_by_month:
            months_set.add(r['month'].strftime('%b %Y'))
        for r in purchases_by_month:
            months_set.add(r['month'].strftime('%b %Y'))
        month_labels = sorted(months_set, key=lambda m: timezone.datetime.strptime(m, '%b %Y'))

        sales_data = {r['month'].strftime('%b %Y'): float(r['total'] or 0) for r in sales_by_month}
        purchases_data = {r['month'].strftime('%b %Y'): float(r['total'] or 0) for r in purchases_by_month}

        chart_data = {
            'labels': month_labels,
            'sales': [sales_data.get(m, 0) for m in month_labels],
            'purchases': [purchases_data.get(m, 0) for m in month_labels],
        }

        from books.models import Book as BookModel
        ctx.update({
            # Sales (completed only)
            'total_earned': round(float(sales_agg['total_earned'] or 0), 2),
            'highest_sale': round(float(sales_agg['highest_sale'] or 0), 2),
            'lowest_sale': round(float(sales_agg['lowest_sale'] or 0), 2),
            'total_sales_count': sales_agg['total_sales'] or 0,
            # Purchases (completed only)
            'total_spent': round(float(purchases_agg['total_spent'] or 0), 2),
            'highest_purchase': round(float(purchases_agg['highest_purchase'] or 0), 2),
            'lowest_purchase': round(float(purchases_agg['lowest_purchase'] or 0), 2),
            'total_purchases_count': purchases_agg['total_purchases'] or 0,
            # Chart
            'chart_data_json': json.dumps(chart_data),
            # Recent completed transactions
            'recent_sales': sales_qs.select_related('book', 'buyer').order_by('-created_at')[:5],
            'recent_purchases': purchases_qs.select_related('book', 'seller').order_by('-created_at')[:5],
            # Recent listings (most recently listed first)
            'recent_listings': BookModel.objects.filter(
                seller=user, is_active=True
            ).exclude(status='sold').prefetch_related('images', 'authors').order_by('-created_at')[:4],
        })
        return ctx


class EditProfileView(LoginRequiredMixin, UpdateView):
    model = Profile
    form_class = ProfileUpdateForm
    template_name = "accounts/edit_profile.html"
    success_url = reverse_lazy("accounts:profile")

    def get_object(self, queryset=None):
        return self.request.user.profile  # type: ignore

    def form_valid(self, form):
        messages.success(self.request, "Profile updated successfully.")
        return super().form_valid(form)


class BecomeSellerView(LoginRequiredMixin, View):
    """Convert user to seller."""

    def get(self, request, *args, **kwargs):
        profile = request.user.profile  # type: ignore
        profile.is_seller = True
        profile.save()
        messages.success(request, "You are now a seller!")
        return redirect("accounts:profile")


class ChangePasswordView(LoginRequiredMixin, PasswordChangeView):
    template_name = "accounts/change_password.html"
    success_url = reverse_lazy("accounts:profile")

    def form_valid(self, form):
        messages.success(self.request, "Password changed successfully.")
        return super().form_valid(form)

class PublicProfileView(DetailView):
    template_name = "accounts/public_profile.html"
    context_object_name = "profile_user"

    def get_object(self, queryset=None):
        from django.shortcuts import get_object_or_404
        return get_object_or_404(User, username=self.kwargs["username"])

    def get_context_data(self, **kwargs):
        from books.models import Book
        context = super().get_context_data(**kwargs)
        user = self.get_object()
        context["listings"] = Book.objects.filter(
            seller=user, status="available"
        ).prefetch_related("images", "authors").order_by("-created_at")
        return context