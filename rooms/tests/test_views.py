from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from decimal import Decimal

from rooms.models import Room

User = get_user_model()


class TestRoomViewSet(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            email="user@example.com", password="testpassword123"
        )
        self.admin = User.objects.create_user(
            email="admin@example.com",
            password="adminpassword123",
            is_staff=True,
        )

        self.room1 = Room.objects.create(
            number="101",
            room_type="SINGLE",
            price_per_night=Decimal("50.00"),
            capacity=1,
        )
        self.room2 = Room.objects.create(
            number="102",
            room_type="DOUBLE",
            price_per_night=Decimal("100.00"),
            capacity=2,
        )
        self.room3 = Room.objects.create(
            number="103",
            room_type="SUITE",
            price_per_night=Decimal("200.00"),
            capacity=4,
        )

        self.list_url = reverse("rooms:room-list")
        self.detail_url = reverse(
            "rooms:room-detail", kwargs={"pk": self.room1.pk}
        )

    def test_list_rooms_public_access(self):
        res = self.client.get(self.list_url)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(len(res.data), 3)

    def test_create_room_admin_only(self):
        self.client.force_authenticate(user=self.admin)

        payload = {
            "number": "201",
            "room_type": "DOUBLE",
            "price_per_night": "150.00",
            "capacity": 2,
        }
        res = self.client.post(self.list_url, payload)

        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        self.assertTrue(Room.objects.filter(number="201").exists())

    def test_create_room_forbidden_for_regular_user(self):
        self.client.force_authenticate(user=self.user)

        payload = {
            "number": "202",
            "room_type": "SINGLE",
            "price_per_night": "80.00",
            "capacity": 1,
        }
        res = self.client.post(self.list_url, payload)

        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)
        self.assertFalse(Room.objects.filter(number="202").exists())

    def test_filter_rooms_by_type(self):
        res = self.client.get(self.list_url, {"type": "DOUBLE"})

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(len(res.data), 1)
        self.assertEqual(res.data[0]["number"], self.room2.number)

    def test_filter_rooms_by_capacity(self):
        res = self.client.get(self.list_url, {"capacity": 4})

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(len(res.data), 1)
        self.assertEqual(res.data[0]["number"], self.room3.number)

    def test_filter_rooms_by_invalid_capacity(self):
        res = self.client.get(self.list_url, {"capacity": "invalid"})

        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("capacity", res.data)
