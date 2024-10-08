# Generated by Django 5.0.7 on 2024-08-06 17:39

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0008_rename_date_time_transactions_created_on_and_more'),
        ('mobile_app', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Cart',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('quantity', models.PositiveIntegerField(default=1)),
                ('created_on', models.DateTimeField(auto_now_add=True)),
                ('book', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='core.books')),
                ('material', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='core.materials')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='core.mobileusers')),
            ],
            options={
                'unique_together': {('user', 'book', 'material')},
            },
        ),
    ]
