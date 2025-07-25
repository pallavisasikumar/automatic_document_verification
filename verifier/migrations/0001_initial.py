# Generated by Django 5.2.4 on 2025-07-21 17:31

from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name="UploadedDocument",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("file", models.FileField(upload_to="documents/")),
                ("uploaded_at", models.DateTimeField(auto_now_add=True)),
                ("file_type", models.CharField(max_length=10)),
                ("uploader_ip", models.GenericIPAddressField()),
                ("device_info", models.TextField()),
            ],
        ),
    ]
