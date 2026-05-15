from django.contrib import admin
from .models import Author, Book, BookImage, Transaction


# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# Author Admin
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
@admin.register(Author)
class AuthorAdmin(admin.ModelAdmin):
    list_display = ["name"]
    search_fields = ["name"]


# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# Book Image Inline
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
class BookImageInline(admin.TabularInline):
    model = BookImage
    extra = 1
    fields = ["image", "image_type", "caption", "order"]


# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# Book Admin
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
@admin.register(Book)
class BookAdmin(admin.ModelAdmin):
    list_display = [
        "title",
        "seller",
        "asking_price",
        "condition",
        "status",
        "created_at",
    ]
    list_filter = ["status", "condition", "category", "language", "created_at"]
    search_fields = ["title", "isbn", "seller__username"]
    readonly_fields = ["slug", "views", "created_at", "updated_at"]
    inlines = [BookImageInline]

    fieldsets = (
        (
            "Core Information",
            {
                "fields": (
                    "title",
                    "slug",
                    "subtitle",
                    "authors",
                    "publisher",
                    "published_year",
                    "edition",
                    "isbn",
                )
            },
        ),
        ("Details", {"fields": ("language", "num_pages", "category", "description")}),
        ("Condition", {"fields": ("condition", "condition_notes")}),
        ("Pricing", {"fields": ("original_price", "asking_price", "is_negotiable")}),
        ("Listing", {"fields": ("seller", "status", "city", "is_active")}),
        (
            "Metadata",
            {"fields": ("views", "created_at", "updated_at"), "classes": ("collapse",)},
        ),
    )


# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# Transaction Admin
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    list_display = ["book", "buyer", "seller", "price", "status", "created_at"]
    list_filter = ["status", "created_at"]
    search_fields = ["book__title", "buyer__username", "seller__username"]
    readonly_fields = ["created_at"]
