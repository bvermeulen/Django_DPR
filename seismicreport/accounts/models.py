from django.db import models
from django.contrib.auth.models import User
from django.core.mail import EmailMessage
from django.template.loader import render_to_string


class Home(models.Model):
    welcome_text = models.TextField(max_length=2000)
    welcome_image = models.ImageField(upload_to='images/', null=True)
    member_text = models.TextField(max_length=2000)
    member_image = models.ImageField(upload_to='images/', null=True)

    def __str__(self):
        return 'home page'
