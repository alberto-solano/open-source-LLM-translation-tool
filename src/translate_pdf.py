from transformers import AutoTokenizer, AutoModelForSeq2SeqLM
import os
from tqdm import tqdm
from utils import convert_text, basic_preprocessing


def translate_document(
    document,
    model_name,
    models_path,
    max_tokens,
    lang_origin_code,
    lang_dest_code,
    loaded_model,
):
    # obtains tokenizer associated to detected text language
    tokenizer = AutoTokenizer.from_pretrained(
        os.path.join("facebook/", model_name), src_lang=lang_origin_code
    )

    if loaded_model:
        model = loaded_model
    else:
        # load models from local when debugging
        model = AutoModelForSeq2SeqLM.from_pretrained(
            os.path.join(models_path, f"{model_name}")
        )

    # Here we start the translating over the paragraphs of the document
    print("Translating paragraphs...")
    tqdm.pandas()
    document["translated_paragraph"] = document.paragraph.progress_apply(
        lambda x: translate(x, tokenizer, max_tokens, model, lang_dest_code)
    )

    return document


def translate(text, tokenizer, max_tokens, model, lang_dest_code):
    """Auxiliary translation function encapsulated in a lambda"""

    # initialization
    translated_text = text
    # do not translate empty or digits
    if not (text == "" or text.isdigit()):
        # first some basic preprocessing
        text = basic_preprocessing(text)
        # obtains untranslated text list in which each element does not
        # exceed a certain token length
        text_chunks = convert_text(text, tokenizer, max_tokens)

        translated_text = []

        for text_chunk in text_chunks:
            inputs = tokenizer(text_chunk, return_tensors="pt")
            translated_tokens = model.generate(
                **inputs,
                forced_bos_token_id=tokenizer.lang_code_to_id[lang_dest_code],
            )
            translated_text_block = tokenizer.batch_decode(
                translated_tokens, skip_special_tokens=True
            )[0]
            translated_text.append(translated_text_block)

        # join and substitute in docx properties
        translated_text = " ".join(translated_text)
    # place de translated value
    return translated_text
