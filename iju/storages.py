import os
from urllib.parse import urljoin

from django.conf import settings
from django.core.files.storage import FileSystemStorage


class ArticleImageStorage(FileSystemStorage):
    location = os.path.join(settings.MEDIA_ROOT, "article_images")
    base_url = urljoin(settings.MEDIA_URL, "articles/")