from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import BacktestView, ItemViewSet, PredictStockPriceView, GenerateReportView, AvailableSymbolsView
from django.contrib import admin
from . import views

router = DefaultRouter()
router.register(r'items', ItemViewSet)

urlpatterns = [
    path('', include(router.urls)),
    path('backtest/', BacktestView.as_view(), name='backtest'),
    path('predict/', PredictStockPriceView.as_view(), name='predict'),
    path('generate-report/', GenerateReportView.as_view(), name='generate-report'),
    path('available-symbols/', AvailableSymbolsView.as_view(), name='available-symbols'),
]