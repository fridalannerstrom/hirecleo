# Generated by Django 4.2.20 on 2025-04-12 19:23

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('hello_world', '0007_alter_candidate_email'),
    ]

    operations = [
        migrations.AlterField(
            model_name='candidate',
            name='cv_text',
            field=models.TextField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name='candidate',
            name='interview_notes',
            field=models.TextField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name='candidate',
            name='jobs',
            field=models.ManyToManyField(blank=True, related_name='candidates', to='hello_world.job'),
        ),
        migrations.AlterField(
            model_name='candidate',
            name='linkedin_url',
            field=models.URLField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name='candidate',
            name='phone_number',
            field=models.CharField(blank=True, max_length=20, null=True),
        ),
        migrations.AlterField(
            model_name='candidate',
            name='test_results',
            field=models.TextField(blank=True, null=True),
        ),
    ]
