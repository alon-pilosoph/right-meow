from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.db.models import Q
from django.http import HttpResponseBadRequest, HttpResponseForbidden, JsonResponse
from django.shortcuts import get_object_or_404
from django.template.loader import render_to_string
from django.urls import reverse_lazy
from django.utils import timezone
from django.views.generic import DeleteView, DetailView, ListView, UpdateView
from django.views.generic.edit import FormMixin

from .forms import PostForm
from .models import Comment, Post


class PostListView(LoginRequiredMixin, FormMixin, ListView):
    """Class-based view that lists posts and renders new post form"""

    model = Post
    paginate_by = 5
    template_name = "posts/home.html"
    context_object_name = "posts"
    form_class = PostForm
    redirect_field_name = None

    def get_queryset(self):
        # Posts visible to user are posts by profiles he is following and by the user themselves
        return Post.objects.filter(
            Q(author__in=self.request.user.profile.following.all())
            | Q(author=self.request.user.profile)
        ).order_by("-last_modified")

    def get_success_url(self):
        # After creating a new post, user is redirected to homepage
        return reverse_lazy("home")

    def post(self, request, *args, **kwargs):
        self.object_list = self.get_queryset()
        # Add form functionality to ListView
        form = self.get_form()
        if form.is_valid():
            return self.form_valid(form)
        else:
            return self.form_invalid(form)

    def form_valid(self, form):
        # If form is valid, set the author of the post to the current user
        form.instance.author = self.request.user.profile
        form.save()
        return super(PostListView, self).form_valid(form)


class PostDetailView(LoginRequiredMixin, DetailView):
    """Class-based view that shows the details of a post"""

    model = Post


class PostUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    """Class-based view that updates posts"""

    model = Post
    fields = ["text", "image", "public"]
    template_name = "posts/post_update.html"

    def form_valid(self, form):
        # If post is updated, set author to current user
        form.instance.author = self.request.user.profile
        # Additionally, set last modified to current time
        form.instance.last_modified = timezone.now()
        return super().form_valid(form)

    def get_success_url(self):
        # After post is updated, redirect to its detail page
        return self.get_object().get_absolute_url()

    def get_context_data(self, **kwargs):
        # Add current post image to context data to render on update form
        context = super().get_context_data(**kwargs)
        post = Post.objects.get(id=self.object.id)
        if post:
            context["current_image"] = post.image
        return context

    def test_func(self):
        # User must be author to be able to update post
        post = self.get_object()
        return self.request.user.profile == post.author


