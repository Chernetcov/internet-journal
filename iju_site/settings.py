import os
from pathlib import Path
import environ


# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

env = environ.Env()
environ.Env.read_env(BASE_DIR / '.env', overwrite=True)

# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/3.2/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = 'django-insecure-g&9r8i36p*li!xyxz-&zx5k+906_!!iz(5n819$$1zsm#wk-$j'

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

ALLOWED_HOSTS = []


# Application definition

DJANGO_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django_extensions',
]

THIRD_PARTY_APPS = [
    'django_tailwind_cli',
    'django_ckeditor_5',
]

LOCAL_APPS = [
    'iju.apps.IjuConfig',
]

INSTALLED_APPS = DJANGO_APPS + THIRD_PARTY_APPS + LOCAL_APPS

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'iju_site.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'iju_site.wsgi.application'


# Database
# https://docs.djangoproject.com/en/3.2/ref/settings/#databases

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": env("POSTGRES_DB", default="iju"),
        "USER": env("POSTGRES_USER", default="postgres"),
        "PASSWORD": env("POSTGRES_PASSWORD", default=""),
        "HOST": env("POSTGRES_HOST", default="localhost"),
        "PORT": env("POSTGRES_PORT", default="5432"),
        # Переиспользование соединений
        "CONN_MAX_AGE": 60,
        # Проверка соединения перед повторным использованием
        "CONN_HEALTH_CHECKS": True,
        "OPTIONS": {
            "connect_timeout": 10,
            "options": "-c statement_timeout=30000",
        },
    }
}


# Password validation
# https://docs.djangoproject.com/en/3.2/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]


# Internationalization
# https://docs.djangoproject.com/en/3.2/topics/i18n/

LANGUAGE_CODE = 'ru'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_L10N = True
USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/3.2/howto/static-files/

STATIC_URL = '/static/'

MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')

# Default primary key field type
# https://docs.djangoproject.com/en/3.2/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

STATICFILES_DIRS = [BASE_DIR / 'assets']
TAILWIND_CLI_VERSION = '4.3.3'
TAILWIND_CLI_SRC_CSS = 'styles/main.css'

# ---------------------------------------------------------------------------
# ImageStore -- загрузка изображений и генерация копий для srcset
# ---------------------------------------------------------------------------

#: Папка внутри MEDIA_ROOT для изображений ImageStore
IMAGE_STORE_UPLOAD_TO = "images/"

#: Максимальный размер загружаемого файла (байты) -- 10 MB
IMAGE_STORE_ORIGIN_MAX_SIZE = 10485760

#: Максимальные размеры оригинала ПОСЛЕ сжатия (пиксели).
#: По умолчанию равны IMAGE_STORE_ORIGIN_MAX_DIMENSION.
IMAGE_STORE_ORIGIN_MAX_WIDTH = 8000
IMAGE_STORE_ORIGIN_MAX_HEIGHT = 8000

#: Допустимые форматы загрузки (не чувствительно к регистру).
IMAGE_STORE_SUPPORTED_FORMATS = ('JPEG', 'PNG', 'WEBP')

# ---------------------------------------------------------------------------
# Предварительно обработанные копии WebP для srcset / ретины
# ---------------------------------------------------------------------------

#: Список кортежей (css-ширина, физическая ширина пикселей, качество).
#: css-ширина используется в_sizes_, физическая ширина -- дескриптор в srcset.
#: Копии квадратные по дескриптору, высота выводится из пропорций оригинала.
IMAGE_STORE_PREVIEWS = (
    (1920, 1920, 80),   # десктоп
    (1440, 1440, 85),   # обычный экран
    (768, 768, 85),     # планшет
    (375, 375, 90),     # мобильный
)

#: Формат копий
IMAGE_STORE_PREVIEWS_FORMAT = 'WEBP'

#: Качество копий
IMAGE_STORE_PREVIEWS_QUALITY = 80

# Загрузка изображений из CKEditor 5 идёт в ImageStore через собственное
# представление iju.views.ckeditor_image_upload.
CK_EDITOR_5_UPLOAD_FILE_VIEW_NAME = "ckeditor_image_upload"
CKEDITOR_5_CONFIGS = {
    'article': {
        'toolbar': {
            'items': [
                'heading',
                '|',
                "style",
                '|',
                'bold',
                'italic',
                'link',
                'bulletedList',
                'numberedList',
                '|',
                'blockQuote',
                'imageUpload',
                'insertTable',
                'undo',
                'redo',
            ],
        },
        "style": {
            "definitions": [
                {
                    "name": "С буквицей",
                    "element": "p",
                    "classes": ["drop-cap"],
                },
            ],
        },
        'heading': {
            'options': [
                {
                    'model': 'paragraph',
                    'title': 'Paragraph',
                    'class': 'ck-heading_paragraph',
                },
                {
                    'model': 'heading2',
                    'view': 'h2',
                    'title': 'Heading 2',
                    'class': 'ck-heading_heading2',
                },
                {
                    'model': 'heading3',
                    'view': 'h3',
                    'title': 'Heading 3',
                    'class': 'ck-heading_heading3',
                },
            ]
        },
        "htmlSupport": {
            "allow": [
                {
                    "name": "p",
                    "classes": [
                        "drop-cap",
                    ],
                },
            ],
        },
    },
}
CKEDITOR_5_FILE_UPLOAD_PERMISSION = "staff"
# Штатная очистка django-ckeditor-5 удаляет файлы по basename в хранилище
# CKEDITOR_5_FILE_STORAGE и не учитывает структуру каталогов ImageStore.
# Поэтому она отключена, чтобы не удалять чужие файлы. Очистка изображений
# контента выполняется в iju.models (сигналы Article).
CKEDITOR_5_IMAGE_CLEANUP = False