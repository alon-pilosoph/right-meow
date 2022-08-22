from django.contrib import messages
from django.contrib.auth import authenticate, login, update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import AuthenticationForm, PasswordChangeForm
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib.auth.views import PasswordResetView
from django.contrib.messages.views import SuccessMessageMixin
from django.db.models import Q
from posts.forms import PostForm
from django.http import HttpResponseBadRequest, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.template.defaultfilters import slugify
from django.template.loader import render_to_string
from django.urls import reverse_lazy
from django.views.generic import DetailView, UpdateView
from django.views.generic.edit import FormMixin
from django.views.generic.list import MultipleObjectMixin
from .forms import (
    UserRegistrationForm,
    ProfileCreationForm,
    ProfileTimezoneForm,
    UserUpdateForm,
)
from .models import Profile


def landing(request):
    """View that handles user login and registration"""

    # If user already authenticated, redirect to homepage
    if request.user.is_authenticated:
        return redirect("home")

    tab = None
    # POST request from the page's login form
    if request.method == "POST" and "login" in request.POST:
        # Set visible tab to login
        tab = "login"
        # populate authentication form with POST data
        login_form = AuthenticationForm(data=request.POST)
        # If form is valid, login user
        if login_form.is_valid():
            user = login_form.get_user()
            login(request, user)
            # Redirect to next page if it exists
            next_page = request.GET.get("next")
            messages.success(request, f"You logged in successfully!")
            return redirect(next_page if next_page else "home")
        else:
            # If form is invalid, add error message(s)
            for error in login_form.non_field_errors():
                messages.error(request, error)
    else:
        # GET request or POST request from another form on page
        login_form = AuthenticationForm()

    # POST request from the page's registration and profile creation forms
    if request.method == "POST" and "register" in request.POST:
        # Set visible tab to register
        tab = "register"
        # populate forms with POST data
        register_form = UserRegistrationForm(request.POST)
        profile_form = ProfileCreationForm(request.POST)
        # If both forms are valid
        if register_form.is_valid() and profile_form.is_valid():
            # Save user and associated profile
            new_user = register_form.save()
            profile_form.instance.user = new_user
            profile_form.instance.slug = slugify(new_user.username)
            profile_form.save()
            # Authenticate user and log them in
            user = authenticate(
                username=register_form.cleaned_data["username"],
                password=register_form.cleaned_data["password1"],
            )
            if user:
                login(request, user)
                messages.success(request, f"Account created successfully!")
                return redirect("home")
    else:
        # GET request or POST request from another form on page
        register_form = UserRegistrationForm()
        profile_form = ProfileCreationForm()

    return render(
        request,
        "users/landing.html",
        {
            "login_form": login_form,
            "register_form": register_form,
            "profile_form": profile_form,
            "tab": tab or "login",
        },
    )


class ProfileDetailView(LoginRequiredMixin, FormMixin, DetailView, MultipleObjectMixin):
    """Class-based view that shows profile details, along with new post form and list of associated posts"""

    model = Profile
    paginate_by = 5
    slug_field = "slug"
    template_name = "users/profile_detail.html"
    form_class = PostForm

    def get_context_data(self, **kwargs):
        # Add associated profiles to context data
        # If current user is following the profile viewed
        if self.object in self.request.user.profile.following.all():
            # Show all of that profile's posts
            posts = self.object.posts.all().order_by("-last_modified")
        else:
            # Otherwise, show only public posts
            posts = self.object.posts.filter(public=True).order_by("-last_modified")
        context = super().get_context_data(object_list=posts, **kwargs)
        return context

    def get_success_url(self):
        # After creating a new post form, user is redirected back to profile page
        return self.get_object().get_absolute_url()

    def post(self, request, *args, **kwargs):
        # Handle posts request on the page
        self.object = self.get_object()
        form = self.get_form()
        if form.is_valid():
            return self.form_valid(form)
        else:
            return self.form_invalid(form)

    def form_valid(self, form):
        # If form is valid, set the author of the post to the current user
        form.instance.author = self.request.user.profile
        form.save()
        return super(ProfileDetailView, self).form_valid(form)


class ProfileUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    """Class-based view that handles profile update"""

    model = Profile
    fields = ["name", "picture", "about"]
    slug_field = "slug"
    template_name = "users/profile_update.html"

    def form_valid(self, form):
        # If form is valid, add success message
        messages.success(self.request, "Profile updated successfully!")
        return super().form_valid(form)

    def test_func(self):
        # User must be associated with profile to be able to update it
        profile = self.get_object()
        return self.request.user.profile == profile


@login_required
def follow(request, slug):
    """View that handles follow requests"""
    # Find profile with slug
    profile = get_object_or_404(Profile, slug=slug)
    # If request method is POST, add profile to user's following field
    if request.method == "POST":
        request.user.profile.following.add(profile)
    # Redirect to profile page
    return redirect(profile.get_absolute_url())


@login_required
def unfollow(request, slug):
    """View that handles unfollow requests"""
    # Find profile with slug
    profile = get_object_or_404(Profile, slug=slug)
    # If request method is POST, remove profile from user's following field
    if request.method == "POST":
        request.user.profile.following.remove(profile)
    # Redirect to profile page
    return redirect(profile.get_absolute_url())


@login_required
def search(request):
    """View that renders search page"""
    return render(request, "users/search.html")


@login_required
def search_profiles(request):
    """View that receives AJAX GET requests with query string and responds with search results"""
    # Make sure the request is ajax
    is_ajax = request.headers.get("X-Requested-With") == "XMLHttpRequest"
    if is_ajax:
        if request.method == "GET":
            # Get query from request
            q = request.GET.get("q")
            # Find profiles that query is included in their name or username of their associated user
            profiles = Profile.objects.filter(
                Q(name__contains=q) | Q(user__username__contains=q)
            )
            # Send a json response with partial template that lists the matched profiles
            html = render_to_string(
                "partials/_profile_list.html", {"profiles": profiles}
            )
            return JsonResponse({"html": html, "results": profiles.count()}, safe=False)
    else:
        return HttpResponseBadRequest("Invalid request")


@login_required
def settings(request):
    """View that handles user and timezone settings, as well as changing user password"""
    # POST request from the page's settings form
    if request.method == "POST" and "settings" in request.POST:
        # populate forms with POST data
        user_form = UserUpdateForm(request.POST, instance=request.user)
        tz_form = ProfileTimezoneForm(request.POST, instance=request.user.profile)
        # If both forms are valid
        if user_form.is_valid() and tz_form.is_valid():
            # Save email and timezone
            user_form.save()
            tz_form.save()
            # Add success message and redirect to homepage
            messages.success(request, f"Your account has been updated!")
            return redirect("home")
    else:
        # GET request or POST request from another form on page
        user_form = UserUpdateForm(instance=request.user)
        tz_form = ProfileTimezoneForm(instance=request.user.profile)

    # POST request from the page's password change form
    if request.method == "POST" and "change_password" in request.POST:
        # populate form with POST data
        pass_form = PasswordChangeForm(user=request.user, data=request.POST)
        # If form is valid
        if pass_form.is_valid():
            # Save new password
            pass_form.save()
            # Update user authentication
            update_session_auth_hash(request, pass_form.user)
            # Add success message and redirect to homepage
            messages.success(request, f"Your password has been changed!")
            return redirect("home")
    else:
        # GET request or POST request from another form on page
        pass_form = PasswordChangeForm(user=request.user)

    return render(
        request,
        "users/settings.html",
        {"user_form": user_form, "tz_form": tz_form, "pass_form": pass_form},
    )


class CustomPasswordResetView(SuccessMessageMixin, PasswordResetView):
    """Custom class-based view that handles password reset requests"""

    template_name = "users/password_reset.html"
    success_message = "An email has been sent with instructions to reset your pasword."
    success_url = reverse_lazy("landing")


def custom_error_404(request, exception, template_name="errors/404.html"):
    """View that handles 404 errors"""
    return render(request, template_name)


def custom_error_403(request, exception, template_name="errors/403.html"):
    """View that handles 403 errors"""
    return render(request, template_name)


def custom_error_500(request, template_name="errors/500.html"):
    """View that handles 500 errors"""
    return render(request, template_name)
