from django.utils.text import slugify
from unidecode import unidecode

def generate_unique_slug(model_class, name_parts):
    base_slug = slugify(unidecode("-".join(name_parts)))
    slug = base_slug
    counter = 1
    while model_class.objects.filter(slug=slug).exists():
        slug = f"{base_slug}-{counter}"
        counter += 1
    return slug