from docx import Document
from utils import language_detection


def preprocess_text(doc_filepath, language):
    """Function to preprocess text from a .docx file. Each paragraph is
    obtained through paragraph atribute from python.docx library.

    Parameters
    ----------
    doc_filepath : str
        String with complete path to the document we aim to translate
    language : str | None
        Language of the original document if provided, if not it should be
        ``None'' and it will be inferred.

    Returns
    -------
    language : str
        Language of the document
    document : docx.document.Document
        Document object from .docx file containing all the text
    """
    # opens .docx file
    document = Document(doc_filepath)

    # creates a list of non-empty paragraphs
    paragraphs_list = [
        paragraph.text
        for paragraph in document.paragraphs
        if paragraph.text != ""
    ]

    # infer language if it has not been specified
    if language is None:
        print("Detecting the language of the document...")
        language = language_detection(paragraphs_list)

    return language, document
