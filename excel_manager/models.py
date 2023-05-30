from django.db import models


class ExcelFile(models.Model):
    file = models.FileField(upload_to="uploads/", unique=True)
    filename = models.CharField(max_length=50, default="nofilename", blank=True)
    month = models.DateField()
    project_name = models.CharField(max_length=100, default="noprojectname")

    def __str__(self):
        return self.file.name.split("/")[-1]
