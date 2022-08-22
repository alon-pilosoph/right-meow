from django.urls import path
from django.views.decorators.cache import never_cache
from . import views
from .views import PostListView, PostDetailView, PostUpdateView, PostDeleteView

urlpatterns = [
    path("", never_cache(PostListView.as_view()), name="home"),
    path(
        "<slug:slug>/<int:pk>/",
        never_cache(PostDetailView.as_view()),
        name="post_detail",
    ),
    path(
        "<slug:slug>/<int:pk>/edit/",
        PostUpdateView.as_view(),
        name="post_update",
    ),
    path(
        "<slug:slug>/<int:pk>/delete/",
        PostDeleteView.as_view(),
        name="post_delete",
    ),
    path("like-post/", views.like_post, name="like_post"),
    path("like-comment/", views.like_comment, name="like_comment"),
    path("get-likes/", views.get_likes, name="get_likes"),
    path("create-comment/", views.create_comment, name="create_comment"),
    path("delete-comment/", views.delete_comment, name="delete_comment"),
]
