# Generated by Django 5.0.7 on 2024-08-13 05:14

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('mobile_app', '0008_alter_payment_amount'),
    ]

    operations = [
        migrations.AlterField(
            model_name='payment',
            name='amount',
            field=models.FloatField(null=True),
        ),
    ]
