# Generated by Django 4.2.2 on 2023-06-23 11:25

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='user',
            name='chat_id',
            field=models.BigIntegerField(blank=True, default=None, null=True, unique=True, verbose_name='Chat id'),
        ),
    ]
