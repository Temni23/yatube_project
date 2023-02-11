from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.shortcuts import render, get_object_or_404, redirect
from django.views.generic import ListView, DetailView

from .forms import PostForm, CommentForm
from .models import Post, Group, Comment, Follow, User


# POSTS_TO_OUTPUT = 10


def get_paginator(args, request):
    paginator = Paginator(args, settings.POSTS_TO_OUTPUT)
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)
    return {
        "page_number": page_number,
        "page_obj": page_obj,
    }

class PostsHome(ListView):
    paginate_by = 10
    model = Post
    template_name = 'posts/index.html'
    # context_object_name = 'posts'

    def get_queryset(self):
        return Post.objects.select_related("author").all()

# def index(request):
#     template = "posts/index.html"
#     post_list = Post.objects.select_related("author").all()
#     context = {"index": True}
#     context.update(get_paginator(post_list, request))
#     return render(request, template, context)


# def group_posts(request, slug):
#     group = get_object_or_404(Group, slug=slug)
#     template = "posts/group_list.html"
#     post_list = group.posts.all()
#     context = {
#         "group": group,
#     }
#     context.update(get_paginator(post_list, request))
#     return render(request, template, context)
class PostGroup(ListView):
    paginate_by = 10
    model = Post
    template_name = 'posts/group_list.html'

    def get_queryset(self):
        return get_object_or_404(Group, slug = self.kwargs['slug']).posts.all()



def profile(request, username):
    author = get_object_or_404(User, username=username)
    post_list_user = author.posts.all()
    following = False
    if request.user.is_authenticated and author.following.filter(
            user=request.user).exists():
        following = True
    context = {
        "author": author,
        "following": following
    }
    context.update(get_paginator(post_list_user, request))
    template = "posts/profile.html"
    return render(request, template, context)


# def post_detail(request, post_id):
#     post = get_object_or_404(Post, pk=post_id)
#     form = CommentForm(request.POST or None)
#     comments = post.comment.all()
#     author = False
#     if request.user == post.author:
#         author = True
#     context = {
#         "post": post,
#         "author": author,
#         "form": form,
#         "comments": comments
#     }
#     template = "posts/post_detail.html"
#     return render(request, template, context)

class PostDetailView(DetailView):
    model = Post
    template_name = "posts/post_detail.html"
    context_object_name = "post"
    pk_url_kwarg = "post_id"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["form"] = CommentForm(self.request.POST or None)
        context["comments"] = self.object.comment.all()
        context["author"] = False
        if self.request.user == self.object.author:
            context["author"] = True
        return context

@login_required
def post_create(request):
    template = "posts/create_post.html"
    form = PostForm(request.POST or None)
    if request.method == "POST":
        if form.is_valid():
            instance = form.save(commit=False)
            instance.author = request.user
            instance.save()
            return redirect("posts:profile", request.user.username)
    return render(request, template, {"form": form})


@login_required()
def post_edit(request, post_id):
    template = "posts/create_post.html"
    post = get_object_or_404(Post, id=post_id)
    form = PostForm(
        request.POST or None,
        files=request.FILES or None,
        instance=post
    )
    context = {"form": form, "is_edit": True}
    if request.user == post.author:
        if form.is_valid():
            post.save()
            return redirect("posts:post_detail", post_id=post_id)
        return render(request, template, context)
    return redirect("posts:post_detail", post_id=post_id)


@login_required
def add_comment(request, post_id):
    post = get_object_or_404(Post, pk=post_id)
    form = CommentForm(request.POST or None)
    if form.is_valid():
        comment = form.save(commit=False)
        comment.author = request.user
        comment.post = post
        comment.save()
    return redirect("posts:post_detail", post_id=post_id, )


@login_required
def follow_index(request):
    user = request.user
    post_list = Post.objects.filter(
        author__following__user=user)
    context = {"follow": True}
    context.update(get_paginator(post_list, request))
    return render(request, "posts/follow.html", context)


@login_required
def profile_follow(request, username):
    user = request.user
    author = get_object_or_404(User, username=username)
    if author != request.user:
        Follow.objects.get_or_create(user=user, author=author)
    return redirect("posts:profile", author)


@login_required
def profile_unfollow(request, username):
    author = get_object_or_404(User, username=username)
    follow = get_object_or_404(
        Follow,
        user=request.user,
        author=author
    )
    follow.delete()
    return redirect("posts:profile", username)
