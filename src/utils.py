import fasttext
import os
from unidecode import unidecode
import pytesseract
from PIL import Image
from transformers import AutoModelForSeq2SeqLM


def handle_non_ascii(_string):
    """Convert all non-ASCII characters to their closest ASCII equivalent
    automatically."""
    result = unidecode(_string)
    return result


def handle_utf8(_string):
    result = _string.encode("utf-8", errors="ignore").decode("utf-8")
    return result


def handle_whitespaces(_string):
    result = " ".join(_string.split())
    return result


def basic_preprocessing(_string):
    # TODO: improve preprocessing
    clean_string = handle_non_ascii(_string)
    clean_string = handle_utf8(clean_string)
    clean_string = handle_whitespaces(clean_string)
    return clean_string


def convert_text(original_paragraph, tokenizer, max_tokens):
    """Function to generate a list of strings with a limited number of tokens
    given the max_tokens parameter. The sentence is splited by ". " as a
    separator and the sentences are combined (or not) based on if they
    exceed (or not) the number of tokens limit given the tokenizer.

    Parameters
    ----------
    original_paragraph : str
        String considered as paragraph
    tokenizer : NllbTokenizerFast
        tool that converts text to tokens
    max_tokens : max_tokens
        Max number of tokens included in each original_text_list element

    Returns
    -------
    text_groups : ndarray
        1D array with the concatenated strings of the elements of each group.
    """

    # initializes empty list in which text strings will be introduced
    limited_tokens_sentences = []

    # strip the original paragraph
    original_paragraph = original_paragraph.strip()

    # makes a list of sentences (here we consider a ". ")
    sentences_list = original_paragraph.split(". ")

    # initializes string in which text will be stored
    cummulative_sentence = sentences_list[0].strip()
    for text in sentences_list[1:]:
        # create temporal sentence variable which adds or substracts text
        t_cummulative_sentence = cummulative_sentence + ". " + text.strip()
        n_tokens = tokenizer(t_cummulative_sentence, return_tensors="pt")[
            "input_ids"
        ].shape[1]

        # if cummulative sentence + appended sentence exceeds total length
        if n_tokens > max_tokens:
            limited_tokens_sentences.append(cummulative_sentence.strip() + ".")

            # empty the sentence
            cummulative_sentence = text.strip()

        # if we can still append text blocks to cummulative sentence
        else:
            cummulative_sentence += ". " + text

    # append the last chunk of text.
    limited_tokens_sentences.append(cummulative_sentence.strip())

    return limited_tokens_sentences


def language_detection(text):
    """Function to automatically detect a langauge using the lid218e model.

    Parameters
    ----------
    text : list
        Text list with the paragraphs in the language that we want to know

    Returns
    -------
    text_lang : str
        Inferred language
    """

    # manual set of models path
    filepath = os.path.abspath(__file__)
    projpath = os.path.abspath(os.path.join(filepath, "..", ".."))
    models_path = os.path.join(projpath, "models")
    # load lid model
    fasttextmodel = fasttext.load_model(
        os.path.join(models_path, "lid218e.bin")
    )
    # replace newlines as they are not accepted by the model, the model seems
    # to accept any input lenght so we pass the entire document
    all_text = " ".join(text).replace("\n", "")
    # language identification
    text_lang = fasttextmodel.predict(all_text, k=1)[0][0].replace(
        "__label__", ""
    )

    print(f"Detected language: {text_lang}")
    return text_lang


def detect_language_from_images(img_list, page_limit=5):
    """Function to infer the language of a group of images using the
    google Tesseract OCR engine + lid218e model.

    Parameters
    ----------
    img_list : list
        Path to the images which language we want to know

    page_limit : int
        Number of document pages to consider when inferring the language

    Returns
    -------
    language : str
        Inferred language
    """

    filepath = os.path.abspath(__file__)
    projpath = os.path.abspath(os.path.join(filepath, "..", ".."))
    tesseract_path = os.path.join(projpath, "Tesseract-OCR", "tesseract.exe")

    pytesseract.pytesseract.tesseract_cmd = tesseract_path
    # prevent error on little docs
    limit = min(page_limit, len(img_list))

    # initialize an empty string for storing the text from the images
    complete_text = []

    print("Detecting the language of the document...")
    # iterate over each of the images
    for image in img_list[:limit]:
        im = Image.open(image)
        text_from_image = pytesseract.image_to_string(im)
        # append to the cummulative string
        complete_text.append(text_from_image)

    # now we will infer the language from the given text
    language = language_detection(complete_text)

    return language


def load_model(model_path):
    """Function to load the desired nllb model.

    Parameters
    ----------
    model_path : str
        Path in which the model is stored

    Returns
    -------
    model : str
        Loaded model class
    """

    model = AutoModelForSeq2SeqLM.from_pretrained(model_path)

    return model
