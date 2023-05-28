from django.db import models


class ExcelFile(models.Model):
    file = models.FileField(upload_to="uploads/", unique=True)
    month = models.DateField()

    def __str__(self):
        return self.file.name.split("/")[-1]
