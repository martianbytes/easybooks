from django.urls import path
from . import views
from django.conf import settings
from django.conf.urls.static import static

app_name = "books"

urlpatterns = [
    path("", views.HomeView.as_view(), name="home"),
    path("browse/", views.BrowseView.as_view(), name="browse"),
    path("sell/", views.book_create, name="sell"),
    path("book/<int:pk>/", views.BookDetailView.as_view(), name="detail"),
    path("book/<int:pk>/checkout/", views.CheckoutView.as_view(), name="checkout"),
    path(
        "book/<int:pk>/contact-seller/",
        views.ContactSellerView.as_view(),
        name="contact_seller",
    ),
    path("subscribe/", views.SubscribeView.as_view(), name="subscribe"),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
