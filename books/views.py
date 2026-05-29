from django.views.generic import TemplateView, ListView, CreateView, DetailView
from django.db.models import Sum
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy, reverse
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.views import View
from .models import Book, Message, Transaction, CartItem, MessageReply, Conversation, ChatMessage
from django.http import JsonResponse
from django.conf import settings
import base64
import binascii
import hashlib
import hmac
import io
import json
import uuid
import requests as http_requests

from typing import cast
import re
from django.contrib.auth.decorators import login_required
from django.core.files.uploadedfile import InMemoryUploadedFile
from django.db import transaction
from django.views.decorators.http import require_POST
from django.db.models import Q
from .forms import AuthorForm, BookForm, BookImageFormSet, CheckoutForm
from .models import Author, Book, Message

IMAGE_FORMSET_PREFIX = "images"
MAX_DATAURL_IMAGE_BYTES = 8 * 1024 * 1024  # 8 MB per reconstructed image

# ---------------------------------------------------------------------------
# eSewa helpers
# ---------------------------------------------------------------------------

def _esewa_build_signature(transaction_uuid, total_amount):
    message = (
        f"total_amount={total_amount},"
        f"transaction_uuid={transaction_uuid},"
        f"product_code={settings.ESEWA_PRODUCT_CODE}"
    )
    raw = hmac.new(
        settings.ESEWA_SECRET_KEY.encode(),
        message.encode(),
        hashlib.sha256,
    ).digest()
    return base64.b64encode(raw).decode()


def _esewa_redirect(request, primary_transaction, override_amount=None, is_cart=False):
    total_amount = str(override_amount if override_amount is not None else primary_transaction.price)
    transaction_uuid = primary_transaction.slug

    signature = _esewa_build_signature(transaction_uuid, total_amount)

    if is_cart:
        success_url = request.build_absolute_uri(reverse('books:esewa_success')) + "?cart=1"
        failure_url = request.build_absolute_uri(reverse('books:esewa_failure')) + "?cart=1"
    else:
        success_url = request.build_absolute_uri(reverse('books:esewa_success')) + f"?txn={primary_transaction.slug}"
        failure_url = request.build_absolute_uri(reverse('books:esewa_failure')) + f"?txn={primary_transaction.slug}"

    context = {
        'esewa_url': settings.ESEWA_PAYMENT_URL,
        'amount': total_amount,
        'tax_amount': '0',
        'total_amount': total_amount,
        'transaction_uuid': transaction_uuid,
        'product_code': settings.ESEWA_PRODUCT_CODE,
        'product_service_charge': '0',
        'product_delivery_charge': '0',
        'success_url': success_url,
        'failure_url': failure_url,
        'signature': signature,
        'signed_field_names': 'total_amount,transaction_uuid,product_code',
    }
    return render(request, 'books/esewa_redirect.html', context)


def _esewa_verify(transaction_uuid, total_amount):
    try:
        url = (
            f"{settings.ESEWA_VERIFY_URL}"
            f"?product_code={settings.ESEWA_PRODUCT_CODE}"
            f"&transaction_uuid={transaction_uuid}"
            f"&total_amount={total_amount}"
        )
        resp = http_requests.get(url, timeout=10)
        data = resp.json()
        return data.get("status") == "COMPLETE"
    except Exception:
        return False


class EsewaSuccessView(LoginRequiredMixin, View):
    login_url = 'accounts:login'

    def get(self, request):
        encoded_data = request.GET.get('data', '')
        is_cart = request.GET.get('cart') == '1'

        if not encoded_data:
            messages.error(request, "Invalid payment response from eSewa.")
            return redirect('books:browse')

        try:
            decoded = base64.b64decode(encoded_data).decode()
            payload = json.loads(decoded)
        except Exception:
            messages.error(request, "Could not decode eSewa response.")
            return redirect('books:browse')

        transaction_uuid = payload.get('transaction_uuid', '')
        total_amount = payload.get('total_amount', '0').replace(',', '')
        ref_id = payload.get('transaction_code', '')

        verified = _esewa_verify(transaction_uuid, total_amount)

        if not verified:
            Transaction.objects.filter(slug=transaction_uuid).update(status='cancelled')
            messages.error(request, "eSewa payment verification failed. Order cancelled.")
            return redirect('books:browse')

        if is_cart:
            slugs = request.session.pop('cart_order_slugs', [transaction_uuid])
            Transaction.objects.filter(slug__in=slugs).update(
                status='completed', esewa_ref_id=ref_id
            )
            return redirect('books:cart_order_confirmed_success')
        if not is_cart:
            t = get_object_or_404(Transaction, slug=transaction_uuid, buyer=request.user)
            t.status = 'completed'
            t.esewa_ref_id = ref_id
            t.payment_method = 'esewa'
            t.book.status = 'sold'
            t.book.save(update_fields=['status'])
            t.save(update_fields=['status', 'esewa_ref_id', 'payment_method'])
            return redirect('books:order_confirmed', order_slug=t.slug)


