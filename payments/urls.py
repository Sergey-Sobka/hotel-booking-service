from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import PaymentViewSet, PaymentSuccessView, PaymentCancelView

app_name = "payments"

router = DefaultRouter()
router.register(r"", PaymentViewSet, basename="payment")

urlpatterns = [
    path("success/", PaymentSuccessView.as_view(), name="payment-success"),
    path("cancel/", PaymentCancelView.as_view(), name="payment-cancel"),
    path("", include(router.urls)),
]
