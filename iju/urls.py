from django.urls import path
from . import views

urlpatterns = [
    path("", views.index, name="index"),
    path("<int:category_id>/", views.category, name="category"),
    path("articles/", views.ArticleListView.as_view(), name="articles"),
    path("article/<slug:slug>/", views.ArticleView.as_view(), name="article"),
    path("images/", views.ImageStoreListView.as_view(), name="images"),
    path(
        "ckeditor5/image_upload/",
        views.ckeditor_image_upload,
        name="ckeditor_image_upload",
    ),

    path("", views.about, name="about"),
]