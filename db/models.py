from django.db import models
import uuid

# Create your models here.

# Project classes (Models)
class Feedback(models.Model):
    id = models.UUIDField(primary_key=True, editable=False, default=uuid.uuid4)
    rating = models.IntegerField(blank=True, null=True)
    text = models.TextField(blank=True, null=True)
