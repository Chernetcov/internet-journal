import os
import re
import shutil

import uuid
from urllib.parse import unquote, urlsplit

from django.conf import settings as django_settings
from django.db import models
from django.db.models.signals import post_delete, post_save, pre_save
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
                  f"{settings.IMAGE_STORE_ORIGIN_MAX_SIZE / 1024 / 1024} MB, "
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

    @property
    def srcset(self):
        """Строка для атрибута ``srcset``: URL превью с дескрипторами ширины."""
        if not self.renditions:
            return ""
        storage = self.image.storage
        items = []
        for width, path in sorted(self.renditions.items(), key=lambda item: int(item[0])):
            items.append(f"{storage.url(path)} {width}w")
        return ", ".join(items)

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

    class Meta:
        verbose_name = "Рубрика"
        verbose_name_plural = "Рубрики"

    def __str__(self):
        return self.name


class Article(models.Model):
    category = models.ForeignKey(Category, on_delete=models.CASCADE)
    title = models.CharField(max_length=128)
    description = models.TextField()
    content = CKEditor5Field(config_name="article", )
    image = models.ForeignKey(ImageStore, on_delete=models.SET_NULL, null=True)
    publish = models.BooleanField()
    created = models.DateTimeField(auto_now_add=True)
    modified = models.DateTimeField(auto_now_add=True)
    publicated = models.DateTimeField(auto_now_add=True)
    time_to_read = models.IntegerField()
    slug = models.SlugField(unique=True)

    class Meta:
        verbose_name = "Статья"
        verbose_name_plural = "Статьи"

    def __str__(self):
        return self.title


_IMG_SRC_RE = re.compile(
    r"""<img\b[^>]*?\ssrc\s*=\s*["']([^"']+)["']""",
    re.IGNORECASE,
)


def extract_content_image_urls(content):
    """Возвращает множество URL изображений из HTML-контента статьи."""
    if not content:
        return set()
    return {match.group(1) for match in _IMG_SRC_RE.finditer(content)}


def image_store_name_from_url(url):
    """Преобразует URL изображения в путь файла внутри ``MEDIA_ROOT``.

    Возвращает ``None``, если URL не относится к медиафайлам.
    """
    media_url = urlsplit(django_settings.MEDIA_URL).path
    if not media_url.endswith("/"):
        media_url = f"{media_url}/"

    path = unquote(urlsplit(url).path)
    if not path.startswith(media_url):
        return None
    return path[len(media_url):].lstrip("/")


def delete_unused_image_stores(urls):
    """Удаляет ``ImageStore``, на которые больше нет ссылок.

    Изображение не удаляется, если оно используется как обложка статьи,
    изображение категории или всё ещё встречается в контенте любой статьи.
    """
    names = {
        name
        for url in urls
        if (name := image_store_name_from_url(url))
    }
    if not names:
        return

    for image_store in ImageStore.objects.filter(image__in=names):
        if Category.objects.filter(image=image_store).exists():
            continue
        if Article.objects.filter(image=image_store).exists():
            continue
        # Проверяем и текущую статью: изображение могло остаться в контенте,
        # но быть записано в HTML в другом виде.
        if Article.objects.filter(content__contains=image_store.image.url).exists():
            continue
        image_store.delete()


@receiver(pre_save, sender=Article)
def remember_removed_article_images(sender, instance, **kwargs):
    """Запоминает удалённые из контента изображения до сохранения статьи."""
    instance._removed_content_image_urls = set()
    if kwargs.get("raw") or instance._state.adding or not instance.pk:
        return

    old_content = (
        sender.objects.filter(pk=instance.pk)
        .values_list("content", flat=True)
        .first()
    )
    if old_content is None:
        return

    instance._removed_content_image_urls = (
            extract_content_image_urls(old_content)
            - extract_content_image_urls(instance.content)
    )


@receiver(post_save, sender=Article)
def delete_removed_article_images(sender, instance, **kwargs):
    """Удаляет из ``ImageStore`` изображения, убранные из контента статьи."""
    if kwargs.get("raw"):
        return

    removed_urls = getattr(instance, "_removed_content_image_urls", set())
    instance._removed_content_image_urls = set()
    if removed_urls:
        delete_unused_image_stores(removed_urls)


@receiver(post_delete, sender=Article)
def delete_article_content_images(sender, instance, **kwargs):
    """Удаляет изображения контента при удалении статьи."""
    delete_unused_image_stores(extract_content_image_urls(instance.content))
