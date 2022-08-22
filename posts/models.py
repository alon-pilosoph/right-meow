from django.core.exceptions import ValidationError
from django.core.files import File
from django.db import models
from django.urls import reverse
from django.utils import timezone
from io import BytesIO
from os.path import basename, splitext
from PIL import Image, ImageOps
from users.models import Profile


def validate_file_size(value):
    """Method that validates the size of the Post model's ImageField"""
    filesize = value.size
    # If filesize is over 10MB, raise ValidationError
    if filesize > 10 * 1024 * 1024:
        raise ValidationError("The maximum file size that can be uploaded is 10MB")
    else:
        return value


class Post(models.Model):
    """Model that represents a post"""

    text = models.CharField(max_length=250)
    image = models.ImageField(
        blank=True, upload_to="post_images", validators=[validate_file_size]
    )
    public = models.BooleanField(default=True)
    last_modified = models.DateTimeField(default=timezone.now)
    author = models.ForeignKey(Profile, related_name="posts", on_delete=models.CASCADE)
    # Likes are stored as Many to Many relationship with Profile model
    likes = models.ManyToManyField(Profile, related_name="post_likes")

    @property
    def total_likes(self):
        # Property method that counts the total number of likes
        return self.likes.count()

    @property
    def total_comments(self):
        # Property method that counts the total number of comments
        return self.comments.count()

    def save(self, *args, **kwargs):
        """Method that reduces the image quality before saving the model instance."""
        # If instance has no id (post was just created) or instace image was changed
        if self.id is None or Post.objects.get(id=self.id).image != self.image:
            filename, extension = splitext(basename(self.image.name))
            # If file extension is jpg, jpeg or png
            if extension in [".jpg", ".jpeg", ".png"]:
                # Reduce the quality of the image before uploading it
                img = Image.open(self.image)
                img = ImageOps.exif_transpose(img)
                # If image width is over 600px, resize it to 600px (while keeping the ratio)
                if img.width > 600:
                    img = img.resize((600, img.height * 600 // img.width))
                output = BytesIO()
                img.convert("RGB").save(output, format="JPEG", quality=70)
                # Save image as jpg
                new_image = File(output, name=filename + ".jpg")
                self.image = new_image
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse("post_detail", kwargs={"slug": self.author.slug, "pk": self.id})

    def __str__(self):
        return str(self.text)


class Comment(models.Model):
    """Model that represents a comment to a post"""

    text = models.CharField(max_length=250)
    date_created = models.DateTimeField(auto_now_add=True)
    author = models.ForeignKey(
        Profile, related_name="comments", on_delete=models.CASCADE
    )
    post = models.ForeignKey(Post, related_name="comments", on_delete=models.CASCADE)
    # Likes are stored as Many to Many relationship with Profile model
    likes = models.ManyToManyField(Profile, related_name="comment_likes")

    @property
    def total_likes(self):
        # Property method that counts the total number of likes
        return self.likes.count()

    def __str__(self):
        return str(self.text)
