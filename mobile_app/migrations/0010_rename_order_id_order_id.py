# Generated by Django 5.0.7 on 2024-08-13 05:28

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('mobile_app', '0009_alter_payment_amount'),
    ]

    operations = [
        migrations.RenameField(
            model_name='order',
            old_name='order_id',
            new_name='id',
        ),
    ]
