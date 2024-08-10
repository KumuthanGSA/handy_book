import uuid
from django.db import models
from django.core.validators import MinValueValidator

# Third party inmports
from phonenumber_field.modelfields import PhoneNumberField

#Local imports
from core.models import Addresses, Books, Materials, MobileUsers


# Create your models here.

def generate_orderid():
    return str(uuid.uuid4().int)[:8]

class Favorite(models.Model):
    TYPE_CHOICES = [
        ('professional', 'Professional'),
        ('book', 'Book'),
        ('material', 'Material'),
    ]

    
    user = models.ForeignKey(MobileUsers, on_delete=models.CASCADE, related_name='favorites')
    type = models.CharField(max_length=20, choices=TYPE_CHOICES)
    item_id = models.PositiveIntegerField()
    created_on = models.DateField(auto_now_add=True)
    last_edited = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('user', 'type', 'item_id')

    def __str__(self):
        return f'{self.user.first_name} - {self.type} {self.item_id}'
    

class Cart(models.Model):
    user = models.ForeignKey(MobileUsers, on_delete=models.CASCADE)
    book = models.ForeignKey(Books, on_delete=models.CASCADE, null=True, blank=True)
    material = models.ForeignKey(Materials, on_delete=models.CASCADE, null=True, blank=True)
    quantity = models.PositiveIntegerField(default=1)
    created_on = models.DateTimeField(auto_now_add=True)
    last_edited = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('user', 'book', 'material')

    def __str__(self):
        return f'{self.user} - {self.book or self.material}'
    

class Order(models.Model):
    ORDER_STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('packed', 'Packed'),
        ('shipped', 'Shipped'),
        ('delivered', 'Delivered'),
        ('cancelled', 'Cancelled'),
    ]

    order_id = models.CharField(max_length=8, primary_key=True, default=generate_orderid, editable=False)
    user = models.ForeignKey(MobileUsers, on_delete=models.CASCADE, related_name='orders')
    total_price = models.FloatField(validators=[MinValueValidator(0)])
    status = models.CharField(max_length=20, choices=ORDER_STATUS_CHOICES, default='pending')
    created_on = models.DateTimeField(auto_now_add=True)
    last_edited = models.DateTimeField(auto_now=True)
    address = models.ForeignKey(Addresses, on_delete=models.DO_NOTHING, related_name="orders")

    def __str__(self):
        return f'Order {self.id} - {self.user.email}'
    

class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items')
    book = models.ForeignKey(Books, on_delete=models.CASCADE, null=True, blank=True)
    material = models.ForeignKey(Materials, on_delete=models.CASCADE, null=True, blank=True)
    quantity = models.PositiveIntegerField(default=1)
    price = models.FloatField()

    def __str__(self):
        return f'Item {self.id} - {self.order.id}'
    

# class Payment(models.Model):
#     PAYMENT_TYPE_CHOICES = [
#         ('cash on delivery', 'Cash on Delivery'), ('upi', 'UPI')
#     ]

#     PAYMENT_STATUS_CHOICES = [
#         ('pending', 'Pending'), ('completed', 'Completed'), ('failed', 'Failed'),
#     ]

#     order = models.OneToOneField(Order, on_delete=models.CASCADE, related_name='payment')
#     amount = models.FloatField(validators=[MinValueValidator(0)])
#     status = models.CharField(max_length=20, choices=PAYMENT_STATUS_CHOICES, default='pending')
#     type = models.CharField(max_length=100, choices=PAYMENT_TYPE_CHOICES)
#     created_on = models.DateTimeField(auto_now_add=True)
#     last_edited = models.DateTimeField(auto_now_add=True)

#     def __str__(self):
#         return f'Payment {self.id} - {self.order.id}'

    