class EsewaFailureView(LoginRequiredMixin, View):
    login_url = 'accounts:login'

    def get(self, request):
        is_cart = request.GET.get('cart') == '1'
        txn_slug = request.GET.get('txn', '')

        if txn_slug:
            t = Transaction.objects.filter(slug=txn_slug, buyer=request.user).first()
            if t:
                t.status = 'cancelled'
                t.save(update_fields=['status'])
                t.book.status = 'available'
                t.book.save(update_fields=['status'])

        if is_cart:
            slugs = request.session.pop('cart_order_slugs', [])
            if slugs:
                txns = Transaction.objects.filter(slug__in=slugs, buyer=request.user)
                for txn in txns:
                    txn.book.status = 'available'
                    txn.book.save(update_fields=['status'])
                txns.update(status='cancelled')

        messages.error(request, "Payment was cancelled or failed. Please try again.")
        return redirect('books:cart' if is_cart else 'books:browse')


class CartOrderConfirmedSuccessView(LoginRequiredMixin, View):
    login_url = 'accounts:login'

    def get(self, request):
        slugs = request.session.pop('cart_order_slugs', [])
        if not slugs:
            transactions = Transaction.objects.filter(
                buyer=request.user, status='completed'
            ).order_by('-created_at')[:5]
        else:
            transactions = Transaction.objects.filter(
                slug__in=slugs, buyer=request.user
            ).select_related('book', 'book__seller')

        total = sum(t.price for t in transactions)
        return render(request, 'books/cart_order_confirmed.html', {
            'transactions': transactions,
            'total': total,
        })


class HomeView(TemplateView):
    template_name = "home.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["featured_books"] = Book.objects.filter(status="available")[:4]
        context["bestselling_books"] = Book.objects.filter(status="available").order_by(
            "-views"
        )[:4]
        context["recommended_books"] = Book.objects.filter(status="available").order_by(
            "-created_at"
        )[:4]
        context["popular_genres"] = [
            {"id": cat[0], "name": cat[1]} for cat in Book.CATEGORY_CHOICES[:5]
        ]
        return context


class BrowseView(ListView):
    model = Book
    template_name = "books/browse.html"
    context_object_name = "books"
    paginate_by = 12

    def get_queryset(self):
        queryset = Book.objects.filter(status="available")

        q = self.request.GET.get("q", "").strip()
        if q:
            queryset = queryset.filter(
                Q(title__icontains=q) |
                Q(authors__name__icontains=q) |
                Q(isbn__icontains=q)
            ).distinct()

        genre = self.request.GET.get("genre")
        if genre:
            queryset = queryset.filter(category=genre)

        language = self.request.GET.get("language")
        if language:
            queryset = queryset.filter(language=language)

        conditions = self.request.GET.getlist("condition")
        if conditions:
            queryset = queryset.filter(condition__in=conditions)

        min_price = self.request.GET.get("min_price")
        if min_price:
            try:
                queryset = queryset.filter(asking_price__gte=min_price)
            except ValueError:
                pass

        max_price = self.request.GET.get("max_price")
        if max_price:
            try:
                queryset = queryset.filter(asking_price__lte=max_price)
            except ValueError:
                pass

        sort = self.request.GET.get("sort", "newest")
        if sort == "price-low-to-high":
            queryset = queryset.order_by("asking_price")
        elif sort == "price-high-to-low":
            queryset = queryset.order_by("-asking_price")
        elif sort == "popular":
            queryset = queryset.order_by("-views")
        else:
            queryset = queryset.order_by("-created_at")

        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["genre_choices"] = Book.CATEGORY_CHOICES
        context["language_choices"] = Book.LANGUAGE_CHOICES
        context["condition_choices"] = Book.CONDITION_CHOICES
        context["selected_genre"] = self.request.GET.get("genre", "")
        context["selected_language"] = self.request.GET.get("language", "")
        context["selected_conditions"] = self.request.GET.getlist("condition")
        context["search_query"] = self.request.GET.get("q", "")
        context["min_price"] = self.request.GET.get("min_price", "")
        context["max_price"] = self.request.GET.get("max_price", "")
        context["selected_sort"] = self.request.GET.get("sort", "newest")
        return context


