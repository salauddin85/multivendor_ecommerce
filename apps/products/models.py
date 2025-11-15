# # apps/products/models.py

# from django.db import models
# from django.utils.text import slugify
# from apps.catalog.models import Category, Brand
# from stores.models import Store


# class Product(models.Model):
#     TYPE = (("simple", "Simple"), ("variable", "Variable"))
#     STATUS = (
#         ("draft", "Draft"),
#         ("pending", "Pending Approval"),
#         ("published", "Published"),
#         ("rejected", "Rejected"),
#     )

#     store = models.ForeignKey(Store, on_delete=models.CASCADE, related_name="products")
#     category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True)
#     brand = models.ForeignKey(Brand, on_delete=models.SET_NULL, null=True, blank=True)
#     title = models.CharField(max_length=500)
#     slug = models.SlugField(unique=True)
#     type = models.CharField(max_length=20, choices=TYPE, default="simple")
#     description = models.TextField(blank=True)
#     base_price = models.DecimalField(max_digits=10, decimal_places=2)
#     main_image = models.CharField(max_length=500, null=True, blank=True)
#     gallery = models.JSONField(default=list)
#     stock = models.IntegerField(default=0)
#     status = models.CharField(max_length=20, choices=STATUS, default="draft")
#     is_featured = models.BooleanField(default=False)
#     view_count = models.IntegerField(default=0)
#     avg_rating = models.DecimalField(max_digits=3, decimal_places=2, default=0)
#     created_at = models.DateTimeField(auto_now_add=True)


#     def save(self, *args, **kwargs):
#         if not self.slug:
#             self.slug = slugify(self.title)
#         super().save(*args, **kwargs)


# class ProductAttribute(models.Model):
#     product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="attributes")
#     name = models.CharField(max_length=100)
#     is_variation = models.BooleanField(default=True)

    


# class ProductAttributeValue(models.Model):
#     attribute = models.ForeignKey(ProductAttribute, on_delete=models.CASCADE, related_name="values")
#     value = models.CharField(max_length=100)
#     color_code = models.CharField(max_length=20, null=True, blank=True)

    

# class ProductVariant(models.Model):
#     product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="variants")
#     sku = models.CharField(max_length=50, unique=True)
#     variant_name = models.CharField(max_length=255)
#     price = models.DecimalField(max_digits=10, decimal_places=2)
#     discount_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
#     stock = models.IntegerField(default=0)
#     image = models.CharField(max_length=500, blank=True, null=True)


# class ProductVariantAttribute(models.Model):
#     variant = models.ForeignKey(ProductVariant, on_delete=models.CASCADE, related_name="variant_attrs")
#     attribute = models.ForeignKey(ProductAttribute, on_delete=models.CASCADE)
#     value = models.ForeignKey(ProductAttributeValue, on_delete=models.CASCADE)

#     class Meta:
#         unique_together = ("variant", "attribute")
