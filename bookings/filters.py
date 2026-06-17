import django_filters
from .models import Booking


class BookingFilter(django_filters.FilterSet):
    check_in_from = django_filters.DateFilter(
        field_name="check_in_date", lookup_expr="gte"
    )
    check_in_to = django_filters.DateFilter(
        field_name="check_in_date", lookup_expr="lte"
    )
    check_out_from = django_filters.DateFilter(
        field_name="check_out_date", lookup_expr="gte"
    )
    check_out_to = django_filters.DateFilter(
        field_name="check_out_date", lookup_expr="lte"
    )

    class Meta:
        model = Booking
        fields = [
            "status",
            "room__room_type",
            "room",
            "check_in_from",
            "check_in_to",
            "check_out_from",
            "check_out_to",
        ]
