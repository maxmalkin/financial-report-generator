from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import ItemViewSet
from django.contrib import admin
from django.urls import path, include

router = DefaultRouter()
router.register(r'items', ItemViewSet)

urlpatterns = [
    path('', include(router.urls)),
]

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include('api.urls')),
]