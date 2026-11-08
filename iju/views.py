from django.core.exceptions import ValidationError
from django.http import HttpResponse, JsonResponse
from django.shortcuts import render
from django.template import loader
from django.views import generic
from django.views.decorators.http import require_POST
from django_ckeditor_5.permissions import check_upload_permission

from iju.models import Article, Category, ImageStore


def index(request):
    context = {
        'categories': Category.objects.all()
    }
    return render(request, 'index.html', context)

def category(request, category_id):
    return HttpResponse(f"Category page id: {category_id}")

class ArticleListView(generic.ListView):
    template_name = "articles.html"
    context_object_name = "articles"

    def get_queryset(self):
        """Return the last 15 published articles."""
        return Article.objects.filter(publish = True).order_by("-publicated")[:15]

class ArticleView(generic.DetailView):
    model = Article
    template_name = "article.html"
    context_object_name = "article"

def about(request):
    return HttpResponse("About page")


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
