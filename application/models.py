from django.db import models


class Translation(models.Model):
    translated_document = models.FileField(upload_to="translated_documents/")
    translation_date = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.translated_document.name
