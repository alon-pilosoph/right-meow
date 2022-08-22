from django import forms
from .models import Post


class PostForm(forms.ModelForm):
    """Model form for posts"""

    class Meta:
        model = Post
        fields = ["text", "image", "public"]
