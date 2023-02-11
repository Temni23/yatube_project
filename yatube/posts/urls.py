from django.urls import path

from .views import *

app_name = "posts"

urlpatterns = [
    path("", PostsHome.as_view(), name="index"),
    path("group/<slug:slug>/", PostGroup.as_view(), name="group_list"),
    path("profile/<str:username>/", profile, name="profile"),
    path("posts/<int:post_id>/", PostDetailView.as_view(), name="post_detail"),
    path("create/", post_create, name="post_create"),
    path("posts/<int:post_id>/edit/", post_edit, name="post_edit"),
    path("posts/<int:post_id>/comment/", add_comment,
         name="add_comment"),
    path("follow/", follow_index, name="follow_index"),
    path(
        "profile/<str:username>/follow/", profile_follow,
        name="profile_follow"
    ),
    path("profile/<str:username>/unfollow/", profile_unfollow,
         name="profile_unfollow"
         ),
]
