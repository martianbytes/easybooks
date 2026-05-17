from django.urls import path
from django.conf import settings
from django.conf.urls.static import static
from .views import (
    HomeView,
    BrowseView,
    BookCreateView,
    AuthorCreateView,
    BookDetailView,
    CheckoutView,
    ContactSellerView,
    SubscribeView,
    BookEditView,
    BookDeleteView,
    OrderConfirmedView,
    CartView,
    AddToCartView,
    RemoveFromCartView,
    CartCheckoutView,
    CartOrderConfirmedView,
)

app_name = "books"

urlpatterns = [
    path("", HomeView.as_view(), name="home"),
    path("browse/", BrowseView.as_view(), name="browse"),
    path("sell/", BookCreateView.as_view(), name="sell"),
    path("sell/add-author/", AuthorCreateView.as_view(), name="author_create"),
    path("book/<str:seller>/<slug:slug>/", BookDetailView.as_view(), name="detail"),
    path("book/<str:seller>/<slug:slug>/checkout/", CheckoutView.as_view(), name="checkout"),
    path(
        "book/<str:seller>/<slug:slug>/contact-seller/",
        ContactSellerView.as_view(),
        name="contact_seller",
    ),
    path("subscribe/", SubscribeView.as_view(), name="subscribe"),
    path("book/<str:seller>/<slug:slug>/edit/", BookEditView.as_view(), name="edit"),
    path("book/<str:seller>/<slug:slug>/delete/", BookDeleteView.as_view(), name="delete"),
    path("order/<slug:order_slug>/confirmed/", OrderConfirmedView.as_view(), name="order_confirmed"),
    path("cart/", CartView.as_view(), name="cart"),
    path("cart/add/<str:seller>/<slug:slug>/", AddToCartView.as_view(), name="add_to_cart"),
    path("cart/remove/<slug:slug>/", RemoveFromCartView.as_view(), name="remove_from_cart"),
    path("cart/checkout/", CartCheckoutView.as_view(), name="cart_checkout"),
    path("cart/order-confirmed/", CartOrderConfirmedView.as_view(), name="cart_order_confirmed"),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
