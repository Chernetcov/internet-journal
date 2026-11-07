import os
from io import BytesIO
from datetime import datetime

from django.conf import settings
from django.core.files.base import ContentFile
from django.core.files.storage import default_storage
from PIL import Image, ImageOps, UnidentifiedImageError

# Максимально допустимая высота загружаемого изображения (в пикселях)
MAX_HEIGHT = 680

# Форматы, которые не поддерживают прозрачность
_NO_ALPHA_FORMATS = {"JPEG", "BMP"}


def generate_image_store_renditions(instance):
    """Генерирует уменьшенные WebP-копии изображения ImageStore.

    Файл перемещается из исходного места в структуру
    ``settings.IMAGE_STORE_UPLOAD_TO/<год>/<месяц>/<день>/<uuid>/``.
    Для указанного в ``settings.IMAGE_STORE_PREVIEWS`` набора ширинок создаются копии в
    формате ``settings.IMAGE_STORE_PREVIEWS_FORMAT`` (по умолчанию WebP)
    с качеством ``settings.IMAGE_STORE_PREVIEWS_QUALITY``. Пути к
    превью сохраняются в поле ``instance.renditions``.

    Работает один раз: если ``instance.renditions`` уже заполнено, выполнение
    пропускается (модель сохраняет ``renditions`` без изменений).
    """
    if not hasattr(instance, "image") or not instance.image:
        return
    # Если превью уже сгенерированы и сохранены в БД, повторная обработка не нужна
    if instance.renditions:
        return

    storage = getattr(instance, "_storage", default_storage)
    renditions = {}
    original_path = instance.image.name
    ext = os.path.splitext(original_path)[1].lstrip(".")

    # Каталог хранения берем из настроек (как и upload_to модели ImageStore),
    # дату -- по времени сохранения записи.
    now = datetime.now()
    base_path = settings.IMAGE_STORE_UPLOAD_TO.strip("/")
    media_path = f"{now:%Y}/{now:%m}/{now:%d}/{instance.uuid}/"
    storage_path = f"{base_path}/{media_path}" if base_path else media_path

    try:
        with storage.open(original_path, "rb") as f:
            content = ContentFile(f.read())
            original_dest = f"{storage_path}original.{ext}"
            if storage.exists(original_dest):
                storage.delete(original_dest)
            storage.save(original_dest, content)
    except (UnidentifiedImageError, OSError):
        return
    storage.delete(original_path)
    instance.image.storage = storage
    instance.image.name = f"{storage_path}original.{ext}"

    # Открываем оригинал для создания превью
    try:
        with storage.open(f"{storage_path}original.{ext}", "rb") as f:
            image = Image.open(f)
            image = ImageOps.exif_transpose(image)
            width, height = image.size
            preview_format = settings.IMAGE_STORE_PREVIEWS_FORMAT.upper()
            if preview_format in ("WEBP", "JPEG", "PNG"):
                if preview_format == "WEBP" and image.mode in ("RGBA", "LA"):
                    image = image.convert("RGB")
                elif preview_format == "JPEG" and image.mode not in ("RGB", "L"):
                    image = image.convert("RGB")

                for css_width, physical_width, quality in settings.IMAGE_STORE_PREVIEWS:
                    if physical_width >= width:
                        continue
                    new_width = physical_width
                    new_height = max(1, round(height * physical_width / width))
                    resized = image.resize((new_width, new_height), Image.LANCZOS)
                    buffer = BytesIO()
                    save_kwargs = {"quality": settings.IMAGE_STORE_PREVIEWS_QUALITY}
                    if preview_format == "WEBP":
                        save_kwargs["optimize"] = True
                    resized.save(buffer, format=preview_format, **save_kwargs)

                    file_name = f"{physical_width}.{preview_format.lower()}"
                    rendition_path = f"{storage_path}{file_name}"
                    rendition_file = ContentFile(buffer.getvalue(), name=file_name)
                    if storage.exists(rendition_path):
                        storage.delete(rendition_path)
                    storage.save(rendition_path, rendition_file)
                    renditions[str(physical_width)] = rendition_path
    except (UnidentifiedImageError, OSError):
        return

    instance.renditions = renditions

