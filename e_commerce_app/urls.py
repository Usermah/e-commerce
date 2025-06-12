from django.urls import path
from . import views
from django.conf import settings
from django.conf.urls.static import static


urlpatterns = [
    path('', views.product_list, name='product_list'),
    path('product/<int:pk>/', views.product_detail, name='product_detail'),
    path('cart/', views.cart_view, name='cart'),
    path('checkout/', views.checkout, name='checkout'),
    path('cart/update/<int:product_id>/', views.update_cart, name='update_cart'),
    path('payment/', views.initiate_payment, name='initiate_payment'),
    path('payment/verify/<str:reference>/', views.verify_payment, name='verify_payment'),


]+static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT) \
+static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
