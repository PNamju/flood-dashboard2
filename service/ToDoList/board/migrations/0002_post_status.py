# Generated by Django 5.0.6 on 2024-07-05 05:16

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("board", "0001_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="post",
            name="status",
            field=models.CharField(
                choices=[
                    ("draft", "Draft"),
                    ("published", "Published"),
                    ("deleted", "Deleted"),
                ],
                default="draft",
                max_length=10,
            ),
        ),
    ]
