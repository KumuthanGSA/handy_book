from django.contrib import admin

from .models import Cart, Favorite

# Register your models here.
admin.site.register(Favorite)
admin.site.register(Cart)