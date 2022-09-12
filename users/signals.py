from django.contrib import messages
from django.contrib.auth import user_logged_out
from django.dispatch import receiver


@receiver(user_logged_out)
def on_user_logged_out(sender, request, user, **kwargs):
    """Signal that fires after user logs out and adds a success message"""

    messages.success(request, "You successfully logged out. Goodbye!")
