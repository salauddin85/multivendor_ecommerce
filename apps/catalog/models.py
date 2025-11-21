# apps/catalog/models.py
from django.db import models
from django.utils.text import slugify

class CatalogBaseModel(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        abstract = True
        

class Category(CatalogBaseModel):
    name = models.CharField(max_length=255)
    slug = models.SlugField(unique=True)
    parent = models.ForeignKey(
        "self", null=True, blank=True, on_delete=models.CASCADE, related_name="children"
    )
    icon = models.ImageField(upload_to="category_icons/", blank=True, null=True)
    display_order = models.IntegerField(default=0)


    def save(self, *args, **kwargs):
        if not self.slug:
            base_slug = slugify(self.name)
            slug = base_slug
            counter = 1
            while Category.objects.filter(slug=slug).exists():
                slug = f"{base_slug}-{counter}"
                counter += 1
            self.slug = slug
        super().save(*args, **kwargs)


class Brand(CatalogBaseModel):

    name = models.CharField(max_length=255)
    slug = models.SlugField(unique=True)
    logo = models.ImageField(upload_to="brand_logos/", blank=True, null=True)
    display_order = models.IntegerField(default=0)

    def save(self, *args, **kwargs):
        if not self.slug:
            base_slug = slugify(self.name)
            slug = base_slug
            counter = 1
            while Brand.objects.filter(slug=slug).exists():
                slug = f"{base_slug}-{counter}"
                counter += 1
            self.slug = slug
        super().save(*args, **kwargs)
        

class CategoryAnalytics(CatalogBaseModel):
    category = models.OneToOneField(Category, on_delete=models.CASCADE, related_name='analytics')
    views_count = models.PositiveIntegerField(default=0)      #how many view this type of product
    products_count = models.PositiveIntegerField(default=0)    # total products in this category
    total_sold = models.IntegerField(default=0)                # how many products sold for this type of category
    avg_rating = models.DecimalField(max_digits=3, decimal_places=2, default=0.00)  # category rating
    top_product_id = models.IntegerField(null=True, blank=True)  # most of sold type of product


class BrandAnalytics(CatalogBaseModel):
    brand = models.OneToOneField(Brand, on_delete=models.CASCADE, related_name='analytics')
    views_count = models.PositiveIntegerField(default=0)       # how many view this type of product brand
    products_count = models.PositiveIntegerField(default=0)    # total products under this brand
    total_sold = models.IntegerField(default=0)                # total sold this type of brand products
    avg_rating = models.DecimalField(max_digits=3, decimal_places=2, default=0.00)  # average rating
    top_product_id = models.IntegerField(null=True, blank=True)  # top selling product


