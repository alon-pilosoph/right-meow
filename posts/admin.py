from django.contrib import admin
from .models import Post, Comment

# Register Post and Comment models in the admin site
admin.site.register(Post)
admin.site.register(Comment)
