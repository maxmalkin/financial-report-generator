from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import ItemViewSet
from . import views
from django.contrib import admin
from .views import BacktestView

router = DefaultRouter()
router.register(r'items', ItemViewSet)

urlpatterns = [
    path('', include(router.urls)),
]

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include('api.urls')),
    path('fetch/', views.fetch_data_view, name='fetch-data'),
    path('backtest/', BacktestView.as_view(), name='backtest'),
]