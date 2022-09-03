from django.contrib import admin

from .models import Comment, Post

# Register Post and Comment models in the admin site
admin.site.register(Post)
admin.site.register(Comment)
