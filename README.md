# Open Source Translation Tool

This project use the Meta [NLLB-200](https://ai.meta.com/blog/nllb-200-high-quality-machine-translation/) translation model through the [Hugging Face](https://huggingface.co/docs/transformers/model_doc/nllb) transformers library. The Meta NLLB-200 is a powerful language model designed for translation which has 54 billion parameters. However, this application built in Django uses a much smaller version ([600M parameters](https://huggingface.co/facebook/nllb-200-distilled-600M)) so that it can be used in its simplest form. How to modify this in the code to use alternative versions is detailed below.

The application has a translation interface where text can be directly copied and pasted for translation. In addition, it has a [language detector](https://huggingface.co/facebook/fasttext-language-identification) as part of the NLLB-200 project that is used to detect the source language.

In addition, the application contains a document translation interface through which documents with .pdf, .docx and .pptx extension can be translated. The translation of PDF documents makes use of an OCR through the Python easyOCR library, while for .pptx and .docx extensions the python-pptx and python-docx libraries are used respectively.

## Setting Up the Django Server

Below are the steps to set up the Django server on your local environment:

### Prerequisites (Linux)

Make sure you have the following installed:

- Python 3.10.12*
- Virtualenv (optional but recommended)

### Steps (Linux)

1. Clone this repository to your local machine:

   ```bash
   git clone https://github.com/alberto-solano/open_source_translation_tool.git
   ```


2. Set up a virtual environment and activate it

   ```bash
   virtualenv venv
   source venv/bin/activate
   ```

3. Install the necessary modules

   ```bash
   pip install -r requirements.txt
   ```
4. Download the lid_218 language detection model locally
   ```bash
   python src/save_models.py
   ``````

5. Run the django server
    ```bash
    python manage.py runserver
    ``````


### Prerequisites (Windows)

Make sure you have the following installed:

- Python 3.11.5*
- Virtualenv (optional but recommended)
- Poppler (0.68.0) installed and named 'poppler-0.68.0' as a folder inside the project. /bin folder should be inside.
- Tesseract installed and named 'Tesseract-OCR' as a folder inside the project. tesseract.exe file should be inside.

### Steps (Windows)

1. Clone this repository to your local machine:

   ```bash
   git clone https://github.com/alberto-solano/open_source_translation_tool.git
   ``````


2. Set up a virtual environment and activate it

   ```bash
   virtualenv venv
   source venv/bin/activate
   ```

3. Move to 'windows' branch

   ```bash
   git checkout windows
   ```

4. Install the necessary modules

   ```bash
   pip install -r requirements.txt
   pip install -e src/
   ```
5. Download the lid_218 language detection model locally
   ```bash
   python src/save_models.py
   ``````

6. Run the django server
    ```bash
    python manage.py runserver
    ```

***Note: If your Python version doesn't match with the required one, or if the installation fails, you can try manual installation using the 'libraries_required.txt' file, which contains all the necessary libraries.**

### Next steps and considerations

**1. Modifying the model:**
As mentioned above, the model used can be changed. By default, the 600M model is loaded in the views.py file so that it can be used directly after the server is up, if you want to use another model simply modify this at the beginning of the views.py file.

**2. GPU inference:**
GPU inference is currently not being used due to limitations on my local machine. This can be changed if you are lucky enough to have a GPU with which to do inference. The OCR models work faster with a GPU as the library points out and to use it you have to change the following line in "src/preprocess_pdf.py" setting the gpu parameter to 'True':
`reader = easyocr.Reader([easyocr_lang], gpu=False)``

**3. Limitations:**\
**3.1** It is likely that there are bugs in the preprocessing of the texts. The method currently followed is the separation of sentences by punctuation mark "." and concatenation of sentences ensuring that a certain maximum number of tokens is not exceeded. This maximum number of tokens has been set at 150 since it has been found that the models eliminate part of the input when it is very long. If other languages have a different sentence separation system, it is very likely that the translation will not work.

**3.2** The translation of powerpoint presentations and word documents, especially the latter, have limitations when it comes to accessing text located inside figures, or for example, the footers in the documents. This problem has not been addressed in depth so complex documents are expected to contain untranslated parts if they are over complex structures.

**3.3** PDF translation consists of detecting the text blocks of the images taken from the pdfs, and once translated, pasting them on top of the image. An algorithm is in charge of selecting the font size so that the text fits in this "box". The original formatting of the pdf will therefore not be maintained in the output. In addition, the model tends to generate invented text when we send it as input, for example alphanumeric codes that are not translatable, so we must be careful with the loss of information in this way.

**3.4** The selector with the list of languages ​​presented in the app has the intersection of the languages ​​accepted by all the models participating in the translation pipeline. The translation interface could present a more extensive list of languages ​​as referred to in the list of languages ​​supported by nllb models.

For any suggestions or improvements, do not hesitate to contact me. Happy coding!
