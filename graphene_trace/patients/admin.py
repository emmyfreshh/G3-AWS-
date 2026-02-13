from django.contrib import admin
from .models import PressureData, Comment, Notification

admin.site.register(PressureData)
admin.site.register(Comment)
admin.site.register(Notification)
