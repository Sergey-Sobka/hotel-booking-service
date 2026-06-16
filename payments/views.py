import stripe
from django.conf import settings
from drf_spectacular.utils import (
    extend_schema,
    OpenApiParameter,
    OpenApiResponse,
)
from rest_framework import viewsets, status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated

from .models import Payment
from .serializers import PaymentSerializer

from .services import complete_payment_process

stripe.api_key = settings.STRIPE_SECRET_KEY


class PaymentSuccessView(APIView):
    @extend_schema(
        summary="Confirm payment success",
        description="Verify the Stripe session status and finalize the booking payment process. If the payment is confirmed in Stripe, the booking status is updated accordingly.",
        parameters=[
            OpenApiParameter(
                name="session_id",
                description="The unique identifier of the Stripe Checkout session.",
                required=True,
                type=str,
                location=OpenApiParameter.QUERY,
            )
        ],
        responses={
            200: OpenApiResponse(
                description="Payment successfully verified and booking updated."
            ),
            400: OpenApiResponse(
                description="Invalid session or payment not completed."
            ),
            404: OpenApiResponse(description="Payment record not found."),
        },
    )
    def get(self, request):
        session_id = request.query_params.get("session_id")

        if not session_id:
            return Response(
                {"error": "Missing session_id."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            payment = Payment.objects.get(session_id=session_id)

            if payment.status != Payment.StatusChoices.PAID:
                stripe_session = stripe.checkout.Session.retrieve(session_id)
                if stripe_session.payment_status != "paid":
                    return Response(
                        {"error": "Not paid yet."},
                        status=status.HTTP_400_BAD_REQUEST,
                    )

                complete_payment_process(payment)

            return Response(
                {
                    "message": "Payment successful",
                    "booking": {
                        "id": payment.booking.id,
                        "status": payment.booking.status,
                        "check_in": payment.booking.check_in_date,
                    },
                },
                status=status.HTTP_200_OK,
            )

        except Payment.DoesNotExist:
            return Response(
                {"error": "Payment not found."},
                status=status.HTTP_404_NOT_FOUND,
            )
        except stripe.error.StripeError as e:
            return Response(
                {"error": f"Stripe error: {str(e)}"},
                status=status.HTTP_400_BAD_REQUEST,
            )


class PaymentCancelView(APIView):
    @extend_schema(
        summary="Handle cancelled payment",
        description="Endpoint triggered when the user cancels the payment process in the Stripe checkout flow.",
        responses={
            200: OpenApiResponse(description="Cancellation message received.")
        },
    )
    def get(self, request):
        return Response(
            {"message": "Payment process was cancelled by the user."},
            status=status.HTTP_200_OK,
        )


class PaymentViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Payment.objects.all()
    serializer_class = PaymentSerializer
    permission_classes = [IsAuthenticated]

    @extend_schema(
        summary="List payments",
        description="Retrieve a list of payments associated with the authenticated user.",
    )
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

    def get_queryset(self):
        user = self.request.user
        if user.is_staff:
            return Payment.objects.all()
        return Payment.objects.filter(booking__user=user)