class PostDeleteView(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    """Class-based view that deletes posts"""

    model = Post
    success_url = "/"

    def test_func(self):
        # User must be author to be able to delete post
        post = self.get_object()
        return self.request.user.profile == post.author


@login_required
def like_post(request):
    """View that receives AJAX POST requests and adds a like to a post or subtracts a like from it"""
    # Make sure the request is ajax
    is_ajax = request.headers.get("X-Requested-With") == "XMLHttpRequest"
    if is_ajax:
        if request.method == "POST":
            # Get post id from request and find post
            post_id = request.POST.get("id")
            post = get_object_or_404(Post, id=post_id)
            # User can like a post if they are following the author, if they are the author of if post is public
            if not (
                post.author.following.filter(id=request.user.profile.id).exists()
                or post.author == request.user.profile
                or post.public
            ):
                return HttpResponseForbidden("Private post")
            action = ""
            # If user already liked post, remove like from post
            if post.likes.filter(id=request.user.profile.id).exists():
                post.likes.remove(request.user.profile)
                post.save()
                action = "unlike"
            else:
                # Otherwise, add like to post
                post.likes.add(request.user.profile)
                post.save()
                action = "like"
            return JsonResponse({"result": post.total_likes, "action": action})
    else:
        return HttpResponseBadRequest("Invalid request")


@login_required
def like_comment(request):
    """View that receives AJAX POST requests and adds a like to a comment or subtracts a like from it"""
    # Make sure the request is ajax
    is_ajax = request.headers.get("X-Requested-With") == "XMLHttpRequest"
    if is_ajax:
        if request.method == "POST":
            # Get comment id from request and find comment
            comment_id = request.POST.get("id")
            comment = get_object_or_404(Comment, id=comment_id)
            # User can like a comment if they are following the post's author, if they are the author of if post is public
            if not (
                comment.post.author.following.filter(
                    id=request.user.profile.id
                ).exists()
                or comment.post.author == request.user.profile
                or comment.post.public
            ):
                return HttpResponseForbidden("Private post")
            action = ""
            # If user already liked comment, remove like from post
            if comment.likes.filter(id=request.user.profile.id).exists():
                comment.likes.remove(request.user.profile)
                comment.save()
                action = "unlike"
            else:
                # Otherwise, add like to comment
                comment.likes.add(request.user.profile)
                comment.save()
                action = "like"
            return JsonResponse({"result": comment.total_likes, "action": action})
    else:
        return HttpResponseBadRequest("Invalid request")


@login_required
def get_likes(request):
    """View that receives AJAX GET requests and returns list of profiles who liked the resource"""
    # Make sure the request is ajax
    is_ajax = request.headers.get("X-Requested-With") == "XMLHttpRequest"
    if is_ajax:
        if request.method == "GET":
            # Get resource id from request
            target_id = request.GET.get("id")
            target = None
            # Find the resource
            if request.GET.get("target") == "post":
                target = get_object_or_404(Post, id=target_id)
            elif request.GET.get("target") == "comment":
                target = get_object_or_404(Comment, id=target_id)
            else:
                return HttpResponseBadRequest("Invalid request")
            # Send a json response with partial template that lists the profiles who liked the resource
            html = render_to_string(
                "partials/_profile_list.html", {"profiles": target.likes.all()}
            )
            return JsonResponse(html, safe=False)
    else:
        return HttpResponseBadRequest("Invalid request")


@login_required
def create_comment(request):
    """View that receives AJAX POST requests and creates and renders comments"""
    # Make sure the request is ajax
    is_ajax = request.headers.get("X-Requested-With") == "XMLHttpRequest"
    if is_ajax:
        if request.method == "POST":
            # Get post id from request and find post
            post_id = request.POST.get("post_id")
            post = get_object_or_404(Post, id=post_id)
            # User can comment if they are following the post's author, if they are the author of if post is public
            if not (
                post.author.following.filter(id=request.user.profile.id).exists()
                or post.author == request.user.profile
                or post.public
            ):
                return HttpResponseForbidden("Private post")
            # Validate post text
            text = request.POST.get("text")
            if not (0 < len(text) <= 250):
                return HttpResponseBadRequest("Invalid comment")
            # Create comment and save
            comment = Comment(text=text, author=request.user.profile, post=post)
            comment.save()
            # Render a partial template and return as json
            html = render_to_string(
                "partials/_post_comment.html",
                {"comment": comment},
            )
            return JsonResponse(
                {"html": html, "count": post.total_comments}, safe=False
            )
    else:
        return HttpResponseBadRequest("Invalid request")


@login_required
def delete_comment(request):
    """View that receives AJAX POST requests and deletes comments"""
    # Make sure the request is ajax
    is_ajax = request.headers.get("X-Requested-With") == "XMLHttpRequest"
    if is_ajax:
        if request.method == "POST":
            # Get post id from request and find post
            comment_id = request.POST.get("id")
            comment = get_object_or_404(Comment, id=comment_id)
            # User can delete comment if they are the author of the comment or of the post
            post = comment.post
            if (
                request.user.profile != post.author
                and request.user.profile != comment.author
            ):
                return HttpResponseForbidden("Unauthorized to delete")
            # delete comment and return number of comments as json
            comment.delete()
            return JsonResponse({"count": post.total_comments})
    else:
        return HttpResponseBadRequest("Invalid request")