class SubscribeView(CreateView):
    def post(self, request):
        email = request.POST.get("email")
        return JsonResponse({"status": "success"})


class BookDetailView(DetailView):
    model = Book
    template_name = "books/detail.html"
    context_object_name = "book"
    slug_field = "slug"
    slug_url_kwarg = "slug"

    def get_object(self) -> Book:
        return cast(Book, super().get_object())

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        book = self.get_object()
        context["related_books"] = (
            Book.objects
            .filter(category=book.category, status="available")
            .exclude(pk=book.pk)
            .select_related("seller")
            [:4]
        )
        return context


class CheckoutView(LoginRequiredMixin, View):

    login_url = 'accounts:login'

    def get(self, request, seller, slug):
        book = get_object_or_404(Book, slug=slug, status='available')

        if book.seller == request.user:
            messages.error(request, "You cannot buy your own book.")
            return redirect('books:detail', seller=book.seller.username, slug=slug)

        return render(request, 'books/checkout.html', {
            'book': book,
        })

    def post(self, request, seller, slug):
        book = get_object_or_404(Book, slug=slug, status='available')

        if book.seller == request.user:
            messages.error(request, "You cannot buy your own book.")
            return redirect('books:detail', seller=book.seller.username, slug=slug)

        t = Transaction.objects.create(
            book=book,
            buyer=request.user,
            seller=book.seller,
            price=book.asking_price,
            status='order_request',
        )

        book.status = 'reserved'
        book.save(update_fields=['status'])

        return redirect('books:order_confirmed', order_slug=t.slug)


class OrderConfirmedView(LoginRequiredMixin, View):

    login_url = 'accounts:login'

    def get(self, request, order_slug):
        order = get_object_or_404(Transaction, slug=order_slug, buyer=request.user)
        return render(request, 'books/order_confirmed.html', {
            'transaction': order,
            'book': order.book,
        })


class ContactSellerView(LoginRequiredMixin, CreateView):
    model = Message
    template_name = "books/contact_seller.html"
    fields = ["message"]
    login_url = "accounts:login"

    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        form.fields['message'].widget.attrs.update({
            'class': 'pdb-edit-form-textarea',
            'rows': 6,
            'placeholder': 'Hi, I\'m interested in this book. Is it still available?',
        })
        return form

    def dispatch(self, request, *args, **kwargs):
        self.book = get_object_or_404(Book, slug=self.kwargs["slug"])
        if request.user.is_authenticated and request.user == self.book.seller:
            return redirect("books:detail", seller=self.book.seller.username, slug=self.book.slug)
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["book"] = self.book
        return ctx

    def form_valid(self, form):
        form.instance.buyer = self.request.user
        form.instance.book = self.book
        form.instance.seller = self.book.seller
        messages.success(self.request, f"Message sent to {self.book.seller.username}!")
        response = super().form_valid(form)
        return response

    def get_success_url(self):
        return reverse("books:detail", kwargs={
            "seller": self.book.seller.username,
            "slug": self.book.slug,
        })


class AuthorCreateView(LoginRequiredMixin, View):
    login_url = "accounts:login"

    def post(self, request, *args, **kwargs):
        name = request.POST.get("new_author_name", "").strip()

        if not name:
            return JsonResponse({"ok": False, "error": "Author name is required."}, status=400)

        if len(name) < 2:
            return JsonResponse({"ok": False, "error": "Author name is too short."}, status=400)

        if not re.search(r"[a-zA-Z]", name):
            return JsonResponse({"ok": False, "error": "Author name must contain at least one letter."}, status=400)

        if not re.match(r"^[a-zA-Z0-9\s\.\-\'\,]+$", name):
            return JsonResponse({"ok": False, "error": "Author name contains invalid characters."}, status=400)

        author, created = Author.objects.get_or_create(name=name)
        return JsonResponse({"ok": True, "id": author.pk, "name": author.name, "created": created})

    def get(self, request, *args, **kwargs):
        return redirect("books:sell")


