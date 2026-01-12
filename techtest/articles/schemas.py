from marshmallow import validate
from marshmallow import fields
from marshmallow import Schema
from marshmallow.decorators import post_load, post_dump

from techtest.articles.models import Article
from techtest.regions.models import Region
from techtest.regions.schemas import RegionSchema, RegionLiteSchema
from techtest.authors.models import Author
from techtest.authors.schemas import AuthorSchema


class ArticleSchema(Schema):
    class Meta(object):
        model = Article

    id = fields.Integer()
    title = fields.String(validate=validate.Length(max=255))
    content = fields.String() 
    author = fields.Method(
        required=False, serialize="get_author"
    )
    # Store raw author value for deserialization
    _author_raw = fields.Raw(required=False, allow_none=True, data_key="author", load_only=True)
    regions = fields.Method(
        required=False, serialize="get_regions", deserialize="load_regions"
    )

    def get_author(self, article):
        if article.author:
            return AuthorSchema().dump(article.author)
        return None

    def load_author(self, author):
        """Convert author from various formats (None, ID, dict, etc.) to Author instance."""
        # Handle None/null explicitly
        if author is None or author == "null":
            return None
        # Handle string or integer ID (e.g., "1" or 1)
        if isinstance(author, (str, int)):
            try:
                return Author.objects.get(pk=int(author))
            except (Author.DoesNotExist, ValueError):
                return None
        if isinstance(author, dict):
            author_id = author.get("id", None)
            if author_id:
                try:
                    return Author.objects.get(pk=author_id)
                except Author.DoesNotExist:
                    # If author doesn't exist, create new one with provided data
                    author_data = {k: v for k, v in author.items() if k != "id"}
                    return Author.objects.create(**author_data)
            # Create new author if no id provided
            return Author.objects.create(**author)
        # Already an Author instance
        return author
    
    @post_dump
    def serialize_author(self, data, **kwargs):
        """Serialize author field using AuthorSchema."""
        # During dump, the author will be an Author instance from the model
        # fields.Raw passes it through as-is, so we serialize it here
        if "author" in data:
            if data["author"] is None:
                data["author"] = None
            elif hasattr(data["author"], "id"):
                # It's an Author instance, serialize it
                data["author"] = AuthorSchema().dump(data["author"])
        return data

    def get_regions(self, article):
        # return RegionSchema().dump(article.regions.all(), many=True)
        return RegionLiteSchema().dump(article.regions.all(), many=True)

    def load_regions(self, regions):
        return [
            Region.objects.get_or_create(id=region.pop("id", None), defaults=region)[0]
            for region in regions
        ]

    @post_load
    def update_or_create(self, data, *args, **kwargs):
        # Check if author was provided before popping (to distinguish between not provided and None)
        # Use _author_raw which is the raw field, or check both
        author_provided = "_author_raw" in data or "author" in data
        author_value = data.pop("_author_raw", None) or data.pop("author", None) if author_provided else None
        # Convert author value to Author instance (or None)
        author = self.load_author(author_value) if author_provided else None
        regions = data.pop("regions", None)
        article, _ = Article.objects.update_or_create(
            id=data.pop("id", None), defaults=data
        )
         # Set author only if it was provided in the input (can be None to remove the relationship)
        if author_provided:
            article.author = author
            article.save()
        if isinstance(regions, list):
            article.regions.set(regions)
        return article
