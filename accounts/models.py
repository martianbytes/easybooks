from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator, MaxValueValidator
from django.db.models import Avg
from django.db.models.signals import post_save
from django.dispatch import receiver
from decimal import Decimal
import uuid


# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# Profile
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
class Profile(models.Model):
    """Extended user profile for marketplace buyers and sellers."""

    VERIFICATION_STATUS_CHOICES = [
        ("unverified", "Unverified"),
        ("verified", "Verified"),
        ("suspended", "Suspended"),
    ]

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="profile")

    # Profile Info
    avatar = models.ImageField(upload_to="avatars/%Y/%m", blank=True, null=True)
    bio = models.TextField(max_length=500, blank=True)
    phone = models.CharField(max_length=20, blank=True)

    # Location
    city = models.CharField(max_length=100, blank=True)
    district = models.CharField(max_length=100, blank=True)

    # Verification & Status
    is_email_verified = models.BooleanField(default=False)
    is_banned = models.BooleanField(default=False)
    verification_status = models.CharField(
        max_length=20, choices=VERIFICATION_STATUS_CHOICES, default="unverified"
    )

    # Seller Info
    is_seller = models.BooleanField(default=False)
    seller_rating = models.DecimalField(
        max_digits=3,
        decimal_places=2,
        default=Decimal("0.0"),
        validators=[MinValueValidator(0)],
    )
    total_sales = models.PositiveIntegerField(default=0)

    # Activity Tracking
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    last_active = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.user.username}'s profile"

    @property
    def full_name(self):
        """Return full name or username fallback."""
        return self.user.get_full_name() or self.user.username

    @property
    def average_rating(self):
        """Calculate average rating from seller reviews."""
        result = self.reviews_received.aggregate(Avg("rating"))["rating__avg"]  # type: ignore
        return round(result, 1) if result else None

    @property
    def total_listings(self):
        """Count active listings by user."""
        return self.user.listings.filter(is_active=True).count()  # type: ignore

    @property
    def total_purchases(self):
        """Count completed purchases by user."""
        return self.user.purchases.filter(status="completed").count()  # type: ignore

    @property
    def review_count(self):
        """Count total reviews received."""
        return self.reviews_received.count()  # type: ignore


@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    """Auto-create Profile when new User is created."""
    if created:
        Profile.objects.create(user=instance)


# @receiver(post_save, sender=User)
# def save_user_profile(sender, instance, **kwargs):
#     """Auto-save Profile when User is saved."""
#     instance.profile.save()

@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    """Auto-save Profile when User is saved."""
    if hasattr(instance, 'profile'):  
        instance.profile.save()
    if hasattr(instance, "profile"):
        instance.profile.save()


# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# Email Verification Token
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
class EmailVerificationToken(models.Model):
    """Token for email verification during signup."""

    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="email_tokens"
    )
    token = models.UUIDField(default=uuid.uuid4, editable=False)
    created_at = models.DateTimeField(auto_now_add=True)
    is_used = models.BooleanField(default=False)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"Email token for {self.user.username}"


# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# Saved Books (Wishlist)
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
class SavedBook(models.Model):
    """User's saved/wishlist books."""

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="saved_books")
    book = models.ForeignKey(
        "books.Book", on_delete=models.CASCADE, related_name="saved_by"
    )
    saved_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-saved_at"]
        constraints = [
            models.UniqueConstraint(fields=["user", "book"], name="unique_saved_book")
        ]

    def __str__(self):
        return f"{self.user.username} saved '{self.book.title}'"


# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# Seller Review
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
class SellerReview(models.Model):
    """Reviews for sellers after completed transactions."""

    reviewer = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="reviews_given"
    )
    seller = models.ForeignKey(
        Profile, on_delete=models.CASCADE, related_name="reviews_received"
    )
    transaction = models.OneToOneField(
        "books.Transaction", on_delete=models.CASCADE, related_name="review"
    )

    rating = models.PositiveSmallIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)]
    )
    comment = models.TextField(max_length=1000, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return (
            f"{self.reviewer.username} → {self.seller.user.username} ({self.rating}★)"
        )
