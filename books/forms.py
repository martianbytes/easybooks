from django import forms
from django.forms import inlineformset_factory
from .models import Book, BookImage, Author


# ─────────────────────────────────────────────────────────────────────────────
# Author quick-add form (used via AJAX to create an author inline)
# ─────────────────────────────────────────────────────────────────────────────
class AuthorForm(forms.ModelForm):
    class Meta:
        model = Author
        fields = ["name"]
        widgets = {
            "name": forms.TextInput(
                attrs={"placeholder": "Author name", "autocomplete": "off"}
            ),
        }


# ─────────────────────────────────────────────────────────────────────────────
# Main Book form
# ─────────────────────────────────────────────────────────────────────────────
class BookForm(forms.ModelForm):

    class Meta:
        model = Book
        fields = [
            # Core info
            "title",
            "subtitle",
            "authors",
            "publisher",
            "published_year",
            "edition",
            "isbn",
            "language",
            "num_pages",
            "category",
            # Condition
            "condition",
            "condition_notes",
            "description",
            # Pricing
            "original_price",
            "asking_price",
            "is_negotiable",
            # Listing
            "status",
            "city",
            # NOTE: seller, slug, views, is_active, created_at, updated_at
            # are handled in the view, not exposed in this form.
        ]
        widgets = {
            # ── Core info ────────────────────────────────────────────
            "title": forms.TextInput(
                attrs={
                    "placeholder": "e.g. The Alchemist",
                    "autofocus": True,
                }
            ),
            "subtitle": forms.TextInput(
                attrs={
                    "placeholder": "Optional subtitle",
                }
            ),
            # authors: hidden – managed by the JS author-tag widget;
            # SelectMultiple keeps Django's validation working.
            "authors": forms.SelectMultiple(attrs={"size": 6}),
            "publisher": forms.TextInput(
                attrs={
                    "placeholder": "e.g. Penguin Books",
                }
            ),
            "published_year": forms.NumberInput(
                attrs={
                    "placeholder": "e.g. 2019",
                    "min": 1800,
                    "max": 2100,
                }
            ),
            "edition": forms.TextInput(
                attrs={
                    "placeholder": "e.g. 3rd",
                }
            ),
            "isbn": forms.TextInput(
                attrs={
                    "placeholder": "13-digit ISBN",
                    "maxlength": 13,
                }
            ),
            "num_pages": forms.NumberInput(
                attrs={
                    "placeholder": "e.g. 320",
                    "min": 1,
                }
            ),
            # Dropdowns
            "language": forms.Select(),
            "category": forms.Select(),
            # ── Condition ────────────────────────────────────────────
            # Hidden – driven by a visual card-picker in JS.
            "condition": forms.HiddenInput(),
            "condition_notes": forms.Textarea(
                attrs={
                    "rows": 3,
                    "placeholder": "e.g. Minor highlighting on pages 10–15, small stain on back cover",
                }
            ),
            "description": forms.Textarea(
                attrs={
                    "rows": 4,
                    "placeholder": "About the book, why you're selling, any extras included…",
                }
            ),
            # ── Pricing ──────────────────────────────────────────────
            "original_price": forms.NumberInput(
                attrs={
                    "placeholder": "e.g. 850",
                    "min": 0,
                    "step": "0.01",
                }
            ),
            "asking_price": forms.NumberInput(
                attrs={
                    "placeholder": "e.g. 400",
                    "min": 0,
                    "step": "0.01",
                }
            ),
            "is_negotiable": forms.CheckboxInput(),
            # ── Listing ───────────────────────────────────────────────
            # Hidden – driven by JS status picker.
            "status": forms.HiddenInput(),
            "city": forms.TextInput(
                attrs={
                    "placeholder": "e.g. Kathmandu",
                }
            ),
        }

    # ── Field-level tweaks ────────────────────────────────────────────────
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Default status to 'available' when not yet submitted
        if not self.data.get(self.add_prefix("status")):
            self.initial.setdefault("status", "available")

        # Required
        for f in (
            "title",
            "authors",
            "category",
            "language",
            "condition",
            "asking_price",
            "city",
        ):
            self.fields[f].required = True

        # Optional
        for f in (
            "subtitle",
            "publisher",
            "published_year",
            "edition",
            "num_pages",
            "isbn",
            "original_price",
            "condition_notes",
            "description",
        ):
            self.fields[f].required = False

        # is_negotiable defaults True (matches model); not required
        self.fields["is_negotiable"].required = False

        # status is required but has a default; hidden from user
        self.fields["status"].required = False

    # ── Cross-field validation ────────────────────────────────────────────
    def clean(self):
        cleaned = super().clean()
        original = cleaned.get("original_price")
        asking = cleaned.get("asking_price")

        if original and asking and asking > original:
            self.add_error(
                "asking_price", "Asking price cannot exceed the original price."
            )

        return cleaned


# ─────────────────────────────────────────────────────────────────────────────
# Book Image form
# ─────────────────────────────────────────────────────────────────────────────
class BookImageForm(forms.ModelForm):
    class Meta:
        model = BookImage
        fields = ["image", "image_type", "caption"]
        widgets = {
            "image": forms.FileInput(attrs={"accept": "image/*"}),
            "image_type": forms.Select(),
            "caption": forms.TextInput(attrs={"placeholder": "Caption (optional)"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["image"].required = False
        self.fields["caption"].required = False
        self.fields["image_type"].initial = "other"


# ─────────────────────────────────────────────────────────────────────────────
# Inline formset – up to 8 images, 3 extra blank slots
# ─────────────────────────────────────────────────────────────────────────────
BookImageFormSet = inlineformset_factory(
    Book,
    BookImage,
    form=BookImageForm,
    extra=3,
    max_num=8,
    can_delete=True,
)
