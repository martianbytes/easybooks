from django.urls import path
from . import views
from django.conf import settings
from django.conf.urls.static import static
from .views import author_create_ajax

app_name = "books"

urlpatterns = [
    path("", views.HomeView.as_view(), name="home"),
    path("browse/", views.BrowseView.as_view(), name="browse"),
    path("sell/", views.BookCreateView.as_view(), name="sell"),
    path("book/<str:seller>/<slug:slug>/", views.BookDetailView.as_view(), name="detail"),
    path("book/<str:seller>/<slug:slug>/checkout/", views.CheckoutView.as_view(), name="checkout"),
    path(
        "book/<str:seller>/<slug:slug>/contact-seller/",
        views.ContactSellerView.as_view(),
        name="contact_seller",
    ),
    path("subscribe/", views.SubscribeView.as_view(), name="subscribe"),
    path("book/<str:seller>/<slug:slug>/edit/", views.BookEditView.as_view(), name="edit"),
    path('order/<slug:order_slug>/confirmed/', views.OrderConfirmedView.as_view(), name='order_confirmed'),
    # path("authors/create-ajax/", author_create_ajax.as)
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
