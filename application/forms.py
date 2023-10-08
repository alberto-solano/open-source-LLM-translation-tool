from django import forms
from django.core.validators import FileExtensionValidator
from django.core.exceptions import ValidationError


class DocumentForm(forms.Form):
    translated_document = forms.FileField(
        label="Select a file*",
        help_text="(*) PDF, Word (docx), or PowerPoint (pptx) files only",
        validators=[
            FileExtensionValidator(allowed_extensions=["pdf", "docx", "pptx"])
        ],
        required=True,
        error_messages={
            "required": "A file is required in order to submit a translation."
        },
    )

    def clean_translated_document(self):
        translated_document = self.cleaned_data.get("translated_document")
        if translated_document:
            file_extension = translated_document.name.split(".")[-1].lower()
            if file_extension not in ["pdf", "docx", "pptx"]:
                raise ValidationError(
                    "Invalid file extension. Allowed extensions are: .pdf, .docx, .pptx"
                )
        return translated_document