class BookUpsertView(LoginRequiredMixin, View):
    template_name = "books/sell.html"
    login_url = "accounts:login"

    def get_book(self):
        return None

    def get(self, request, *args, **kwargs):
        instance = self.get_book()
        editing = instance is not None
        book_form = BookForm(instance=instance)
        image_forms = BookImageFormSet(
            instance=instance,
            prefix=IMAGE_FORMSET_PREFIX,
            initial=[{"image_type": "cover"}, {"image_type": "condition"}, {"image_type": "condition"}],
        )

        try:
            preselected_author_id = int(request.GET.get("author_added", 0))
        except (ValueError, TypeError):
            preselected_author_id = 0

        return render(
            request,
            self.template_name,
            _sell_context(
                book_form=book_form,
                image_forms=image_forms,
                image_data_urls={},
                editing=editing,
                book=instance,
                preselected_author_id=preselected_author_id,
                author_error=request.GET.get("author_error", ""),
            ),
        )

    def post(self, request, *args, **kwargs):
        instance = self.get_book()
        editing = instance is not None

        book_form = BookForm(request.POST, instance=instance)
        merged_files = _merged_image_files_from_dataurls(
            post_data=request.POST,
            files_data=request.FILES,
            prefix=IMAGE_FORMSET_PREFIX,
        )
        image_forms = BookImageFormSet(
            request.POST,
            merged_files,
            instance=instance,
            prefix=IMAGE_FORMSET_PREFIX,
        )

        if book_form.is_valid() and image_forms.is_valid():
            # Check that a cover image is provided (new listing or existing cover kept)
            cover_provided = False
            if editing:
                # Editing: cover is OK if existing cover image not being deleted
                from .models import BookImage
                existing_cover = BookImage.objects.filter(
                    book=instance, image_type='cover'
                ).exists()
                if existing_cover:
                    # Check it's not being marked for deletion
                    for form in image_forms:
                        if (form.instance.pk and
                                form.instance.image_type == 'cover' and
                                form.cleaned_data.get('DELETE')):
                            existing_cover = False
                            break
                cover_provided = existing_cover

            # Also check new upload in slot 0 (first form = cover slot)
            if not cover_provided:
                first_form = image_forms.forms[0] if image_forms.forms else None
                if first_form:
                    has_file = bool(first_form.cleaned_data.get('image'))
                    # Also check data URL submitted for slot 0
                    dataurl_key = f"{IMAGE_FORMSET_PREFIX}-0-image_dataurl"
                    has_dataurl = bool(request.POST.get(dataurl_key, '').startswith('data:image/'))
                    cover_provided = has_file or has_dataurl

            if not cover_provided:
                from django.forms.utils import ErrorList
                # Inject error into the first image form so it renders inline
                first_form = image_forms.forms[0] if image_forms.forms else None
                cover_error = "A cover image is required."
                if first_form:
                    first_form.add_error('image', cover_error)
                return render(
                    request,
                    self.template_name,
                    _sell_context(
                        book_form=book_form,
                        image_forms=image_forms,
                        image_data_urls=_collect_dataurl_values(request.POST),
                        editing=editing,
                        book=instance,
                        preselected_author_id=0,
                        author_error="",
                        cover_error=cover_error,
                    ),
                )

            with transaction.atomic():
                book = book_form.save(commit=False)
                if not editing:
                    book.seller = request.user
                book.save()
                book_form.save_m2m()

                image_forms.instance = book
                image_forms.save()

            return redirect("books:detail", seller=book.seller.username, slug=book.slug)

        return render(
            request,
            self.template_name,
            _sell_context(
                book_form=book_form,
                image_forms=image_forms,
                image_data_urls=_collect_dataurl_values(request.POST),
                editing=editing,
                book=instance,
                preselected_author_id=0,
                author_error="",
            ),
        )


def _sell_context(*, book_form, image_forms, image_data_urls, editing, book,
                  preselected_author_id=0, author_error="", cover_error=""):
    return {
        "book_form": book_form,
        "image_formset": image_forms,
        "image_data_urls": json.dumps(image_data_urls),
        "all_authors": list(Author.objects.order_by("name").values("id", "name")),
        "editing": editing,
        "book": book,
        "preselected_author_id": preselected_author_id,
        "author_error": author_error,
        "cover_error": cover_error,
    }


