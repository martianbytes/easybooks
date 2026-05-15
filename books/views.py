from django.views.generic import TemplateView, ListView, CreateView, DetailView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy
from django.shortcuts import render,get_object_or_404,redirect
from django.contrib import messages
from django.views import View
from .models import Book, Message, Transaction
from .forms import CheckoutForm
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


class CheckoutView(LoginRequiredMixin, View):
    
    login_url = 'accounts:login'

    def get(self, request, pk):
        book = get_object_or_404(Book, pk=pk, status='available')

       
        if book.seller == request.user:
            messages.error(request, "You cannot buy your own book.")
            return redirect('books:detail', pk=pk)

        
        initial_data = {
            'first_name': request.user.first_name,
            'last_name': request.user.last_name,
            'email': request.user.email,
            'phone': getattr(request.user.profile, 'phone', ''),
            'city': getattr(request.user.profile, 'city', ''),
            'district': getattr(request.user.profile, 'district', ''),
        }
        form = CheckoutForm(initial=initial_data)

        return render(request, 'books/checkout.html', {
            'book': book,
            'form': form,
        })

    def post(self, request, pk):
        book = get_object_or_404(Book, pk=pk, status='available')

        if book.seller == request.user:
            messages.error(request, "You cannot buy your own book.")
            return redirect('books:detail', pk=pk)

        form = CheckoutForm(request.POST)

        if form.is_valid():
            # Save the transaction to the db
            transaction = Transaction.objects.create(
                book=book,
                buyer=request.user,
                seller=book.seller,
                price=book.asking_price,
                status='pending',
            )

            
            book.status = 'reserved'
            book.save()

            # Go to confirmation page
            return redirect('books:order_confirmed', pk=transaction.pk)

       
        return render(request, 'books/checkout.html', {
            'book': book,
            'form': form,
        })


class OrderConfirmedView(LoginRequiredMixin, View):
  
    login_url = 'accounts:login'

    def get(self, request, pk):
        transaction = get_object_or_404(Transaction, pk=pk, buyer=request.user)
        return render(request, 'books/order_confirmed.html', {
            'transaction': transaction,
            'book': transaction.book,
        })


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