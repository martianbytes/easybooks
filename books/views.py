from django.views.generic import TemplateView, ListView, CreateView, DetailView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy
from django.http import JsonResponse
import base64
import binascii
import io
import json
import uuid

from django.contrib.auth.decorators import login_required
from django.core.files.uploadedfile import InMemoryUploadedFile
from django.db import transaction
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from .forms import AuthorForm, BookForm, BookImageFormSet
from .models import Author, Book, Message

IMAGE_FORMSET_PREFIX = "images"
MAX_DATAURL_IMAGE_BYTES = 8 * 1024 * 1024  # 8 MB per reconstructed image


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

        category = self.request.GET.get("genre")
        if category:
            queryset = queryset.filter(category=category)

        language = self.request.GET.get("language")
        if language:
            queryset = queryset.filter(language=language)

        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["genre_choices"] = Book.CATEGORY_CHOICES
        context["language_choices"] = Book.LANGUAGE_CHOICES
        context["selected_genre"] = self.request.GET.get("genre")
        context["selected_language"] = self.request.GET.get("language")
        return context


class SubscribeView(CreateView):
    def post(self, request):
        email = request.POST.get("email")
        return JsonResponse({"status": "success"})


class BookDetailView(DetailView):
    model = Book
    template_name = "books/detail.html"
    context_object_name = "book"


class CheckoutView(LoginRequiredMixin, DetailView):
    model = Book
    template_name = "books/checkout.html"
    context_object_name = "book"
    login_url = "login"


class ContactSellerView(LoginRequiredMixin, CreateView):
    model = Message
    template_name = "books/contact_seller.html"
    fields = ["message"]
    success_url = reverse_lazy("books:browse")
    login_url = "login"

    def form_valid(self, form):
        form.instance.buyer = self.request.user
        form.instance.book = Book.objects.get(pk=self.kwargs["pk"])
        form.instance.seller = form.instance.book.seller
        return super().form_valid(form)


@login_required
@require_POST
def author_create_ajax(request):
    form = AuthorForm(request.POST)
    if form.is_valid():
        author = form.save()
        return JsonResponse({"id": author.pk, "name": author.name})
    return JsonResponse({"errors": form.errors.get_json_data()}, status=400)


@login_required
def book_create(request):
    return _book_upsert(request, instance=None)


@login_required
def book_edit(request, slug):
    book = get_object_or_404(Book, slug=slug, seller=request.user)
    return _book_upsert(request, instance=book)


def _book_upsert(request, instance=None):
    editing = instance is not None

    if request.method == "POST":
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
            with transaction.atomic():
                book = book_form.save(commit=False)
                if not editing:
                    book.seller = request.user
                book.save()
                book_form.save_m2m()

                image_forms.instance = book
                image_forms.save()

            return redirect("books:detail", slug=book.slug)

        return render(
            request,
            "books/sell.html",
            _sell_context(
                book_form=book_form,
                image_forms=image_forms,
                image_data_urls=_collect_dataurl_values(request.POST),
                editing=editing,
                book=instance,
            ),
        )

    book_form = BookForm(instance=instance)
    image_forms = BookImageFormSet(instance=instance, prefix=IMAGE_FORMSET_PREFIX)

    return render(
        request,
        "books/sell.html",
        _sell_context(
            book_form=book_form,
            image_forms=image_forms,
            image_data_urls={},
            editing=editing,
            book=instance,
        ),
    )


def _sell_context(*, book_form, image_forms, image_data_urls, editing, book):
    return {
        "book_form": book_form,
        "image_forms": image_forms,
        "image_data_urls": json.dumps(image_data_urls),
        "all_authors": Author.objects.order_by("name").values("id", "name"),
        "editing": editing,
        "book": book,
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