def _merged_image_files_from_dataurls(post_data, files_data, prefix="images"):
    files = files_data.copy()
    total = int(post_data.get(f"{prefix}-TOTAL_FORMS", 0) or 0)

    for i in range(total):
        file_field = f"{prefix}-{i}-image"
        data_field = f"{prefix}-{i}-image_dataurl"

        if file_field in files:
            continue

        data_url = post_data.get(data_field, "")
        if not data_url.startswith("data:image/"):
            continue

        uploaded = _inmemory_file_from_dataurl(
            data_url=data_url,
            field_name="image",
            max_bytes=MAX_DATAURL_IMAGE_BYTES,
        )
        if uploaded:
            files[file_field] = uploaded

    return files


def _inmemory_file_from_dataurl(*, data_url, field_name, max_bytes):
    try:
        header, encoded = data_url.split(",", 1)
        mime = header.split(":", 1)[1].split(";", 1)[0].strip().lower()
        if not mime.startswith("image/"):
            return None

        raw = base64.b64decode(encoded, validate=True)
        if not raw or len(raw) > max_bytes:
            return None

        ext = mime.split("/", 1)[1].split("+", 1)[0] or "jpg"
        buf = io.BytesIO(raw)
        buf.seek(0)

        return InMemoryUploadedFile(
            file=buf,
            field_name=field_name,
            name=f"{uuid.uuid4().hex}.{ext}",
            content_type=mime,
            size=len(raw),
            charset=None,
        )
    except (ValueError, IndexError, binascii.Error):
        return None


def _collect_dataurl_values(post_data):
    return {k: v for k, v in post_data.items() if k.endswith("_dataurl")}


class BookCreateView(BookUpsertView):
    def get_book(self):
        return None


class BookEditView(BookUpsertView):
    def get_book(self):
        return get_object_or_404(Book, slug=self.kwargs["slug"], seller=self.request.user)


class BookDeleteView(LoginRequiredMixin, View):
    login_url = "accounts:login"

    def post(self, request, seller, slug):
        book = get_object_or_404(Book, slug=slug, seller=request.user)
        book.delete()
        messages.success(request, "Your listing has been deleted.")
        return redirect("books:browse")


class CartView(LoginRequiredMixin, View):
    login_url = 'accounts:login'

    def get(self, request):
        cart_items = CartItem.objects.filter(user=request.user).select_related('book')
        total = sum(item.book.asking_price for item in cart_items)
        return render(request, 'books/cart.html', {
            'cart_items': cart_items,
            'total': total,
        })


class AddToCartView(LoginRequiredMixin, View):
    login_url = 'accounts:login'

    def post(self, request, seller, slug):
        book = get_object_or_404(Book, slug=slug, status='available')

        if book.seller == request.user:
            messages.error(request, "You cannot add your own book to cart.")
            return redirect('books:detail', seller=seller, slug=slug)

        cart_item, created = CartItem.objects.get_or_create(
            user=request.user,
            book=book,
        )

        if created:
            messages.success(request, f'"{book.title}" added to your cart!')
        else:
            messages.info(request, f'"{book.title}" is already in your cart.')

        return redirect('books:detail', seller=seller, slug=slug)


class RemoveFromCartView(LoginRequiredMixin, View):
    login_url = 'accounts:login'

    def post(self, request, slug):
        book = get_object_or_404(Book, slug=slug)
        CartItem.objects.filter(user=request.user, book=book).delete()
        messages.success(request, f'"{book.title}" removed from cart.')
        return redirect('books:cart')


