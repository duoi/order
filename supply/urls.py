from django.contrib import admin
from django.urls import include, path, re_path
from rest_framework import routers

from order.viewsets import OrderViewSet
from product.viewsets import ProductViewSet
from knox import views as knox_views

from user.viewsets import AuthenticationViewset

router = routers.DefaultRouter()
router.register(r'orders', OrderViewSet)
router.register(r'products', ProductViewSet)
router.register(r'auth/login', AuthenticationViewset, basename="login")

urlpatterns = [
    path('admin/', admin.site.urls),
    re_path(r'api/', include(router.urls)),
    re_path(r'api/auth/logout/', knox_views.LogoutView.as_view(), name='knox_logout'),
    re_path(r'api/auth/logoutall/', knox_views.LogoutAllView.as_view(), name='knox_logoutall'),
]
