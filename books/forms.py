from django import forms
from .models import Book, BookImage

class BookForm(forms.ModelForm):
    cover_image = forms.ImageField(
        required=True,
        widget=forms.FileInput(attrs={'accept': 'image/*'}),
        help_text='Upload a high-quality cover image'
    )
    
    images = forms.FileField(
        required=False,
        widget=forms.ClearableFileInput(attrs={
            'multiple': True,
            'accept': 'image/*'
        }),
        help_text='Upload multiple images'
    )

    class Meta:
        model = Book
        fields = [
            'title', 'authors', 'subtitle', 'category', 'language', 'isbn',
            'publisher', 'published_year', 'edition', 'num_pages', 'condition',
            'condition_notes', 'description', 'original_price', 'asking_price',
            'is_negotiable', 'city'
        ]
        widgets = {
            'title': forms.TextInput(attrs={'placeholder': 'Enter book title'}),
            'authors': forms.CheckboxSelectMultiple(),
            'subtitle': forms.TextInput(attrs={'placeholder': 'Optional subtitle'}),
            'category': forms.Select(),
            'language': forms.Select(),
            'isbn': forms.TextInput(attrs={'placeholder': 'e.g., 9780134685991'}),
            'publisher': forms.TextInput(attrs={'placeholder': 'Publisher name'}),
            'published_year': forms.NumberInput(attrs={'placeholder': 'YYYY'}),
            'edition': forms.TextInput(attrs={'placeholder': 'e.g., 1st Edition'}),
            'num_pages': forms.NumberInput(attrs={'placeholder': 'Number of pages'}),
            'condition': forms.Select(),
            'condition_notes': forms.Textarea(attrs={
                'placeholder': 'Describe any damage or wear',
                'rows': 3
            }),
            'description': forms.Textarea(attrs={
                'placeholder': 'Write a brief description about the book',
                'rows': 4
            }),
            'original_price': forms.NumberInput(attrs={'placeholder': 'Original price'}),
            'asking_price': forms.NumberInput(attrs={'placeholder': 'Your asking price'}),
            'is_negotiable': forms.CheckboxInput(),
            'city': forms.TextInput(attrs={'placeholder': 'Your city'}),
        }