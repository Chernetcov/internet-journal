from django.urls import reverse

from iju.models import ImageStore
from iju.tests.test_image_store import ImageStoreTestBase


class ImageStoreUploadTest(ImageStoreTestBase):
    def test_image_store_list_view(self):
        image_one = ImageStore.objects.create(
            image = self._make_jpeg(),
            caption="Тестовое изображение"
        )
        image_two = ImageStore.objects.create(
            image = self._make_jpeg(),
            caption="Тестовое изображение 2"
        )

        url = reverse("images")
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.headers['Content-Type'], 'application/json')
        json_data = response.json()
        self.assertEqual(json_data['count'], 2)
        result_array = json_data['results']
        self.assertEqual(result_array[0]['caption'], image_two.caption)
        self.assertEqual(result_array[1]['caption'], image_one.caption)