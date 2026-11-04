from django.contrib import admin

from iju.models import Category, Article

# Register your models here.

class CategoryAdmin(admin.ModelAdmin):
    #fields = "__all__"
    list_display = ("slug", "name", "description")


class ArticleAdmin(admin.ModelAdmin):
    #fields = "__all__"
    list_display = ("slug", "title", "created", "modified", "publicated", "publish")
    prepopulated_fields = {"slug": ["title"]}

admin.site.register(Category, CategoryAdmin)
admin.site.register(Article, ArticleAdmin)
