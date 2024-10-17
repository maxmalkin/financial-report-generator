from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import ItemViewSet, BacktestView, fetch_data_view
from django.contrib import admin
from . import views

router = DefaultRouter()
router.register(r'items', ItemViewSet)

urlpatterns = [
    path('', include(router.urls)),
    path('fetch/', fetch_data_view, name='fetch-data'),
    path('backtest/', BacktestView.as_view(), name='backtest'),
]