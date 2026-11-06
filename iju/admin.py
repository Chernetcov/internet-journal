from django.contrib import admin
from django.utils.html import format_html

from iju.models import Category, Article, ImageStore


class CategoryAdmin(admin.ModelAdmin):
    list_display = ("slug", "name", "description")


class ArticleAdmin(admin.ModelAdmin):
    list_display = ("slug", "title", "created", "modified", "publicated", "publish")
    prepopulated_fields = {"slug": ["title"]}

class ImageStoreAdmin(admin.ModelAdmin):
    list_display = (
        "uuid",
        "image_preview",
        "caption",
    )
    readonly_fields = ("image_preview",)

    @admin.display(description="Превью")
    def image_preview(self, obj):
        if not obj.image:
            return "Нет изображения"

        return format_html(
            '<img src="{}" width="120" style="'
            'max-height: 80px; object-fit: contain;" />',
            obj.image.url,
        )

admin.site.register(Category, CategoryAdmin)
admin.site.register(Article, ArticleAdmin)
admin.site.register(ImageStore, ImageStoreAdmin)
