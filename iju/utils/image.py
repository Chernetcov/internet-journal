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


def resize_image_to_max_height(image_file):
    """Масштабирует изображение так, чтобы его высота не превышала MAX_HEIGHT px.

    Пропорции сохраняются, изображение не растягивается (маленькие картинки
    не увеличиваются). Формат исходного файла сохраняется.

    Возвращает ContentFile с тем же именем, что и исходный файл.
    """
    original_name = getattr(image_file, "name", "") or ""
    file_name = os.path.basename(original_name) or "image"

    if hasattr(image_file, "seek"):
        image_file.seek(0)

    image = Image.open(image_file)
    original_format = image.format or "JPEG"

    # Учитываем EXIF-ориентацию (иначе фото с телефона могут оказаться "лежащими")
    image = ImageOps.exif_transpose(image)

    if image.height > MAX_HEIGHT:
        new_height = MAX_HEIGHT
        new_width = max(1, round(image.width * MAX_HEIGHT / image.height))
        image = image.resize((new_width, new_height), Image.LANCZOS)

    if original_format in _NO_ALPHA_FORMATS and image.mode not in ("RGB", "L"):
        image = image.convert("RGB")

    buffer = BytesIO()
    save_kwargs = {"quality": 85, "optimize": True} if original_format == "JPEG" else {}
    image.save(buffer, format=original_format, **save_kwargs)

    return ContentFile(buffer.getvalue(), name=file_name)


def generate_image_store_renditions(instance):
    """Генерирует уменьшенные WebP-копии изображения ImageStore.

    Файл перемещается из ``image_store/<uuid>/<имя>`` в структуру
    ``image_store/<год>/<месяц>/<день>/<uuid>/``. Для указанного в
    ``settings.IMAGE_STORE_PREVIEWS`` набора ширинок создаются копии в
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

    # Разбираем дату из пути загруженного оригинала (формат ``image_store/
    # <uuid>/<имя>.<ext>``), для каталогов используем время сохранения записи.
    now = datetime.now()
    media_path = f"{now:%Y}/{now:%m}/{now:%d}/{instance.uuid}/"
    storage_path = f"image_store/{media_path}"

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
                    rendition_path = f"images/{media_path}{file_name}"
                    rendition_file = ContentFile(buffer.getvalue(), name=file_name)
                    if storage.exists(f"image_store/{media_path}{file_name}"):
                        storage.delete(f"image_store/{media_path}{file_name}")
                    storage.save(f"image_store/{media_path}{file_name}", rendition_file)
                    renditions[str(physical_width)] = rendition_path
    except (UnidentifiedImageError, OSError):
        return

    instance.renditions = renditions

