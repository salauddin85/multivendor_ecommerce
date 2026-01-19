from django.db import models
from django.utils.text import slugify
from apps.catalog.models import Category, Brand
from apps.stores.models import Store
from .constants.choices import TYPE, STATUS


# -------------------------------
# Abstract Base Model
# -------------------------------
class ProductBaseModel(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


# Product Model
class Product(ProductBaseModel):
    store = models.ForeignKey(Store, on_delete=models.CASCADE, related_name="products",db_index=True, null=True, blank=True)
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, blank=True, db_index=True)
    brand = models.ForeignKey(Brand, on_delete=models.SET_NULL, null=True, blank=True, db_index=True)
    title = models.CharField(max_length=500)
    slug = models.SlugField(unique=True, max_length=255)
    type = models.CharField(max_length=20, choices=TYPE, default="simple")
    description = models.TextField(blank=True, default='')
    base_price = models.DecimalField(max_digits=10, decimal_places=2, default='0.00')
    main_image = models.ImageField(upload_to="products/main_images/", null=True, blank=True)
    stock = models.IntegerField(default=0)
    status = models.CharField(max_length=20, choices=STATUS, default="draft")
    is_featured = models.BooleanField(default=False)
    view_count = models.IntegerField(default=0)
    avg_rating = models.DecimalField(max_digits=3, decimal_places=2, default='0.00')
    total_reviews = models.IntegerField(default=0)

    def save(self, *args, **kwargs):
        if not self.slug:
            base_slug = slugify(self.title)
            slug = base_slug
            counter = 1
            while Product.objects.filter(slug=slug).exists():
                slug = f"{base_slug}-{counter}"
                counter += 1
            self.slug = slug
        super().save(*args, **kwargs)

    def __str__(self):
        return self.title



# Product Images (Multiple)
class ProductImage(ProductBaseModel):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="images",db_index=True)
    image = models.ImageField(upload_to="products/gallery/")

    def __str__(self):
        return f"Image of {self.product.title}"


# Product Attributes
class ProductAttribute(ProductBaseModel):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="attributes",db_index=True)
    name = models.CharField(max_length=100)
    is_variation = models.BooleanField(default=True)
    
    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['product', 'name'], name='unique_product_attribute')
        ]

    def __str__(self):
        return f"{self.name}"


# Product Attribute Values
class ProductAttributeValue(ProductBaseModel):
    attribute = models.ForeignKey(ProductAttribute, on_delete=models.CASCADE, related_name="values",db_index=True)
    value = models.CharField(max_length=100)
    color_code = models.CharField(max_length=20, blank=True, default='')
    
    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['attribute', 'value'], name='unique_attribute_value')
        ]

    def __str__(self):
        return f"{self.value} ({self.attribute.name})"


# Product Variants
class ProductVariant(ProductBaseModel):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="variants",db_index=True)
    sku = models.CharField(max_length=50, unique=True)
    variant_name = models.CharField(max_length=255, default='')
    price = models.DecimalField(max_digits=10, decimal_places=2, default='0.00')
    discount_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    stock = models.IntegerField(default=0)
    image = models.ImageField(upload_to="products/variant_images/", null=True, blank=True)

    def __str__(self):
        return f"{self.variant_name} ({self.product.title})"


# Product Variant Attributes
class ProductVariantAttribute(models.Model):
    variant = models.ForeignKey(ProductVariant, on_delete=models.CASCADE, related_name="variant_attrs",db_index=True)
    attribute = models.ForeignKey(ProductAttribute, on_delete=models.CASCADE, related_name="variant_attrs",db_index=True)
    value = models.ForeignKey(ProductAttributeValue, on_delete=models.CASCADE, related_name="variant_attrs")

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['variant', 'attribute'], name='unique_variant_attribute')
        ]
    def __str__(self):
        return f"{self.attribute.name}: {self.value.value} ({self.variant.variant_name})"


# Product Analytics
class ProductAnalytics(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="analytics",db_index=True)
    date = models.DateField(auto_now_add=True, db_index=True)
    views = models.IntegerField(default=0)
    add_to_cart = models.IntegerField(default=0)
    wishlist = models.IntegerField(default=0)
    sales_count = models.IntegerField(default=0)
    revenue = models.DecimalField(max_digits=12, decimal_places=2, default='0.00')

    class Meta:
        unique_together = ("product", "date")
        constraints = [
            models.UniqueConstraint(fields=['product', 'date'], name='unique_product_date')
        ]
    def __str__(self):
        return f"Analytics for {self.product.title} - {self.date}"
