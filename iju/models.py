from django.db import models
from django_ckeditor_5.fields import CKEditor5Field

# Create your models here.
class Category(models.Model):
    name = models.CharField(max_length=100)
    image = models.ImageField(upload_to='category_images/')
    description = models.TextField()
    slug = models.SlugField(unique=True)


class Article(models.Model):
    category = models.ForeignKey(Category, on_delete=models.CASCADE)
    title = models.CharField(max_length=128)
    description = models.TextField()
    content = CKEditor5Field(config_name="article",)
    image = models.ImageField(upload_to='article_images/')
    publish = models.BooleanField()
    created = models.DateTimeField(auto_now_add=True)
    modified = models.DateTimeField(auto_now_add=True)
    publicated = models.DateTimeField(auto_now_add=True)
    time_to_read = models.IntegerField()
    slug = models.SlugField(unique=True)

