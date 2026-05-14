from django import forms
from django.forms import inlineformset_factory
from .models import Book, BookImage


class BookForm(forms.ModelForm):
    """Form for creating/editing books."""
    
    class Meta:
        model = Book
        fields = [
            'title', 'authors', 'subtitle', 'category', 'language', 'isbn',
            'publisher', 'published_year', 'edition', 'num_pages', 'condition',
            'condition_notes', 'description', 'original_price', 'asking_price',
            'is_negotiable', 'city'
        ]
        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter book title'
            }),
            'authors': forms.CheckboxSelectMultiple(attrs={'class': 'form-check-input'}),
            'subtitle': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Optional subtitle'
            }),
            'category': forms.Select(attrs={'class': 'form-control'}),
            'language': forms.Select(attrs={'class': 'form-control'}),
            'isbn': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'e.g., 9780134685991'
            }),
            'publisher': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Publisher name'
            }),
            'published_year': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': 'YYYY'
            }),
            'edition': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'e.g., 1st Edition'
            }),
            'num_pages': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': 'Number of pages'
            }),
            'condition': forms.Select(attrs={'class': 'form-control'}),
            'condition_notes': forms.Textarea(attrs={
                'class': 'form-control',
                'placeholder': 'Describe any damage or wear',
                'rows': 3
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'placeholder': 'Write a brief description about the book',
                'rows': 4
            }),
            'original_price': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': 'Original price',
                'step': '0.01'
            }),
            'asking_price': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': 'Your asking price'
            }),
            'is_negotiable': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'city': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Your city'
            }),
        }


class BookImageForm(forms.ModelForm):
    """Form for book images."""
    
    class Meta:
        model = BookImage
        fields = ['image', 'image_type', 'caption']
        widgets = {
            'image': forms.FileInput(attrs={
                'class': 'form-control',
                'accept': 'image/*'
            }),
            'image_type': forms.Select(attrs={'class': 'form-control'}),
            'caption': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Image caption (optional)'
            }),
        }


# Formset for multiple images
BookImageFormSet = inlineformset_factory(
    Book, 
    BookImage, 
    form=BookImageForm, 
    extra=3, 
    can_delete=True
)