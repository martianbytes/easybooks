from django.urls import path
from .views import HomeView, BrowseView, SellView, SubscribeView

app_name = 'books'

urlpatterns = [
    path('', HomeView.as_view(), name='home'),
    path('browse/', BrowseView.as_view(), name='browse'),
    path('sell/', SellView.as_view(), name='sell'),
    path('subscribe/', SubscribeView.as_view(), name='subscribe'),
]