class CartCheckoutView(LoginRequiredMixin, View):
    login_url = 'accounts:login'

    def get(self, request):
        cart_items = CartItem.objects.filter(user=request.user).select_related('book')

        if not cart_items.exists():
            messages.info(request, "Your cart is empty.")
            return redirect('books:cart')

        available = [item for item in cart_items if item.book.status == 'available' and item.book.seller != request.user]
        unavailable = [item for item in cart_items if item.book.status != 'available' or item.book.seller == request.user]

        if not available:
            messages.error(request, "None of the books in your cart are available for purchase.")
            return redirect('books:cart')

        total = sum(item.book.asking_price for item in available)

        return render(request, 'books/cart_checkout.html', {
            'available_items': available,
            'unavailable_items': unavailable,
            'total': total,
        })

    def post(self, request):
        cart_items = CartItem.objects.filter(user=request.user).select_related('book')

        if not cart_items.exists():
            return redirect('books:cart')

        available = [item for item in cart_items if item.book.status == 'available' and item.book.seller != request.user]

        if not available:
            messages.error(request, "None of the books in your cart are available.")
            return redirect('books:cart')

        with transaction.atomic():
            for item in available:
                Transaction.objects.create(
                    book=item.book,
                    buyer=request.user,
                    seller=item.book.seller,
                    price=item.book.asking_price,
                    status='order_request',
                )
                item.book.status = 'reserved'
                item.book.save(update_fields=['status'])

            CartItem.objects.filter(
                user=request.user,
                book__in=[item.book for item in available]
            ).delete()

        messages.success(request, f"Your order request for {len(available)} book(s) has been sent to the seller(s)!")
        return redirect('books:orders')


class CartOrderConfirmedView(LoginRequiredMixin, View):
    login_url = 'accounts:login'

    def get(self, request):
        slugs = request.session.pop('cart_order_slugs', [])
        if not slugs:
            return redirect('books:browse')

        transactions = Transaction.objects.filter(
            slug__in=slugs,
            buyer=request.user
        ).select_related('book', 'book__seller')

        total = sum(t.price for t in transactions)

        return render(request, 'books/cart_order_confirmed.html', {
            'transactions': transactions,
            'total': total,
        })


class SalesView(LoginRequiredMixin, View):
    login_url = 'accounts:login'

    def get(self, request):
        sales = Transaction.objects.filter(
            seller=request.user
        ).select_related('book', 'buyer').order_by('-created_at')

        status_filter = request.GET.get('status', '')
        if status_filter in ('order_request', 'pending', 'completed', 'cancelled'):
            sales = sales.filter(status=status_filter)

        total_earned = Transaction.objects.filter(
            seller=request.user, status='completed'
        ).aggregate(total=Sum('price'))['total'] or 0
        total_earned = round(float(total_earned), 2)

        # Attach the related conversation so the template can link directly to that thread
        sales = list(sales)
        for sale in sales:
            setattr(sale, 'related_conversation', Conversation.objects.filter(
                buyer=sale.buyer, book=sale.book, seller=request.user
            ).first())

        return render(request, 'books/sales.html', {
            'sales': sales,
            'status_filter': status_filter,
            'total_earned': total_earned,
        })


class BestSellersView(View):
    def get(self, request):
        return redirect(reverse('books:browse') + '?sort=popular')


class GenresView(TemplateView):
    template_name = 'books/genres.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        genres = []
        for slug, label in Book.CATEGORY_CHOICES:
            count = Book.objects.filter(category=slug, status='available').count()
            genres.append({'slug': slug, 'label': label, 'count': count})
        context['genres'] = genres
        return context


class AuthorsView(ListView):
    template_name = 'books/authors.html'
    context_object_name = 'authors'

    def get_queryset(self):
        from .models import Author
        from django.db.models import Count, Q
        return Author.objects.annotate(
            book_count=Count('books', filter=Q(books__status='available'))
        ).filter(book_count__gt=0).order_by('name')


class WishlistView(LoginRequiredMixin, View):
    login_url = 'accounts:login'

    def get(self, request):
        from accounts.models import SavedBook
        saved = SavedBook.objects.filter(user=request.user).select_related('book', 'book__seller')
        return render(request, 'books/wishlist.html', {'saved': saved})


class OrdersView(LoginRequiredMixin, View):
    login_url = 'accounts:login'

    def get(self, request):
        status_filter = request.GET.get('status', '')
        orders = list(Transaction.objects.filter(buyer=request.user).select_related('book', 'seller', 'book__seller').order_by('-created_at'))
        if status_filter in ('order_request', 'pending', 'completed', 'cancelled'):
            orders = [o for o in orders if o.status == status_filter]

        # Attach related conversation to each order
        for order in orders:
            setattr(order, 'related_conversation', Conversation.objects.filter(
                buyer=request.user, book=order.book, seller=order.seller
            ).first())

        return render(request, 'books/orders.html', {
            'orders': orders,
            'status_filter': status_filter,
        })


