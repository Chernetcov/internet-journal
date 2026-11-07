import os
import shutil

import uuid
from django.db import models
from django.db.models.signals import post_delete
from django.dispatch import receiver
from django_ckeditor_5.fields import CKEditor5Field

from iju.utils.image import MAX_HEIGHT, generate_image_store_renditions
from iju.validators.image_upload_validator import validate_image
from iju_site import settings


class ImageStore(models.Model):

    uuid = models.UUIDField(primary_key=True, default=uuid.uuid4)
    image = models.ImageField(
        upload_to=settings.IMAGE_STORE_UPLOAD_TO,
        help_text=f"Оригинал изображения (сохраняется в исходном формате, max "
                  f"{settings.IMAGE_STORE_ORIGIN_MAX_SIZE / 1024 /1024} MB, "
                  f"{settings.IMAGE_STORE_ORIGIN_MAX_HEIGHT}px).",
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
        # После переноса оригинала и генерации превью сохраняем новые пути,
        # чтобы они были доступны при последующем удалении объекта.
        if generate_image_store_renditions(self):
            super().save(update_fields=["image", "renditions"])

    class Meta:
        verbose_name = "Изображение"
        verbose_name_plural = "Изображения"


@receiver(post_delete, sender=ImageStore)
def delete_image_store_files(sender, instance, **kwargs):
    """Удаляет оригинал, превью и каталог с ними из хранилища.

    Срабатывает при удалении как одиночного объекта, так и через
    ``QuerySet.delete()`` (например, массовое удаление в админке).
    """
    if not instance.image:
        return

    storage = instance.image.storage

    # Удаляем каталог, в котором лежали оригинал и превью
    directory = os.path.dirname(instance.image.name)
    if not directory:
        return
    try:
        directory_path = storage.path(directory)
    except (AttributeError, NotImplementedError):
        # Хранилище не поддерживает работу с файловой системой
        return
    shutil.rmtree(directory_path, ignore_errors=True)


class Category(models.Model):
    name = models.CharField(max_length=100)
    image = models.ForeignKey(ImageStore, on_delete=models.SET_NULL, null=True)
    description = models.TextField()
    slug = models.SlugField(unique=True)


class Article(models.Model):
    category = models.ForeignKey(Category, on_delete=models.CASCADE)
    title = models.CharField(max_length=128)
    description = models.TextField()
    content = CKEditor5Field(config_name="article",)
    image = models.ForeignKey(ImageStore, on_delete=models.SET_NULL, null=True)
    publish = models.BooleanField()
    created = models.DateTimeField(auto_now_add=True)
    modified = models.DateTimeField(auto_now_add=True)
    publicated = models.DateTimeField(auto_now_add=True)
    time_to_read = models.IntegerField()
    slug = models.SlugField(unique=True)

