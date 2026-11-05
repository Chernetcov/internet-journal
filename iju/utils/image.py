import os
from io import BytesIO

from django.core.files.base import ContentFile
from PIL import Image, ImageOps

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
