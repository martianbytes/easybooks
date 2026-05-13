from django.views.generic import TemplateView, ListView, CreateView, DetailView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy
from .models import Book, Message
from django.http import JsonResponse

class HomeView(TemplateView):
    template_name = 'home.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['featured_books'] = Book.objects.filter(status='available')[:4]
        context['bestselling_books'] = Book.objects.filter(status='available').order_by('-views')[:4]
        context['recommended_books'] = Book.objects.filter(status='available').order_by('-created_at')[:4]
        context['popular_genres'] = [
            {'id': cat[0], 'name': cat[1]} 
            for cat in Book.CATEGORY_CHOICES[:5]
        ]
        return context


class BrowseView(ListView):
    model = Book
    template_name = 'books/browse.html'
    context_object_name = 'books'
    paginate_by = 12

    def get_queryset(self):
        queryset = Book.objects.filter(status='available')
        
        # Filter by category (genre)
        category = self.request.GET.get('genre')
        if category:
            queryset = queryset.filter(category=category)
        
        # Filter by language
        language = self.request.GET.get('language')
        if language:
            queryset = queryset.filter(language=language)
        
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['genre_choices'] = Book.CATEGORY_CHOICES
        context['language_choices'] = Book.LANGUAGE_CHOICES
        context['selected_genre'] = self.request.GET.get('genre')
        context['selected_language'] = self.request.GET.get('language')
        return context


class SellView(LoginRequiredMixin, CreateView):
    model = Book
    template_name = 'books/sell.html'
    fields = ['title', 'subtitle', 'authors', 'publisher', 'published_year', 'edition', 'isbn', 'language', 'num_pages', 'category', 'condition']
    success_url = reverse_lazy('books:browse')
    login_url = 'login'

    def form_valid(self, form):
        form.instance.seller = self.request.user
        return super().form_valid(form)


class SubscribeView(CreateView):
    # Handle newsletter subscription
    def post(self, request):
        email = request.POST.get('email')
        # Add your newsletter logic here
        return JsonResponse({'status': 'success'})


class BookDetailView(DetailView):
    model = Book
    template_name = 'books/detail.html'
    context_object_name = 'book'


class CheckoutView(LoginRequiredMixin, DetailView):
    model = Book
    template_name = 'books/checkout.html'
    context_object_name = 'book'
    login_url = 'login'


class ContactSellerView(LoginRequiredMixin, CreateView):
    model = Message  # You'll need to create a Message model
    template_name = 'books/contact_seller.html'
    fields = ['message']
    success_url = reverse_lazy('books:browse')
    login_url = 'login'

    def form_valid(self, form):
        form.instance.buyer = self.request.user
        form.instance.book = Book.objects.get(pk=self.kwargs['pk'])
        form.instance.seller = form.instance.book.seller
        return super().form_valid(form)