class CompleteOrderView(LoginRequiredMixin, View):
    """Buyer marks an order as completed after receiving the book."""
    login_url = 'accounts:login'

    def post(self, request, order_slug):
        order = get_object_or_404(Transaction, slug=order_slug, buyer=request.user)

        if order.status not in ('order_request', 'pending'):
            messages.error(request, "This order cannot be completed.")
            return redirect('books:orders')

        method = request.POST.get('payment_method', '')
        remarks = request.POST.get('payment_remarks', '').strip()

        if method == 'esewa':
            order.status = 'pending'
            order.payment_method = 'esewa'
            order.save(update_fields=['status', 'payment_method'])
            return _esewa_redirect(request, order)

        elif method == 'other':
            order.status = 'completed'
            order.payment_method = 'other'
            order.payment_remarks = remarks
            order.book.status = 'sold'
            order.book.save(update_fields=['status'])
            order.save(update_fields=['status', 'payment_method', 'payment_remarks'])
            messages.success(request, "Order marked as completed. Thank you!")
            return redirect('books:orders')

        messages.error(request, "Please select a payment method.")
        return redirect('books:orders')


class SellerCompleteOrderView(LoginRequiredMixin, View):
    """Seller can mark an order complete if buyer hasn't done it yet."""
    login_url = 'accounts:login'

    def post(self, request, order_slug):
        order = get_object_or_404(Transaction, slug=order_slug, seller=request.user)

        if order.status not in ('order_request', 'pending'):
            messages.error(request, "This order cannot be completed.")
            return redirect('books:sales')

        remarks = request.POST.get('payment_remarks', '').strip()
        order.status = 'completed'
        order.payment_method = 'other'
        order.payment_remarks = remarks or 'Completed by seller'
        order.book.status = 'sold'
        order.book.save(update_fields=['status'])
        order.save(update_fields=['status', 'payment_method', 'payment_remarks'])
        messages.success(request, f"Order for \"{order.book.title}\" marked as completed.")
        return redirect('books:sales')


class CancelOrderView(LoginRequiredMixin, View):
    """Either buyer or seller can cancel an order_request/pending order."""
    login_url = 'accounts:login'

    def post(self, request, order_slug):
        # Allow both buyer and seller to cancel
        order = Transaction.objects.filter(slug=order_slug).filter(
            Q(buyer=request.user) | Q(seller=request.user)
        ).first()

        if not order:
            messages.error(request, "Order not found.")
            return redirect('books:orders')

        if order.status not in ('order_request', 'pending'):
            messages.error(request, "This order cannot be cancelled.")
        else:
            order.status = 'cancelled'
            order.book.status = 'available'
            order.book.save(update_fields=['status'])
            order.save(update_fields=['status'])
            messages.success(request, f"Order for \"{order.book.title}\" has been cancelled.")

        # Redirect back to whichever page they came from
        if order.seller == request.user and order.buyer != request.user:
            return redirect('books:sales')
        return redirect('books:orders')


class AboutView(TemplateView):
    template_name = 'books/about.html'


class ContactView(TemplateView):
    template_name = 'books/contact.html'


class BlogView(TemplateView):
    template_name = 'books/blog.html'


# ─────────────────────────────────────────────────────────────────
# Messenger  (new system)
# ─────────────────────────────────────────────────────────────────

class MessagesInboxView(LoginRequiredMixin, View):
    """
    Renders the messenger shell.
    All conversations where the current user is buyer OR seller,
    sorted by most recent message.  An optional ?conv=<pk> query
    param tells the template which conversation to open on load.
    """
    login_url = 'accounts:login'

    def get(self, request):
        user = request.user
        conversations = (
            Conversation.objects
            .filter(Q(buyer=user) | Q(seller=user))
            .select_related('buyer', 'seller', 'book')
            .order_by('-last_message_at')
        )

        # Total unread across all threads
        total_unread = sum(c.unread_count_for(user) for c in conversations)

        active_conv_pk = request.GET.get('conv')

        return render(request, 'books/messages_inbox.html', {
            'conversations': conversations,
            'total_unread': total_unread,
            'active_conv_pk': active_conv_pk,
        })


