import shutil
import tempfile
from datetime import datetime
from io import BytesIO
from pathlib import Path

from django.conf import settings
from django.core.files.base import ContentFile
from django.test import TestCase, override_settings
from PIL import Image

from iju.models import ImageStore

# Временный каталог для MEDIA_ROOT тестовой среды
TEST_DIR = tempfile.mkdtemp(prefix="iju-test-media-")

@override_settings(MEDIA_ROOT=TEST_DIR)
class ImageStoreTestBase(TestCase):
    """Базовый класс для тестирования с использованием ImageStore"""
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        Path(TEST_DIR).mkdir(parents=True, exist_ok=True)

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEST_DIR, ignore_errors=True)

    @staticmethod
    def _make_jpeg(width=2000, height=1200):
        buffer = BytesIO()
        Image.new("RGB", (width, height), (120, 80, 200)).save(
            buffer, format="JPEG"
        )
        return ContentFile(buffer.getvalue(), name="source.jpeg")


class ImageStoreUploadTest(ImageStoreTestBase):
    """Успешная загрузка изображения в ImageStore."""

    def test_upload_image_creates_original_and_renditions(self):
        instance = ImageStore.objects.create(
            image = self._make_jpeg(),
            caption="Тестовое изображение"
        )

        now = datetime.now()
        media_dir = (
            Path(TEST_DIR)
            / settings.IMAGE_STORE_UPLOAD_TO.strip("/")
            / f"{now:%Y}"
            / f"{now:%m}"
            / f"{now:%d}"
            / str(instance.uuid)
        )

        # Оригинал и все превью сохранены по пути с текущей датой
        self.assertTrue((media_dir / "original.jpeg").is_file())
        for physical_width, _, _ in settings.IMAGE_STORE_PREVIEWS:
            self.assertTrue(
                (media_dir / f"{physical_width}.webp").is_file(),
                msg=f"Не найдено превью {physical_width}.webp",
            )

        # renditions ссылается на реально существующие файлы
        expected_prefix = (
            f"{settings.IMAGE_STORE_UPLOAD_TO.strip('/')}/"
            f"{now:%Y}/{now:%m}/{now:%d}/{instance.uuid}/"
        )
        self.assertEqual(
            set(instance.renditions),
            {str(width) for _, width, _ in settings.IMAGE_STORE_PREVIEWS},
        )
        for physical_width, _, _ in settings.IMAGE_STORE_PREVIEWS:
            rendition_path = instance.renditions[str(physical_width)]
            self.assertEqual(
                rendition_path, f"{expected_prefix}{physical_width}.webp"
            )
            self.assertTrue((Path(TEST_DIR) / rendition_path).is_file())

        self.assertEqual(
            instance.image.name, f"{expected_prefix}original.jpeg"
        )

    def test_delete_image_removes_directory(self):
        instance = ImageStore(caption="Изображение для удаления")
        instance.image = self._make_jpeg()
        instance.save()

        now = datetime.now()
        image_dir = (
            Path(TEST_DIR)
            / settings.IMAGE_STORE_UPLOAD_TO.strip("/")
            / f"{now:%Y}"
            / f"{now:%m}"
            / f"{now:%d}"
            / str(instance.uuid)
        )

        # После загрузки создана папка с именем, равным uuid объекта
        self.assertTrue(image_dir.is_dir(), msg=f"Нет каталога {image_dir}")
        self.assertEqual(image_dir.name, str(instance.uuid))

        instance.delete()

        # После удаления объекта папка с его uuid удалена
        self.assertFalse(image_dir.exists(), msg=f"Каталог {image_dir} не удалён")
