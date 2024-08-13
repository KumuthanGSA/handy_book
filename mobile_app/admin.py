from django.contrib import admin

from .models import Cart, Favorite, Order, OrderItem, Payment

# Register your models here.
admin.site.register(Favorite)
admin.site.register(Cart)
admin.site.register(Order)
admin.site.register(OrderItem)
admin.site.register(Payment)