from urllib.parse import urlencode

from django.core.exceptions import ValidationError
from django.core.paginator import Paginator
from django.http import HttpResponse, JsonResponse
from django.shortcuts import render
from django.template import loader
from django.views import generic
from django.views.decorators.http import require_POST
from django_ckeditor_5.permissions import check_upload_permission

from iju.models import Article, Category, ImageStore

#: Размер страницы по умолчанию и максимум для эндпоинта списка изображений.
IMAGE_STORE_PAGE_SIZE = 20
IMAGE_STORE_MAX_PAGE_SIZE = 100


def index(request):
    context = {
        'categories': Category.objects.all(),
        'latest_articles': Article.objects.all().order_by("-publicated")[:4],
    }
    return render(request, 'index.html', context)


def category(request, category_id):
    return HttpResponse(f"Category page id: {category_id}")


class ArticleListView(generic.ListView):
    template_name = "articles.html"
    context_object_name = "articles"

    def get_queryset(self):
        """Return the last 15 published articles, optionally filtered by category."""
        queryset = Article.objects.filter(publish=True)
        category = self.request.GET.get("category", "").strip()
        if category:
            queryset = queryset.filter(category__slug=category)
        return queryset.order_by("-publicated")[:15]

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["categories"] = Category.objects.all()
        context["category"] = self.request.GET.get("category", "").strip()
        return context


class ArticleView(generic.DetailView):
    model = Article
    template_name = "article.html"
    context_object_name = "article"


def about(request):
    return render(request, 'about.html')


def _positive_int_param(request, name, default, maximum=None):
    """Возвращает положительный целочисленный GET-параметр.

    Бросает ``ValueError``, если значение не является положительным числом
    или превышает ``maximum``.
    """
    raw = request.GET.get(name)
    if raw in (None, ""):
        return default
    try:
        value = int(raw)
    except (TypeError, ValueError):
        raise ValueError(f"Параметр «{name}» должен быть целым числом.")
    if value < 1:
        raise ValueError(f"Параметр «{name}» должен быть больше нуля.")
    if maximum is not None and value > maximum:
        raise ValueError(f"Параметр «{name}» не может быть больше {maximum}.")
    return value


def _image_store_payload(image):
    """Сериализует ``ImageStore`` для JSON-ответа."""
    return {
        "uuid": str(image.uuid),
        "url": image.image.url if image.image else "",
        "srcset": image.srcset,
        "caption": image.caption,
        "source_text": image.source_text,
        "source_url": image.source_url,
        "created": image.created.isoformat() if image.created else None,
        "modified": image.modified.isoformat() if image.modified else None,
    }


class ImageStoreListView(generic.View):
    """Список изображений с пагинацией и фильтрацией по подписи.

    GET-параметры:
        ``caption`` — подстрока для поиска по подписи без учёта регистра;
        ``page`` — номер страницы (по умолчанию 1);
        ``page_size`` — размер страницы (по умолчанию 20, максимум 100).
    """

    def get(self, request, *args, **kwargs):
        try:
            page_number = _positive_int_param(request, "page", 1)
            page_size = _positive_int_param(
                request,
                "page_size",
                IMAGE_STORE_PAGE_SIZE,
                maximum=IMAGE_STORE_MAX_PAGE_SIZE,
            )
        except ValueError as error:
            return JsonResponse({"detail": str(error)}, status=400)

        queryset = ImageStore.objects.all().order_by("-created")
        caption = request.GET.get("caption", "").strip()
        if caption:
            queryset = queryset.filter(caption__icontains=caption)

        paginator = Paginator(queryset, page_size)
        if page_number > paginator.num_pages:
            return JsonResponse(
                {"detail": "Страница не найдена."},
                status=404,
            )
        page = paginator.page(page_number)

        def page_url(number):
            params = request.GET.copy()
            params["page"] = number
            return f"{request.path}?{urlencode(params)}"

        return JsonResponse(
            {
                "count": paginator.count,
                "page": page.number,
                "page_size": page_size,
                "pages": paginator.num_pages,
                "next": page_url(page.next_page_number()) if page.has_next() else None,
                "previous": (
                    page_url(page.previous_page_number())
                    if page.has_previous()
                    else None
                ),
                "results": [_image_store_payload(image) for image in page],
            }
        )


@require_POST
@check_upload_permission
def ckeditor_image_upload(request):
    """Загрузка изображения из CKEditor 5 в ``ImageStore``.

    CKEditor 5 (SimpleUploadAdapter) отправляет файл в поле ``upload``
    и ожидает JSON-ответ с URL изображения.
    """
    upload = request.FILES.get("upload")
    if upload is None:
        return JsonResponse(
            {"error": {"message": "Файл изображения не передан."}},
            status=400,
        )

    image_field = ImageStore._meta.get_field("image")
    try:
        upload = image_field.clean(upload, None)
    except ValidationError as error:
        return JsonResponse(
            {"error": {"message": " ".join(error.messages)}},
            status=400,
        )

    image_store = ImageStore(caption=request.POST.get("caption", ""))
    image_store.image = upload
    image_store.save()

    return JsonResponse({"url": image_store.image.url})