class ConversationMessagesView(LoginRequiredMixin, View):
    """
    AJAX — returns the full message list for a conversation as JSON,
    and marks all incoming messages as read.
    """
    login_url = 'accounts:login'

    def get(self, request, pk):
        conv = get_object_or_404(Conversation, pk=pk)
        user = request.user

        if user not in (conv.buyer, conv.seller):
            return JsonResponse({'error': 'Forbidden'}, status=403)

        # Mark unread messages (sent by the other person) as read
        ChatMessage.objects.filter(conversation=conv, is_read=False).exclude(sender=user).update(is_read=True)

        msgs = ChatMessage.objects.filter(conversation=conv).select_related('sender', 'book', 'book__seller').order_by('created_at')
        data = [
            {
                'id': m.pk,
                'sender': m.sender.username,
                'body': m.body,
                'is_self': m.sender == user,
                'created_at': m.created_at.strftime('%b %d · %I:%M %p'),
                'book_title': m.book.title if m.book else None,
                'book_url': (
                    reverse('books:detail', kwargs={
                        'seller': m.book.seller.username,
                        'slug': m.book.slug,
                    }) if m.book else None
                ),
            }
            for m in msgs
        ]

        other = conv.other_participant(user)
        return JsonResponse({
            'ok': True,
            'messages': data,
            'other_username': other.username,
        })


class SendChatMessageView(LoginRequiredMixin, View):
    """
    AJAX POST — appends a ChatMessage to an existing conversation.
    """
    login_url = 'accounts:login'

    def post(self, request, pk):
        conv = get_object_or_404(Conversation, pk=pk)
        user = request.user

        if user not in (conv.buyer, conv.seller):
            return JsonResponse({'error': 'Forbidden'}, status=403)

        body = request.POST.get('body', '').strip()
        if not body:
            return JsonResponse({'error': 'Message cannot be empty.'}, status=400)

        # Pick up any pending book context set by StartConversationView
        session_key = f'pending_book_{conv.pk}'
        pending_book_id = request.session.pop(session_key, None)
        book_obj = None
        if pending_book_id:
            from books.models import Book as BookModel
            book_obj = BookModel.objects.filter(pk=pending_book_id).first()

        msg = ChatMessage.objects.create(
            conversation=conv,
            sender=user,
            body=body,
            book=book_obj,
        )

        return JsonResponse({
            'ok': True,
            'id': msg.pk,
            'sender': msg.sender.username,
            'body': msg.body,
            'is_self': True,
            'created_at': msg.created_at.strftime('%b %d · %I:%M %p'),
            'book_title': msg.book.title if msg.book else None,
            'book_url': (
                reverse('books:detail', kwargs={
                    'seller': msg.book.seller.username,
                    'slug': msg.book.slug,
                }) if msg.book else None
            ),
        })


class StartConversationView(LoginRequiredMixin, View):
    """
    Called when the user clicks "Message Seller" (detail/orders page)
    or "Message Buyer" (sales page).

    GET  /messages/start/?book=<slug>&with=<username>
         → get_or_create a Conversation, redirect to inbox with ?conv=<pk>
    """
    login_url = 'accounts:login'

    def get(self, request):
        user = request.user
        book_slug = request.GET.get('book')
        with_username = request.GET.get('with')

        if not with_username:
            return redirect('books:messages_inbox')

        from django.contrib.auth.models import User as AuthUser
        other = get_object_or_404(AuthUser, username=with_username)

        if other == user:
            return redirect('books:messages_inbox')

        book = None
        if book_slug:
            book = Book.objects.filter(slug=book_slug).first()

        # Determine who is buyer / seller.
        # The seller is always the one who owns the book listing.
        # If no book, the initiating user is treated as the buyer.
        if book:
            buyer  = user   if user  != book.seller else other
            seller = other  if user  != book.seller else user
        else:
            buyer  = user
            seller = other

        conv, created = Conversation.objects.get_or_create(
            buyer=buyer,
            seller=seller,
            defaults={'book': book},
        )

        # If this is a new book context on an existing thread, create a
        # system-style opening message tagged with the book so the UI can
        # render an inline book pill as a context-switch marker.
        if book and not created:
            last = conv.chat_messages.order_by('-created_at').first()  # type: ignore[attr-defined]
            last_book_id = last.book_id if last else None  # type: ignore[attr-defined]
            if last_book_id != book.pk:
                # Tag the next real message by storing a zero-body sentinel?
                # No — just stash the pending book in the session so
                # SendChatMessageView can attach it to the first new message.
                request.session[f'pending_book_{conv.pk}'] = book.pk

        return redirect(f"{reverse('books:messages_inbox')}?conv={conv.pk}")