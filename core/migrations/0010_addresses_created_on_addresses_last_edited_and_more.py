# Generated by Django 5.0.7 on 2024-08-08 05:52

import django.utils.timezone
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0009_alter_proreview_professional'),
    ]

    operations = [
        migrations.AddField(
            model_name='addresses',
            name='created_on',
            field=models.DateField(auto_now_add=True, default=django.utils.timezone.now),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='addresses',
            name='last_edited',
            field=models.DateTimeField(auto_now=True),
        ),
        migrations.AddField(
            model_name='portfolios',
            name='created_on',
            field=models.DateField(auto_now_add=True, default=django.utils.timezone.now),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='portfolios',
            name='last_edited',
            field=models.DateTimeField(auto_now=True),
        ),
        migrations.AddField(
            model_name='referrals',
            name='created_on',
            field=models.DateField(auto_now_add=True, default=django.utils.timezone.now),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='referrals',
            name='last_edited',
            field=models.DateTimeField(auto_now=True),
        ),
        migrations.AddField(
            model_name='transactions',
            name='last_edited',
            field=models.DateTimeField(auto_now=True),
        ),
    ]