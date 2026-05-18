from django.db import models
from django.contrib.auth.models import User
from django.utils.text import slugify
from django.core.validators import MinValueValidator
from django.core.exceptions import ValidationError
from datetime import datetime
import uuid


# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# Authors
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
class Author(models.Model):
    name = models.CharField(max_length=255, unique=True)

    def __str__(self):
        return self.name


# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# BOOK MODEL
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
class Book(models.Model):
    """what things will the book possess"""

    CONDITION_CHOICES = [
        ("new", "New"),
        ("like_new", "Like New"),
        ("good", "Good"),
        ("fair", "Fair"),
        ("poor", "Poor"),
    ]

    CATEGORY_CHOICES = [
        ("fiction", "Fiction"),
        ("non_fiction", "Non-Fiction"),
        ("textbook", "Textbook"),
        ("science", "Science"),
        ("technology", "Technology"),
        ("history", "History"),
        ("biography", "Biography"),
        ("self_help", "Self Help"),
        ("business", "Business"),
        ("children", "Children"),
        ("comics", "Comics & Manga"),
        ("other", "Other"),
    ]

    LANGUAGE_CHOICES = [
        ("en", "English"),
        ("ne", "Nepali"),
        ("hi", "Hindi"),
        ("other", "Other"),
    ]

    STATUS_CHOICES = [
        ("available", "Available"),
        ("reserved", "Reserved"),
        ("sold", "Sold"),
    ]

    # =========Core Info===========
    title = models.CharField(max_length=255)
    slug = models.SlugField(max_length=300, unique=True, blank=True)
    subtitle = models.CharField(
        max_length=255, blank=True
    )  # Optional extra title line.

    authors = models.ManyToManyField(Author, related_name="books")

    publisher = models.CharField(max_length=255, blank=True)
    published_year = models.PositiveIntegerField(blank=True, null=True)
    edition = models.CharField(max_length=100, blank=True)

    isbn = models.CharField(max_length=13, blank=True, unique=True, null=True)

    language = models.CharField(max_length=10, choices=LANGUAGE_CHOICES, default="en")
    num_pages = models.IntegerField(blank=True, null=True)
    category = models.CharField(
        max_length=50, choices=CATEGORY_CHOICES, default="other"
    )

    # ======Condition==========================
    condition = models.CharField(max_length=20, choices=CONDITION_CHOICES)
    condition_notes = models.TextField(blank=True)
    description = models.TextField(blank=True)

    # ========Pricing===========================
    original_price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        blank=True,
        null=True,
        validators=[MinValueValidator(0)],
    )
    asking_price = models.DecimalField(
        max_digits=10, decimal_places=2, validators=[MinValueValidator(0)]
    )

    is_negotiable = models.BooleanField(default=True)

    # ========Seller=================================
    seller = models.ForeignKey(User, on_delete=models.CASCADE, related_name="listings")
    status = models.CharField(
        max_length=20, choices=STATUS_CHOICES, default="available"
    )

    # +++++++++++Location+++++++++++++++++++++++++++
    city = models.CharField(max_length=100, blank=True)

    # +++++++++++engagements+++++++++++++++++++++++++++
    views = models.PositiveIntegerField(default=0)

    # ++++++++++++Soft delete+++++++++++++++++++++++++
    is_active = models.BooleanField(default=True)

    # +++++++++++++++++Meta+++++++++++++++++++++
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["slug"]),
            models.Index(fields=["category"]),
            models.Index(fields=["status"]),
            models.Index(fields=["created_at"]),
            models.Index(fields=["title"]),
        ]

    # ------------- Validation -------------------------------
    def clean(self):
        if self.original_price and self.asking_price:
            if self.asking_price > self.original_price:
                raise ValidationError("Asking price cannot exceed original price.")

        if self.published_year:
            if self.published_year > datetime.now().year:
                raise ValidationError("Published year cannot be in the future")

    # -------------- SAVE -----------------------------------
    def save(self, *args, **kwargs):
        if not self.slug:
            base_slug = slugify(self.title)
            for _ in range(5):
                unique_id = uuid.uuid4().hex[:6]
                slug = f"{base_slug}-{unique_id}"
                if not Book.objects.filter(slug=slug).exists():
                    self.slug = slug
                    break
            else:
                raise Exception("Slug generation failed.")
        # Only run full_clean when update_fields is not specified
        # (i.e. not a targeted partial update like status change in checkout)
        if not kwargs.get("update_fields"):
            self.full_clean()
        super().save(*args, **kwargs)

    # ========================Helpers========================
    def __str__(self):
        return self.title

    def get_cover_image(self):
        images = self.images.all()  # type: ignore

        for img in images:
            if img.image_type == "cover":
                return img.image.url

        return images[0].image.url if images else None

    @property
    def cover_image(self):
        """Return cover image URL (used by templates as book.cover_image)."""
        return self.get_cover_image()

    def discount_percentage(self):
        if self.original_price and self.asking_price > 0:
            if self.asking_price >= self.original_price:
                return 0

            return round(
                ((self.original_price - self.asking_price) / self.original_price * 100)
            )

        return None


# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
#  Book Image Model
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
class BookImage(models.Model):

    IMAGE_TYPE_CHOICES = [
        ("cover", "Cover"),
        ("back", "Back Cover"),
        ("spine", "Spine"),
        ("condition", "Condition Photo"),
        ("other", "Other"),
    ]

    book = models.ForeignKey(Book, on_delete=models.CASCADE, related_name="images")
    image = models.ImageField(upload_to="book_images/")
    image_type = models.CharField(
        max_length=20, choices=IMAGE_TYPE_CHOICES, default="cover"
    )
    caption = models.CharField(max_length=255, blank=True)
    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["order"]
        constraints = [
            models.UniqueConstraint(
                fields=["book"],
                condition=models.Q(image_type="cover"),
                name="one_cover_per_book",
            )
        ]

    def save(self, *args, **kwargs):
        if not self.pk:  # Only for new instances
            max_order = BookImage.objects.filter(book=self.book).aggregate(
                models.Max("order")
            )["order__max"]
            self.order = (max_order or -1) + 1
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.image_type} image of {self.book.title}"


# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# Transaction
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
class Transaction(models.Model):
    STATUS_CHOICES = [
        ("pending", "Pending"),
        ("completed", "Completed"),
        ("cancelled", "Cancelled"),
    ]

    book = models.ForeignKey(Book, on_delete=models.CASCADE)
    buyer = models.ForeignKey(User, on_delete=models.CASCADE, related_name="purchases")
    seller = models.ForeignKey(User, on_delete=models.CASCADE, related_name="sales")

    price = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="pending")

    slug = models.SlugField(max_length=300, unique=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        if not self.slug:
            base_slug = slugify(f"{self.book.title}-{self.buyer.username}")
            for _ in range(5):
                unique_id = uuid.uuid4().hex[:6]
                slug = f"{base_slug}-{unique_id}"
                if not Transaction.objects.filter(slug=slug).exists():
                    self.slug = slug
                    break
            else:
                raise Exception("Slug generation failed.")
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.book.title} - {self.status}"


# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# Message
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
class Message(models.Model):
    buyer = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="sent_messages"
    )
    seller = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="received_messages"
    )
    book = models.ForeignKey(Book, on_delete=models.CASCADE, related_name="messages")
    message = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"Message from {self.buyer.username} to {self.seller.username} about {self.book.title}"


# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# Cart Item
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
class CartItem(models.Model):
    """
    Stores books that a user has added to their cart.
    One user cannot add the same book twice.
    """

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="cart_items")
    book = models.ForeignKey(Book, on_delete=models.CASCADE, related_name="carted_by")
    added_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["user", "book"], name="unique_cart_item")
        ]
        ordering = ["-added_at"]

    def __str__(self):
        return f"{self.user.username}'s cart → {self.book.title}"
