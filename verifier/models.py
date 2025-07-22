from django.db import models

class UploadedDocument(models.Model):
    file = models.FileField(upload_to='documents/')
    uploaded_at = models.DateTimeField(auto_now_add=True)
    file_type = models.CharField(max_length=10)
    uploader_ip = models.GenericIPAddressField()
    device_info = models.TextField()
    extracted_text = models.TextField(blank=True, null=True)

    # Added fields
    document_type = models.CharField(max_length=50, blank=True, null=True)
    name = models.CharField(max_length=100, blank=True, null=True)
    dob = models.CharField(max_length=20, blank=True, null=True)
    passport_no = models.CharField(max_length=20, blank=True, null=True)
    verification_status = models.CharField(max_length=20, default="Pending")

    def __str__(self):
        return self.file.name
