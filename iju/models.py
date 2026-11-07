import os

import uuid
from django.db import models
from django_ckeditor_5.fields import CKEditor5Field

from iju.utils.image import MAX_HEIGHT, generate_image_store_renditions
from iju.validators.image_upload_validator import validate_image
from iju_site import settings


class ImageStore(models.Model):

    uuid = models.UUIDField(primary_key=True, default=uuid.uuid4)
    image = models.ImageField(
        upload_to=settings.IMAGE_STORE_UPLOAD_TO,
        help_text="Оригинал изображения (сохраняется в исходном формате, max 10 MB, 4000px).",
        validators=[validate_image],
    )
    caption = models.TextField(
        blank=True,
        help_text="Подпись изображения.",
    )
    source_text = models.CharField(
        max_length=255,
        blank=True,
        help_text="Текстовая ссылка на источник изображения (автор, издание и т.п.).",
    )
    source_url = models.URLField(
        blank=True,
        help_text="URL источника изображения.",
    )
    renditions = models.JSONField(
        default=dict,
        blank=True,
        editable=False,
        verbose_name="Производные изображения",
    )
    created = models.DateTimeField(auto_now_add=True)
    modified = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        generate_image_store_renditions(self)

    class Meta:
        verbose_name = "Изображение"
        verbose_name_plural = "Изображения"


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
    image = models.ImageField(
        upload_to='article_images/',
        blank=True,
        null=True,
    )
    publish = models.BooleanField()
    created = models.DateTimeField(auto_now_add=True)
    modified = models.DateTimeField(auto_now_add=True)
    publicated = models.DateTimeField(auto_now_add=True)
    time_to_read = models.IntegerField()
    slug = models.SlugField(unique=True)

