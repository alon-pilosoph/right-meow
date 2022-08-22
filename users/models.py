from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.core.files import File
from django.db import models
from django.urls import reverse
from io import BytesIO
from os import listdir
from os.path import basename, isfile, join, splitext
from PIL import Image, ImageOps
import pytz
from random import choice


def random_img():
    """Method that returns a random image from the default profile pictures folder"""
    dir_path = join("media", "profile_pics", "default")
    files = [
        content for content in listdir(dir_path) if isfile(join(dir_path, content))
    ]
    return join("profile_pics", "default", choice(files))


def validate_file_size(value):
    """Method that validates the size of the Profile model's ImageField"""
    filesize = value.size
    # If filesize is over 10MB, raise ValidationError
    if filesize > 10 * 1024 * 1024:
        raise ValidationError("The maximum file size that can be uploaded is 10MB")
    else:
        return value


class Profile(models.Model):
    """Model that represents a user profile"""

    # Tuple of common timezones as choices for timezone field
    TIMEZONES = tuple(zip(pytz.common_timezones, pytz.common_timezones))
    timezone = models.CharField(
        max_length=32, choices=TIMEZONES, default="Asia/Jerusalem"
    )
    user = models.OneToOneField(User, related_name="profile", on_delete=models.CASCADE)
    slug = models.SlugField(unique=True)
    name = models.CharField(max_length=20)
    picture = models.ImageField(
        default=random_img, upload_to="profile_pics", validators=[validate_file_size]
    )
    about = models.TextField(null=True, blank=True)
    following = models.ManyToManyField(
        "self", related_name="followers", symmetrical=False, blank=True
    )

    def get_absolute_url(self):
        return reverse("profile_detail", kwargs={"slug": self.slug})

    def save(self, *args, **kwargs):
        """Method that redices the image quality before saving the model instance."""
        # If the model has an id field (if it was already saved)
        if self.id is not None:
            this_profile = Profile.objects.get(id=self.id)
            # If the current picture of the profile is different than the one being saved
            if this_profile.picture != self.picture:
                filename, extension = splitext(basename(self.picture.name))
                # If file extension is jpg, jpeg or png
                if extension in [".jpg", ".jpeg", ".png"]:
                    # Reduce the dimensions and quality of the image before uploading it
                    img = Image.open(self.picture)
                    img = ImageOps.exif_transpose(img)
                    if img.height > 300 or img.width > 300:
                        img.thumbnail((300, 300))
                    output = BytesIO()
                    img.convert("RGB").save(output, format="JPEG", quality=70)
                    # Save image as jpg
                    new_image = File(output, name=filename + ".jpg")
                    self.picture = new_image
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name if self.name else self.user.username
