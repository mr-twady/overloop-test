import json

from django.test import TestCase
from django.urls import reverse

from techtest.articles.models import Article
from techtest.regions.models import Region
from techtest.authors.models import Author


class ArticleListViewTestCase(TestCase):
    def setUp(self):
        self.url = reverse("articles-list")
        self.author = Author.objects.create(first_name="John", last_name="Doe")
        self.article_1 = Article.objects.create(title="Fake Article 1")
        self.region_1 = Region.objects.create(code="AL", name="Albania")
        self.region_2 = Region.objects.create(code="UK", name="United Kingdom")
        self.article_2 = Article.objects.create(
            title="Fake Article 2", content="Lorem Ipsum"
        )
        self.article_2.regions.set([self.region_1, self.region_2])
        self.article_3 = Article.objects.create(
            title="Fake Article 3", content="With Author", author=self.author
        )

    def test_serializes_with_correct_data_shape_and_status_code(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertCountEqual(
            response.json(),
            [
                {
                    "id": self.article_1.id,
                    "title": "Fake Article 1",
                    "content": "",
                    "author": None,
                    "regions": [],
                },
                {
                    "id": self.article_2.id,
                    "title": "Fake Article 2",
                    "content": "Lorem Ipsum",
                    "author": None,
                    "regions": [
                        {
                            "code": "AL",
                            "name": "Albania",
                        },
                        {
                            "code": "UK",
                            "name": "United Kingdom",
                        },
                    ],
                },
                {
                    "id": self.article_3.id,
                    "title": "Fake Article 3",
                    "content": "With Author",
                    "author": {
                        "id": self.author.id,
                        "first_name": "John",
                        "last_name": "Doe",
                    },
                    "regions": [],
                },
            ],
        )

    def test_creates_new_article_with_regions(self):
        payload = {
            "title": "Fake Article 3",
            "content": "To be or not to be",
            "regions": [
                {"code": "US", "name": "United States of America"},
                {"code": "AU", "name": "Austria"},
            ],
        }
        response = self.client.post(
            self.url, data=json.dumps(payload), content_type="application/json"
        )
        article = Article.objects.last()
        regions = Region.objects.filter(articles__id=article.id)
        self.assertEqual(response.status_code, 201)
        self.assertIsNotNone(article)
        self.assertEqual(regions.count(), 2)
        self.assertDictEqual(
            {
                "id": article.id,
                "title": "Fake Article 3",
                "content": "To be or not to be",
                "author": None,
                "regions": [
                    {
                        "code": "US",
                        "name": "United States of America",
                    },
                    {"code": "AU", "name": "Austria"},
                ],
            },
            response.json(),
        )

    def test_creates_new_article_with_author(self):
        author = Author.objects.create(first_name="John", last_name="Doe")
        payload = {
            "title": "Fake Article 4",
            "content": "Article with author",
            "author": author.id,
        }
        response = self.client.post(
            self.url, data=json.dumps(payload), content_type="application/json"
        )
        article = Article.objects.last()
        self.assertEqual(response.status_code, 201)
        self.assertIsNotNone(article)
        self.assertEqual(article.author.id, author.id)
        self.assertDictEqual(
            {
                "id": article.id,
                "title": "Fake Article 4",
                "content": "Article with author",
                "author": {
                    "id": author.id,
                    "first_name": "John",
                    "last_name": "Doe",
                },
                "regions": [],
            },
            response.json(),
        )

    def test_creates_new_article_with_author_as_string_id(self):
        author = Author.objects.create(first_name="Jane", last_name="Smith")
        payload = {
            "title": "Fake Article 5",
            "content": "Article with author as string",
            "author": str(author.id),
        }
        response = self.client.post(
            self.url, data=json.dumps(payload), content_type="application/json"
        )
        article = Article.objects.last()
        self.assertEqual(response.status_code, 201)
        self.assertIsNotNone(article)
        self.assertEqual(article.author.id, author.id)

    def test_creates_new_article_with_author_and_regions(self):
        author = Author.objects.create(first_name="Bob", last_name="Johnson")
        payload = {
            "title": "Fake Article 6",
            "content": "Article with author and regions",
            "author": author.id,
            "regions": [
                {"code": "CA", "name": "Canada"},
            ],
        }
        response = self.client.post(
            self.url, data=json.dumps(payload), content_type="application/json"
        )
        article = Article.objects.last()
        regions = Region.objects.filter(articles__id=article.id)
        self.assertEqual(response.status_code, 201)
        self.assertIsNotNone(article)
        self.assertEqual(article.author.id, author.id)
        self.assertEqual(regions.count(), 1)


class ArticleViewTestCase(TestCase):
    def setUp(self):
        self.article = Article.objects.create(title="Fake Article 1")
        self.region_1 = Region.objects.create(code="AL", name="Albania")
        self.region_2 = Region.objects.create(code="UK", name="United Kingdom")
        self.article.regions.set([self.region_1, self.region_2])
        self.url = reverse("article", kwargs={"article_id": self.article.id})

    def test_serializes_single_record_with_correct_data_shape_and_status_code(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertCountEqual(
            response.json(),
            {
                "id": self.article.id,
                "title": "Fake Article 1",
                "content": "",
                "author": None,
                "regions": [
                    {
                        "code": "AL",
                        "name": "Albania",
                    },
                    {
                        "code": "UK",
                        "name": "United Kingdom",
                    },
                ],
            },
        )

    def test_updates_article_and_regions(self):
        # Change regions
        payload = {
            "title": "Fake Article 1 (Modified)",
            "content": "To be or not to be here",
            "regions": [
                {"code": "US", "name": "United States of America"},
                {"id": self.region_2.id},
            ],
        }
        response = self.client.put(
            self.url, data=json.dumps(payload), content_type="application/json"
        )
        article = Article.objects.first()
        regions = Region.objects.filter(articles__id=article.id)
        self.assertEqual(response.status_code, 200)
        self.assertIsNotNone(article)
        self.assertEqual(regions.count(), 2)
        self.assertEqual(Article.objects.count(), 1)
        self.assertDictEqual(
            {
                "id": article.id,
                "title": "Fake Article 1 (Modified)",
                "content": "To be or not to be here",
                "author": None,
                "regions": [
                    {
                        "code": "UK",
                        "name": "United Kingdom",
                    },
                    {
                        "code": "US",
                        "name": "United States of America",
                    },
                ],
            },
            response.json(),
        )
        # Remove regions
        payload["regions"] = []
        response = self.client.put(
            self.url, data=json.dumps(payload), content_type="application/json"
        )
        article = Article.objects.last()
        regions = Region.objects.filter(articles__id=article.id)
        self.assertEqual(response.status_code, 200)
        self.assertIsNotNone(article)
        self.assertEqual(regions.count(), 0)
        self.assertDictEqual(
            {
                "id": article.id,
                "title": "Fake Article 1 (Modified)",
                "content": "To be or not to be here",
                "author": None,
                "regions": [],
            },
            response.json(),
        )

    def test_updates_article_with_author(self):
        author = Author.objects.create(first_name="John", last_name="Doe")
        payload = {
            "title": "Fake Article 1 (With Author)",
            "content": "Updated content",
            "author": author.id,
        }
        response = self.client.put(
            self.url, data=json.dumps(payload), content_type="application/json"
        )
        article = Article.objects.first()
        self.assertEqual(response.status_code, 200)
        self.assertEqual(article.author.id, author.id)
        self.assertDictEqual(
            {
                "id": article.id,
                "title": "Fake Article 1 (With Author)",
                "content": "Updated content",
                "author": {
                    "id": author.id,
                    "first_name": "John",
                    "last_name": "Doe",
                },
                "regions": [
                    {
                        "code": "AL",
                        "name": "Albania",
                    },
                    {
                        "code": "UK",
                        "name": "United Kingdom",
                    },
                ],
            },
            response.json(),
        )

    def test_updates_article_with_author_as_string_id(self):
        author = Author.objects.create(first_name="Jane", last_name="Smith")
        payload = {
            "title": "Fake Article 1",
            "content": "Updated content",
            "author": str(author.id),
        }
        response = self.client.put(
            self.url, data=json.dumps(payload), content_type="application/json"
        )
        article = Article.objects.first()
        self.assertEqual(response.status_code, 200)
        self.assertEqual(article.author.id, author.id)

    def test_updates_article_removes_author_by_setting_null(self):
        author = Author.objects.create(first_name="John", last_name="Doe")
        self.article.author = author
        self.article.save()
        payload = {
            "title": "Fake Article 1",
            "content": "Updated content",
            "author": None,
        }
        response = self.client.put(
            self.url, data=json.dumps(payload), content_type="application/json"
        )
        article = Article.objects.first()
        self.assertEqual(response.status_code, 200)
        self.assertIsNone(article.author)
        self.assertIsNone(response.json()["author"])

    def test_updates_article_preserves_author_when_not_provided(self):
        author = Author.objects.create(first_name="John", last_name="Doe")
        self.article.author = author
        self.article.save()
        payload = {
            "title": "Fake Article 1 (Modified)",
            "content": "Updated content",
            # Note: author not provided
        }
        response = self.client.put(
            self.url, data=json.dumps(payload), content_type="application/json"
        )
        article = Article.objects.first()
        self.assertEqual(response.status_code, 200)
        self.assertEqual(article.author.id, author.id)
        # Author should still be present in response
        self.assertIsNotNone(response.json()["author"])

    def test_updates_article_changes_author(self):
        author1 = Author.objects.create(first_name="John", last_name="Doe")
        author2 = Author.objects.create(first_name="Jane", last_name="Smith")
        self.article.author = author1
        self.article.save()
        payload = {
            "title": "Fake Article 1",
            "content": "Updated content",
            "author": author2.id,
        }
        response = self.client.put(
            self.url, data=json.dumps(payload), content_type="application/json"
        )
        article = Article.objects.first()
        self.assertEqual(response.status_code, 200)
        self.assertEqual(article.author.id, author2.id)
        self.assertEqual(response.json()["author"]["id"], author2.id)

    def test_removes_article(self):
        response = self.client.delete(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(Article.objects.count(), 0)
