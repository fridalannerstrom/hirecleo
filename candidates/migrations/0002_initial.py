# Generated by Django 4.2.20 on 2025-06-22 20:27

from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('jobs', '0001_initial'),
        ('candidates', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='candidate',
            name='jobs',
            field=models.ManyToManyField(blank=True, related_name='candidates', to='jobs.job'),
        ),
    ]
