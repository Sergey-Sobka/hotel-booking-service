from django.test import TestCase
from decimal import Decimal
from rooms.models import Room
from rooms.serializers import RoomSerializer


class TestRoomSerializer(TestCase):
    def setUp(self):
        self.valid_data = {
            "number": "201",
            "room_type": "DOUBLE",
            "price_per_night": Decimal("150.00"),
            "capacity": 2,
        }

    def test_serializer_read_only_display_field(self):
        room = Room.objects.create(
            number="202",
            room_type=Room.RoomType.SUITE,
            price_per_night=Decimal("300.00"),
            capacity=4,
        )
        serializer = RoomSerializer(instance=room)

        self.assertIn("room_type_display", serializer.data)
        self.assertEqual(serializer.data["room_type_display"], "Suite")

    def test_serializer_invalid_negative_price(self):
        invalid_data = self.valid_data.copy()
        invalid_data["price_per_night"] = Decimal("-10.00")

        serializer = RoomSerializer(data=invalid_data)

        self.assertFalse(serializer.is_valid())
        self.assertIn("price_per_night", serializer.errors)
        self.assertEqual(
            str(serializer.errors["price_per_night"][0]),
            "The price per night cannot be less than 0.",
        )

    def test_serializer_invalid_zero_capacity(self):
        invalid_data = self.valid_data.copy()
        invalid_data["capacity"] = 0

        serializer = RoomSerializer(data=invalid_data)

        self.assertFalse(serializer.is_valid())
        self.assertIn("capacity", serializer.errors)
        self.assertEqual(
            str(serializer.errors["capacity"][0]),
            "The room capacity must be greater than 0.",
        )
