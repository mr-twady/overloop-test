import json

from django.test import TestCase
from django.urls import reverse

from techtest.authors.models import Author


class AuthorListViewTestCase(TestCase):
    def setUp(self):
        self.url = reverse("authors-list")
        self.author_1 = Author.objects.create(first_name="John", last_name="Doe")
        self.author_2 = Author.objects.create(first_name="Jane", last_name="Smith")

    def test_serializes_with_correct_data_shape_and_status_code(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertCountEqual(
            response.json(),
            [
                {
                    "id": self.author_1.id,
                    "first_name": "John",
                    "last_name": "Doe",
                },
                {
                    "id": self.author_2.id,
                    "first_name": "Jane",
                    "last_name": "Smith",
                },
            ],
        )

    def test_creates_new_author(self):
        payload = {
            "first_name": "Bob",
            "last_name": "Johnson",
        }
        response = self.client.post(
            self.url, data=json.dumps(payload), content_type="application/json"
        )
        author = Author.objects.last()
        self.assertEqual(response.status_code, 201)
        self.assertIsNotNone(author)
        self.assertEqual(Author.objects.count(), 3)
        self.assertDictEqual(
            {
                "id": author.id,
                "first_name": "Bob",
                "last_name": "Johnson",
            },
            response.json(),
        )

    def test_creates_author_with_validation_error(self):
        payload = {
            "first_name": "",  # Empty first name should still work but let's test with missing fields
        }
        response = self.client.post(
            self.url, data=json.dumps(payload), content_type="application/json"
        )
        self.assertEqual(response.status_code, 400)


class AuthorViewTestCase(TestCase):
    def setUp(self):
        self.author = Author.objects.create(first_name="John", last_name="Doe")
        self.url = reverse("author", kwargs={"author_id": self.author.id})

    def test_serializes_single_record_with_correct_data_shape_and_status_code(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertCountEqual(
            response.json(),
            {
                "id": self.author.id,
                "first_name": "John",
                "last_name": "Doe",
            },
        )

    def test_returns_404_for_nonexistent_author(self):
        url = reverse("author", kwargs={"author_id": 9999})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 404)
        self.assertIn("error", response.json())

    def test_updates_author(self):
        payload = {
            "id": self.author.id,
            "first_name": "Jane",
            "last_name": "Smith",
        }
        response = self.client.put(
            self.url, data=json.dumps(payload), content_type="application/json"
        )
        author = Author.objects.filter(id=self.author.id).first()
        self.assertEqual(response.status_code, 200)
        self.assertIsNotNone(author)
        self.assertEqual(Author.objects.count(), 1)
        self.assertEqual(author.first_name, "Jane")
        self.assertEqual(author.last_name, "Smith")
        self.assertDictEqual(
            {
                "id": author.id,
                "first_name": "Jane",
                "last_name": "Smith",
            },
            response.json(),
        )

    def test_removes_author(self):
        response = self.client.delete(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(Author.objects.count(), 0)
