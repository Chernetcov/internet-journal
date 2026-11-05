import tempfile
from io import BytesIO

from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from PIL import Image

from iju.models import Article, Category

MEDIA_ROOT = tempfile.mkdtemp()


def make_uploaded_image(width, height, name="image.jpg", image_format="JPEG"):
    """Готовит загружаемый файл-картинку нужного размера."""
    buffer = BytesIO()
    Image.new("RGB", (width, height), color="red").save(buffer, format=image_format)
    return SimpleUploadedFile(
        name,
        buffer.getvalue(),
        content_type="image/jpeg" if image_format == "JPEG" else "image/png",
    )


@override_settings(MEDIA_ROOT=MEDIA_ROOT)
class ArticleImageResizeTest(TestCase):
    def setUp(self):
        self.category = Category.objects.create(
            name="Тест",
            description="",
            slug="test",
        )

    def create_article(self, image):
        return Article.objects.create(
            category=self.category,
            title="Тест",
            description="Тест",
            content="<p>Тест</p>",
            image=image,
            publish=True,
            time_to_read=5,
            slug="test-article",
        )

    def get_saved_size(self, article):
        article.refresh_from_db()
        with article.image.open() as opened:
            size = Image.open(opened).size
        return size

    def test_tall_image_is_scaled_down_to_680(self):
        """Портретная картинка 800x2400 становится высотой 680px с сохранением пропорций."""
        article = self.create_article(make_uploaded_image(800, 2400, "tall.jpg"))

        width, height = self.get_saved_size(article)

        self.assertEqual(height, 680)
        self.assertEqual(width, round(800 * 680 / 2400))  # 227
        self.assertTrue(article.image.storage.exists(article.image.name))

    def test_wide_image_is_scaled_down_to_680(self):
        """Широкая картинка 2000x1000 тоже ограничивается по высоте до 680px."""
        article = self.create_article(make_uploaded_image(2000, 1000, "wide.jpg"))

        width, height = self.get_saved_size(article)

        self.assertEqual(height, 680)
        self.assertEqual(width, round(2000 * 680 / 1000))  # 1360

    def test_small_image_is_not_upscaled(self):
        """Картинка ниже 680px не увеличивается и не изменяется."""
        article = self.create_article(make_uploaded_image(200, 300, "small.jpg"))

        self.assertEqual(self.get_saved_size(article), (200, 300))

    def test_image_exactly_680_is_untouched(self):
        """Картинка высотой ровно 680px остаётся как есть."""
        article = self.create_article(make_uploaded_image(1000, 680, "exact.jpg"))

        self.assertEqual(self.get_saved_size(article), (1000, 680))

    def test_resave_does_not_duplicate_or_shrink_again(self):
        """Повторное сохранение статьи не создаёт новый файл и не меняет размер."""
        article = self.create_article(make_uploaded_image(800, 2400, "tall.jpg"))
        saved_name = article.image.name

        article.title = "Новый заголовок"
        article.save()

        article.refresh_from_db()
        self.assertEqual(article.image.name, saved_name)
        self.assertEqual(self.get_saved_size(article), (round(800 * 680 / 2400), 680))
