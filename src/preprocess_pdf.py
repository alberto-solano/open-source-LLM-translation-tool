from pdf2image import convert_from_path
import easyocr
import os
import pandas as pd
import json
from utils import detect_language_from_images


def convert_pdf2image(doc_filepath):
    """Function to convert a PDF into a set of images.

    Parameters
    ----------
    doc_filepath : str
        String with complete path to the document we aim to translate.

    Returns
    -------
    img_list : list
        List of the converted images
    """
    filepath = os.path.abspath(__file__)
    projpath = os.path.abspath(os.path.join(filepath, "..", ".."))
    tmp_path = os.path.join(projpath, "input", "tmp")

    # Store Pdf with convert_from_path function
    images = convert_from_path(doc_filepath)

    # list of filepaths to the images
    img_list = []

    for num, image in enumerate(images):
        # Save pages as images in the pdf
        image.save(os.path.join(tmp_path, f"page_{num+1}.png"))
        img_list.append(os.path.join(tmp_path, f"page_{num+1}.png"))

    return img_list


def preprocess_text(doc_filepath, language):
    """Function to preprocess text from a .pdf file.

    Parameters
    ----------
    doc_filepath : str
        String with complete path to the document we aim to translate
    language : str | None
        Language of the original document if provided, if not it should be
        ``None'' and it will be inferred.language

    Returns
    -------
    language : str
        Language of the pdf document
    ocr_data: pd.DataFrame
        Pandas DataFrame with all the paragraph texts and its bounding boxes
    """

    # paths
    filepath = os.path.abspath(__file__)
    projpath = os.path.abspath(os.path.join(filepath, "..", ".."))
    json_path = os.path.join(projpath, "json", "bcp47_to_easyocr.json")

    images = convert_pdf2image(doc_filepath)

    # use the google tesseract engine to convert the images to string
    # TODO: it is better to use TESSERACT than easyOCR?
    if language is None:
        language = detect_language_from_images(img_list=images)

    # easyocr accepts its own syntax for language, we must change this for the
    # tranlation model
    with open(json_path) as f:
        equivalences = json.load(f)

    easyocr_lang = equivalences.get(language)

    # TODO: Enable GPU
    reader = easyocr.Reader([easyocr_lang], gpu=False)

    # empty parameters initialization
    text_list = []
    page_list = []
    x_min_list = []
    y_min_list = []
    x_max_list = []
    y_max_list = []
    height_list = []
    width_list = []

    # iterate over the images
    for page, image in enumerate(images):
        # extract paragraphs and its coordinates
        bounds = reader.readtext(image, detail=1, paragraph=True)

        # gather the info for each paragraph
        for paragraph in bounds:
            text_list.append(paragraph[1])
            page_list.append(page + 1)
            # bbox
            xmin, ymin = paragraph[0][0]
            xmax, ymax = paragraph[0][2]
            x_min_list.append(xmin)
            y_min_list.append(ymin)
            x_max_list.append(xmax)
            y_max_list.append(ymax)
            height_list.append(ymax - ymin)
            width_list.append(xmax - xmin)

        # update the page
        page += 1

    # convert into a pandas dataframe
    ocr_data = pd.DataFrame(
        {
            "paragraph": text_list,
            "xmin": x_min_list,
            "xmax": x_max_list,
            "ymin": y_min_list,
            "ymax": y_max_list,
            "page": page_list,
        }
    )

    return language, ocr_data
