import os

import uuid
from django.db import models
from django_ckeditor_5.fields import CKEditor5Field

from iju.utils.image import MAX_HEIGHT, resize_image_to_max_height
from iju.validators.image_upload_validator import validate_image


class ImageStore(models.Model):

    uuid = models.UUIDField(primary_key=True, default=uuid.uuid4)
    image = models.ImageField(
        upload_to="image_store/",
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

    def save(self, *args, **kwargs):
        # Масштабирование картинки при загрузке (Django Admin, ModelForm, shell и т.д.)
        image = self.image
        # _committed == False означает, что файл только что загружен и ещё не сохранён в storage
        if image and not image._committed:
            try:
                needs_resize = image.height > MAX_HEIGHT
            except OSError:
                needs_resize = False
            if needs_resize:
                content = resize_image_to_max_height(image)
                image.save(os.path.basename(image.name), content, save=False)

        super().save(*args, **kwargs)

