from django.db import models
from django.conf import settings
from django.utils.text import slugify
from apps.authentication.models import StoreOwner,Vendor
from .constants.store_choices import TYPE_CHOICES, STATUS_CHOICES



class StoreBaseModel(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True
        

class CommissionRate(models.Model):
    store_type = models.CharField(max_length=20, choices=TYPE_CHOICES)  # vendor / company
    rate = models.DecimalField(max_digits=5, decimal_places=2)


class Store(StoreBaseModel):
    """Store/Shop model for vendors and companies"""
    
    store_owner = models.ForeignKey(StoreOwner, on_delete=models.CASCADE, related_name='store_owner_stores',null=True,blank=True)
    vendor = models.ForeignKey(Vendor, on_delete=models.CASCADE, related_name='vendor_stores',null=True,blank=True)
    store_name = models.CharField(max_length=255, unique=True,default='')
    slug = models.SlugField(max_length=255, unique=True)
    type = models.CharField(max_length=20, choices=TYPE_CHOICES,default='company')
    logo = models.ImageField(upload_to='store_logos/', blank=True, null=True)
    banner = models.ImageField(upload_to='store_banners/', blank=True, null=True)
    address = models.CharField(max_length=255,default='')
    description = models.TextField(default='')
    is_verified = models.BooleanField(default=False)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    
    
    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.store_name)
        
        if not self.store_owner and not self.vendor:
            raise ValueError("Either store_owner or vendor must be set to create a store object")
        
        super().save(*args, **kwargs)
    
    def __str__(self):
        return self.store_name



class StoreAnalytics(StoreBaseModel):
    store = models.OneToOneField(
        Store, 
        on_delete=models.CASCADE, 
        related_name='analytics'
    )

    # Views / Traffic
    views_count = models.PositiveIntegerField(default=0)

    # Product stats
    products_count = models.PositiveIntegerField(default=0)

    # Sales stats
    orders_count = models.PositiveIntegerField(default=0)
    total_sold_quantity = models.PositiveIntegerField(default=0)
    total_revenue = models.DecimalField(max_digits=12, decimal_places=2, default=0)

    # Ratings
    average_rating = models.DecimalField(max_digits=3, decimal_places=2, default=0)
    total_reviews = models.PositiveIntegerField(default=0)

    # Followers (optional)
    followers_count = models.PositiveIntegerField(default=0)

    def __str__(self):
        return f"Analytics for {self.store.store_name}"
