# Generated by Django 3.2.25 on 2024-06-01 08:22

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0006_alter_recipe_tags'),
    ]

    operations = [
        migrations.AlterField(
            model_name='recipe',
            name='tags',
            field=models.ManyToManyField(to='core.Tag'),
        ),
    ]