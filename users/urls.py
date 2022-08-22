from django.contrib.auth import views as auth_views
from django.urls import path
from django.views.decorators.cache import never_cache
from . import views
from .views import CustomPasswordResetView, ProfileDetailView, ProfileUpdateView


urlpatterns = [
    path(
        "logout/",
        auth_views.LogoutView.as_view(template_name="users/logout.html"),
        name="logout",
    ),
    path(
        "password-reset/",
        CustomPasswordResetView.as_view(),
        name="password_reset",
    ),
    path(
        "password-reset-confirm/<uidb64>/<token>/",
        auth_views.PasswordResetConfirmView.as_view(
            template_name="users/password_reset_confirm.html"
        ),
        name="password_reset_confirm",
    ),
    path(
        "password-reset-complete/",
        auth_views.PasswordResetCompleteView.as_view(
            template_name="users/password_reset_complete.html"
        ),
        name="password_reset_complete",
    ),
    path("welcome/", views.landing, name="landing"),
    path(
        "<slug:slug>/profile",
        never_cache(ProfileDetailView.as_view()),
        name="profile_detail",
    ),
    path(
        "<slug:slug>/profile/edit/",
        ProfileUpdateView.as_view(),
        name="profile_update",
    ),
    path(
        "<slug:slug>/follow/",
        views.follow,
        name="profile_follow",
    ),
    path(
        "<slug:slug>/unfollow/",
        views.unfollow,
        name="profile_unfollow",
    ),
    path("search/", views.search, name="search"),
    path("search-profiles/", views.search_profiles, name="search_profiles"),
    path("settings/", views.settings, name="settings"),
]
