from django.test import TestCase
from rooms.models import Room


class TestRoomModel(TestCase):

    def test_create_room_and_str_method(self):
        room = Room.objects.create(
            number="101A",
            room_type=Room.RoomType.SUITE,
            price_per_night=250.00,
            capacity=4,
        )
        self.assertEqual(str(room), "Room 101A - Suite")
        self.assertEqual(room.number, "101A")
        self.assertEqual(room.capacity, 4)

    def test_default_room_type_is_single(self):
        room = Room.objects.create(number="102B", price_per_night=50.00, capacity=1)
        self.assertEqual(room.room_type, Room.RoomType.SINGLE)
