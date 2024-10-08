# Generated by Django 5.0.7 on 2024-08-10 06:47

import django.utils.timezone
import mobile_app.models
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('mobile_app', '0004_cart_last_edited_favorite_created_on_and_more'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='order',
            name='id',
        ),
        migrations.AddField(
            model_name='order',
            name='order_id',
            field=models.CharField(default=mobile_app.models.generate_orderid, editable=False, max_length=8, primary_key=True, serialize=False),
        ),
        migrations.AddField(
            model_name='orderitem',
            name='created_on',
            field=models.DateTimeField(auto_now_add=True, default=django.utils.timezone.now),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='orderitem',
            name='last_edited',
            field=models.DateTimeField(auto_now=True),
        ),
        migrations.DeleteModel(
            name='Payment',
        ),
    ]
