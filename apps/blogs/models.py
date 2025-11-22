from django.db import models
from apps.authentication.models import CustomUser



class BlogBaseModel(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    class Meta:
        abstract = True

class Category(BlogBaseModel):
    name = models.CharField(max_length=80, unique=True)

    def __str__(self):
        return self.name

class Tag(BlogBaseModel):
    name = models.CharField(max_length=50, unique=True)

    def __str__(self):
        return self.name

class Blog(BlogBaseModel):
    
    title = models.CharField(max_length=200)
    author = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name="blog_posts")
    featured_image = models.ImageField(upload_to="blog/featured_images/", null=True, blank=True)
    summary     = models.TextField(blank=True)
    content    = models.TextField(blank=True, null=True)
    category    = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, related_name="posts")
    tags        = models.ManyToManyField(Tag, blank=True, related_name="blog_tags")

    class Meta:
        ordering = ["-created_at"]
        
    
    
    def __str__(self):
        return self.title
