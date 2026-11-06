from django.conf import settings
from django.core.exceptions import ValidationError

from PIL import Image, UnidentifiedImageError


def validate_image(file):
    if file.size > settings.IMAGE_STORE_ORIGIN_MAX_SIZE:
        raise ValidationError(
            f"Размер изображения не должен превышать {settings.IMAGE_STORE_ORIGIN_MAX_SIZE / 1024 / 1024 } MB."
        )

    try:
        file.seek(0)

        with Image.open(file) as image:
            if image.format not in settings.IMAGE_STORE_SUPPORTED_FORMATS:
                raise ValidationError(
                    "Допустимые форматы: JPG, PNG, WebP."
                )

            width, height = image.size

            if width > settings.IMAGE_STORE_ORIGIN_MAX_WIDTH:
                raise ValidationError(
                    f"Ширина изображения не должна превышать "
                    f"{settings.IMAGE_STORE_ORIGIN_MAX_WIDTH} px."
                )

            if height > settings.IMAGE_STORE_ORIGIN_MAX_HEIGHT:
                raise ValidationError(
                    f"Высота изображения не должна превышать "
                    f"{settings.IMAGE_STORE_ORIGIN_MAX_HEIGHT} px."
                )

            image.verify()

    except (UnidentifiedImageError, OSError):
        raise ValidationError("Некорректный файл изображения.")

    finally:
        file.seek(0)