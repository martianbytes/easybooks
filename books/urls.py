from django.urls import path
from . import views
from django.conf import settings
from django.conf.urls.static import static

app_name = "books"

urlpatterns = [
    path("", views.HomeView.as_view(), name="home"),
    path("browse/", views.BrowseView.as_view(), name="browse"),
    path("sell/", views.BookCreateView.as_view(), name="sell"),
    path("book/<slug:slug>/", views.BookDetailView.as_view(), name="detail"),
    path("book/<slug:slug>/checkout/", views.CheckoutView.as_view(), name="checkout"),
    path(
        "book/<slug:slug>/contact-seller/",
        views.ContactSellerView.as_view(),
        name="contact_seller",
    ),
    path("subscribe/", views.SubscribeView.as_view(), name="subscribe"),
    path("book/<slug:slug>/edit/", views.BookEditView.as_view(), name="edit"),

    # path('', views.HomeView.as_view(), name='home'),
    # path('browse/', views.BrowseView.as_view(), name='browse'),
    # path('sell/', views.SellView.as_view(), name='sell'),
    # path('book/<slug:slug>/', views.BookDetailView.as_view(), name='detail'),
    # path('book/<slug:slug>/checkout/', views.CheckoutView.as_view(), name='checkout'),
    # path('book/<slug:slug>/contact-seller/', views.ContactSellerView.as_view(), name='contact_seller'),
    # path('subscribe/', views.SubscribeView.as_view(), name='subscribe'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
