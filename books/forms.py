import re
from datetime import datetime
from django import forms
from django.forms import inlineformset_factory
from .models import Book, BookImage, Transaction, Author


# ─────────────────────────────────────────────────────────────────────────────
# Author quick-add form (used via plain POST to create an author inline)
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

# ── Individual field validation ───────────────────────────────────────

    def clean_title(self):
        """
        Validates the book title.
        - Strips extra spaces
        - Minimum 2 characters
        - Only allows letters, numbers, spaces and common punctuation
        """
        title = self.cleaned_data.get("title") or ""
        title = title.strip()

        # Check minimum length
        if len(title) < 2:
            raise forms.ValidationError(
                "Title must be at least 2 characters long."
            )

        # Check for invalid special characters
        # Allowed: letters, numbers, spaces, . , - & ' : ( ) + /
        if not re.match(r"^[a-zA-Z0-9\s.,\-&':()+/]+$", title):
            raise forms.ValidationError(
                "Title contains invalid characters. "
            )

        return title

    def clean_isbn(self):
        """
        Validates the ISBN number.
        - Optional field — skip if empty
        - Must be exactly 10 or 13 digits
        - Only numbers allowed (no dashes or spaces)
        """
        isbn = self.cleaned_data.get("isbn") or ""
        isbn = isbn.strip()

        # If empty, that's fine — ISBN is optional
        if not isbn:
            return isbn

        # Remove dashes and spaces in case user typed them
        isbn_clean = isbn.replace("-", "").replace(" ", "")

        # Must be only digits
        if not isbn_clean.isdigit():
            raise forms.ValidationError(
                "ISBN must contain numbers only. Remove any dashes or spaces."
            )

        # Must be exactly 10 or 13 digits
        if len(isbn_clean) not in [10, 13]:
            raise forms.ValidationError(
                f"ISBN must be exactly 10 or 13 digits. You entered {len(isbn_clean)} digits."
            )

        return isbn_clean  # return the cleaned version without dashes

    def clean_published_year(self):
        """
        Validates the published year.
        - Optional field — skip if empty
        - Cannot be before 1800
        - Cannot be in the future
        """
        year = self.cleaned_data.get("published_year")

        # If empty, that's fine — published year is optional
        if year is None:
            return year

        current_year = datetime.now().year

        if year < 1800:
            raise forms.ValidationError(
                "Published year cannot be before 1800."
            )

        if year > current_year:
            raise forms.ValidationError(
                f"Published year cannot be in the future. "
                f"Current year is {current_year}."
            )

        return year

    def clean_num_pages(self):
        """
        Validates number of pages.
        - Optional field — skip if empty
        - Minimum 1 page
        - Maximum 10,000 pages
        """
        num_pages = self.cleaned_data.get("num_pages")

        # If empty, that's fine — num_pages is optional
        if num_pages is None:
            return num_pages

        if num_pages < 1:
            raise forms.ValidationError(
                "Number of pages must be at least 1."
            )

        if num_pages > 10000:
            raise forms.ValidationError(
                "Number of pages cannot exceed 10,000."
            )

        return num_pages

    def clean_asking_price(self):
        """
        Validates the asking price.
        - Required field
        - Minimum Rs. 1
        - Maximum Rs. 50,000
        """
        asking_price = self.cleaned_data.get("asking_price")

        if asking_price is None:
            return asking_price

        if asking_price < 1:
            raise forms.ValidationError(
                "Asking price must be at least Rs. 1."
            )

        if asking_price > 50000:
            raise forms.ValidationError(
                "Asking price cannot exceed Rs. 50,000."
            )

        return asking_price

    def clean_original_price(self):
        """
        Validates the original price.
        - Optional field — skip if empty
        - Minimum Rs. 1
        - Maximum Rs. 100,000
        """
        original_price = self.cleaned_data.get("original_price")

        # If empty, that's fine — original price is optional
        if original_price is None:
            return original_price

        if original_price < 1:
            raise forms.ValidationError(
                "Original price must be at least Rs. 1."
            )

        if original_price > 100000:
            raise forms.ValidationError(
                "Original price cannot exceed Rs. 100,000."
            )

        return original_price

    def clean_city(self):
        """
        Validates the city name.
        - Required field
        - Letters, spaces, and hyphens only
        - Minimum 2 characters
        """
        city = self.cleaned_data.get("city") or ""
        city = city.strip()

        if len(city) < 2:
            raise forms.ValidationError(
                "City name must be at least 2 characters long."
            )

        if not re.match(r"^[a-zA-Z\s\-]+$", city):
            raise forms.ValidationError(
                "City name can only contain letters, spaces, and hyphens."
            )

        return city

    def clean_condition_notes(self):
        """
        Validates condition notes.
        - Optional field — skip if empty
        - Maximum 500 characters
        """
        notes = self.cleaned_data.get("condition_notes") or ""
        notes = notes.strip()

        if len(notes) > 500:
            raise forms.ValidationError(
                f"Condition notes cannot exceed 500 characters. "
                f"You have {len(notes)} characters."
            )

        return notes

    def clean_description(self):
        """
        Validates book description.
        - Optional field — skip if empty
        - Maximum 2000 characters
        """
        description = self.cleaned_data.get("description") or ""
        description = description.strip()

        if len(description) > 2000:
            raise forms.ValidationError(
                f"Description cannot exceed 2000 characters. "
                f"You have {len(description)} characters."
            )

        return description

   # ── Cross-field validation ────────────────────────────────────────────
    def clean(self):
        """
        Cross-field validation — checks fields against each other.
        This runs AFTER all individual clean_fieldname() methods.
        """
        cleaned = super().clean()
        original = cleaned.get("original_price")
        asking = cleaned.get("asking_price")

        # Check asking price is not more than original price
        if original and asking and asking > original:
            self.add_error(
                "asking_price",
                f"Asking price (Rs. {asking}) cannot be more than "
                f"original price (Rs. {original})."
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
        # image_type default is set per-slot via formset initial in the view


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


# ─────────────────────────────────────────────────────────────────────────────
# Checkout Form
# Collects delivery info from the buyer at checkout.
# ─────────────────────────────────────────────────────────────────────────────
class CheckoutForm(forms.Form):

    CITY_CHOICES = [
        ("", "Select your city"),
        ("kathmandu", "Kathmandu"),
        ("lalitpur", "Lalitpur"),
        ("bhaktapur", "Bhaktapur"),
        ("pokhara", "Pokhara"),
        ("chitwan", "Chitwan"),
        ("biratnagar", "Biratnagar"),
        ("birgunj", "Birgunj"),
        ("dharan", "Dharan"),
        ("butwal", "Butwal"),
        ("other", "Other"),
    ]

    PAYMENT_CHOICES = [
        ("cod", "Cash on Delivery"),
        ("esewa", "eSewa"),
        ("khalti", "Khalti"),
        ("bank", "Bank Transfer"),
    ]

    first_name = forms.CharField(
        max_length=100,
        widget=forms.TextInput(
            attrs={"class": "form-control", "placeholder": "Ram"}),
    )
    last_name = forms.CharField(
        max_length=100,
        widget=forms.TextInput(
            attrs={"class": "form-control", "placeholder": "Sharma"}
        ),
    )
    email = forms.EmailField(
        widget=forms.EmailInput(
            attrs={"class": "form-control", "placeholder": "ram@example.com"}
        )
    )
    phone = forms.CharField(
        max_length=20,
        widget=forms.TextInput(
            attrs={"class": "form-control", "placeholder": "+977 98XXXXXXXX"}
        ),
    )
    address = forms.CharField(
        max_length=255,
        widget=forms.TextInput(
            attrs={"class": "form-control",
                   "placeholder": "Street / Tole / Landmark"}
        ),
    )
    city = forms.ChoiceField(
        choices=CITY_CHOICES, widget=forms.Select(
            attrs={"class": "form-control"})
    )
    district = forms.CharField(
        max_length=100,
        widget=forms.TextInput(
            attrs={"class": "form-control", "placeholder": "e.g. Kathmandu"}
        ),
    )
    payment_method = forms.ChoiceField(
        choices=PAYMENT_CHOICES,
        widget=forms.RadioSelect(attrs={"class": "payment-radio"}),
    )
    # ── Individual field validation ───────────────────────────────────────

    def clean_first_name(self):
        """
        Validates first name.
        - Strip extra spaces
        - Minimum 2 characters
        - Letters, spaces and hyphens only
        - No numbers or symbols
        """
        first_name = self.cleaned_data.get("first_name") or ""
        first_name = first_name.strip()

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
        - Strip extra spaces
        - Minimum 2 characters
        - Letters, spaces and hyphens only
        """
        last_name = self.cleaned_data.get("last_name") or ""
        last_name = last_name.strip()

        if len(last_name) < 2:
            raise forms.ValidationError(
                "Last name must be at least 2 characters long."
            )

        if not re.match(r"^[a-zA-Z\s\-]+$", last_name):
            raise forms.ValidationError(
                "Last name can only contain letters, spaces, and hyphens."
            )

        return last_name

    def clean_phone(self):
        """
        Validates Nepal phone number.
        - Remove spaces and dashes user might type
        - Must start with 97 or 98 (Nepal mobile)
        - Must be exactly 10 digits
        
        Valid examples:
            9841234567   → valid
            9741234567   → valid
            +977 9841234567 → we strip +977 and validate the rest
        """
        phone = self.cleaned_data.get("phone") or ""
        phone = phone.strip()

        # Remove common formatting characters user might type
        phone = phone.replace(" ", "").replace("-", "").replace("+", "")

        # If user typed country code 977, remove it
        # e.g. 9779841234567 → 9841234567
        if phone.startswith("977") and len(phone) == 13:
            phone = phone[3:]

        # Must be only digits now
        if not phone.isdigit():
            raise forms.ValidationError(
                "Phone number must contain digits only."
            )

        # Must be exactly 10 digits
        if len(phone) != 10:
            raise forms.ValidationError(
                "Phone number must be exactly 10 digits. e.g. 9841234567"
            )

        # Must start with 97 or 98 (Nepal mobile numbers)
        if not (phone.startswith("97") or phone.startswith("98")):
            raise forms.ValidationError(
                "Please enter a valid Nepal mobile number "
                "starting with 97 or 98."
            )

        return phone

    def clean_address(self):
        """
        Validates delivery address.
        - Strip extra spaces
        - Minimum 5 characters
        - Should have some meaningful content
        """
        address = self.cleaned_data.get("address") or ""
        address = address.strip()

        if len(address) < 5:
            raise forms.ValidationError(
                "Please enter a complete address "
                "(at least 5 characters)."
            )

        return address

    def clean_district(self):
        """
        Validates district name.
        - Strip extra spaces
        - Minimum 2 characters
        - Letters, spaces and hyphens only
        """
        district = self.cleaned_data.get("district") or ""
        district = district.strip()

        if len(district) < 2:
            raise forms.ValidationError(
                "District name must be at least 2 characters long."
            )

        if not re.match(r"^[a-zA-Z\s\-]+$", district):
            raise forms.ValidationError(
                "District name can only contain letters, spaces, and hyphens."
            )

        return district