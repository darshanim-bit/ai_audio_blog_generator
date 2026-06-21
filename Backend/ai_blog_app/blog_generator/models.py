from django.db import models
from django.contrib.auth.models import User

# Create your models here.
class Blogpost(models.Model):
    """"Blogpost model is used for store the generated blog content to database.
    """
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    title = models.CharField(max_length=200)
    youtube_url = models.URLField()
    content = models.TextField()    
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return str(self.title)
