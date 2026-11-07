from django.http import HttpResponse
from django.shortcuts import render
from django.template import loader
from django.views import generic

from iju.models import Article, Category


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
