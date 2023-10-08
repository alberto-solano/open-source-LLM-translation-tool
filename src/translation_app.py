import os
import time
from save_document import save_translated_doc


def translate_text(
    doc_filepath,
    max_tokens,
    models_path,
    model_name,
    lang_orig_code,
    lang_dest_code,
    document_type,
    loaded_model,
):
    """Function to generate a list of strings with a limited number of tokens.
    Each string will be processed with the NLLB model so it should not exceed
    the model's length limit (500 tokens).

    Parameters
    ----------
    doc_filepath : str
        Path to the document which will be translated
    document_type : str
        Input file extension
    max_tokens : int
        Max number of tokens included in each original_text_list element
    models_path : str
        Path to where the model is stored at (unused in django app)
    model_name : str
        Name of the model that will be used (unused in django app)
    lang_origin_code : str
        Langugage code in BCP-47 of the original text
    lang_dest_code : str
        Langugage code in BCP-47 of the desired output
    loaded_model :
        Model loaded when running the django server


    Returns
    -------

    """

    if document_type == "docx":
        from preprocess_docx import preprocess_text
        from translate_docx import translate_document
    elif document_type in ["pdf", "PDF"]:
        from preprocess_pdf import preprocess_text
        from translate_pdf import translate_document
    elif document_type == "pptx":
        from preprocess_pptx import preprocess_text
        from translate_pptx import translate_document
    else:
        raise ValueError("Unsupported file type")

    # read and handle the different document inputs
    language, document = preprocess_text(
        doc_filepath=doc_filepath, language=lang_orig_code
    )

    # now we will translate the paragraphs for the document based on its type
    translated_document = translate_document(
        document=document,
        model_name=model_name,
        models_path=models_path,
        max_tokens=max_tokens,
        lang_origin_code=language,
        lang_dest_code=lang_dest_code,
        loaded_model=loaded_model,
    )

    return translated_document


def translate_document(filename, dst_lang, loaded_model=None):
    # select document to translate
    doc_name = filename
    # select model
    model_name = "nllb-200-distilled-600M"
    # select language code in bcp-47 (if None it will be inferred)
    scr_lang = None
    # set a maximum number of tokens to translate in each text block. The
    # model is prepared to parse up to 500 tokens, but as this number increases
    # the model's accuracy might decrease
    max_tokens = 150

    # set variables needed to get and upload files
    filepath = os.path.abspath(__file__)
    projpath = os.path.abspath(os.path.join(filepath, "..", ".."))
    models_path = os.path.join(projpath, "models")
    # input file is saved into tmp folder
    input_path = os.path.join(projpath, "input", "tmp")
    doc_filepath = os.path.join(input_path, doc_name)
    output_path = os.path.join(projpath, "media", "translated_documents")
    output_filename = f"translated_{doc_name}"
    output_file = os.path.join(output_path, output_filename)

    # get document type (docx, pdf, pptx...)
    doc_type = doc_name.split(".")[-1]

    # execute text translation
    start = time.time()
    translated_document = translate_text(
        doc_filepath=doc_filepath,
        max_tokens=max_tokens,
        models_path=models_path,
        model_name=model_name,
        lang_orig_code=scr_lang,
        lang_dest_code=dst_lang,
        document_type=doc_type,
        loaded_model=loaded_model,
    )

    save_translated_doc(translated_document, output_file, doc_type)

    # empty the tmp folder
    # create temporal folder if not exists:
    if os.path.exists(input_path):
        # empty the folder
        for file in os.listdir(input_path):
            os.remove(os.path.join(input_path, file))
        # remove the folder
        os.rmdir(input_path)

    # create the empty folder for storing the images
    os.makedirs(input_path)

    end = time.time()

    print(f"Total time:{end-start} s")
