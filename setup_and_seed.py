import django, os, sys

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "techtest.settings")
sys.path.append(os.path.realpath(os.path.dirname(__file__)))
django.setup()

from techtest.articles.models import Article
from techtest.regions.models import Region
from django.core import management

# Migrate
management.call_command("migrate", no_input=True)

# Seed 
# seed data using get_or_create to avoid duplicates
region_al, _ = Region.objects.get_or_create(code="AL", defaults={"name": "Albania"})
region_uk, _ = Region.objects.get_or_create(code="UK", defaults={"name": "United Kingdom"})
region_au, _ = Region.objects.get_or_create(code="AU", defaults={"name": "Austria"})
region_us, _ = Region.objects.get_or_create(code="US", defaults={"name": "United States of America"})

# duplicate seed data check
if not Article.objects.filter(regions__code="AL").exists():
    article1 = Article.objects.create(title="Fake Article", content="Fake Content")
    article1.regions.set([region_al, region_uk])
    
    Article.objects.create(title="Fake Article", content="Fake Content")
    Article.objects.create(title="Fake Article", content="Fake Content")
    Article.objects.create(title="Fake Article", content="Fake Content")

    articleX = Article.objects.create(title="Fake Article", content="Fake Content")
    articleX.regions.set([region_au, region_us])

print("Database setup and seeded successfully.")
