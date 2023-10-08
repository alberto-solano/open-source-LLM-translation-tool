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
    # Here we start the translating over all the paragraphs of the document
    # by sections, see: https://stackoverflow.com/questions/34779724

    # initialize the class
    translator = docx_translator(
        model_name,
        models_path,
        max_tokens,
        lang_origin_code,
        lang_dest_code,
        loaded_model,
    )

    translator.translate_document(document)

    return document


class docx_translator:
    """
    With the help from: https://stackoverflow.com/questions/34779724
    """

    def __init__(
        self,
        model_name,
        models_path,
        max_tokens,
        lang_origin_code,
        lang_dest_code,
        loaded_model,
    ):
        self.tokenizer = AutoTokenizer.from_pretrained(
            os.path.join("facebook/", model_name), src_lang=lang_origin_code
        )
        if loaded_model:
            self.model = loaded_model
        else:
            # load the model here when debugging
            self.model = AutoModelForSeq2SeqLM.from_pretrained(
                os.path.join(models_path, f"{model_name}")
            )
        self.max_tokens = max_tokens
        self.lang_dest_code = lang_dest_code

    def translate_document(self, document):
        # paragraphs
        self.body_content(document)
        # tables
        self.body_tables(document)
        # headers
        self.headers(document)
        # footers
        self.footers(document)

    def body_content(self, document):
        print("\t☺Processing paragraphs...")
        for paragraph in tqdm(document.paragraphs):
            self.Execute(paragraph)

    def body_tables(self, document):
        print("\t☺Processing body tables...")
        for table in tqdm(document.tables):
            for row in table.rows:
                for cell in row.cells:
                    for paragraph in cell.paragraphs:
                        self.Execute(paragraph)

    def headers(self, document):
        print("\t☺Processing headers ...")
        for section in tqdm(document.sections):
            for paragraph in section.header.paragraphs:
                self.Execute(paragraph)

            for table in section.header.tables:
                for row in table.rows:
                    for cell in row.cells:
                        for paragraph in cell.paragraphs:
                            self.Execute(paragraph)

    def footers(self, document):
        print("\t☺Processing footers ...")
        for section in document.sections:
            for paragraph in section.footer.paragraphs:
                self.Execute(paragraph)

            for table in section.footer.tables:
                for row in table.rows:
                    for cell in row.cells:
                        for paragraph in cell.paragraphs:
                            self.Execute(paragraph)

    def Execute(self, paragraph):
        # here we do the translation and preprocessing at the run level,
        # a lower level than the paragraph itself. That's because each
        # paragraph is composed by multiple runs
        for run in paragraph.runs:
            original_text = run.text
            # preprocessing
            original_text = basic_preprocessing(original_text)
            # initialization
            translated_text = original_text
            # dont translate the following cases
            # empty
            case1 = original_text == ""
            # only digits, symbols, and definitely, less than 4 letters
            case2 = sum([letter.isalpha() for letter in original_text]) <= 3
            cases = case1 or case2
            if not cases:
                # obtains untranslated text list in which each element does not
                # exceed a certain token length
                text_chunks = convert_text(
                    original_text, self.tokenizer, self.max_tokens
                )

                translated_text = []

                for text_chunk in text_chunks:
                    inputs = self.tokenizer(text_chunk, return_tensors="pt")
                    translated_tokens = self.model.generate(
                        **inputs,
                        forced_bos_token_id=self.tokenizer.lang_code_to_id[
                            self.lang_dest_code
                        ],
                    )
                    translated_text_block = self.tokenizer.batch_decode(
                        translated_tokens, skip_special_tokens=True
                    )[0]
                    translated_text.append(translated_text_block)

                # join and substitute in docx properties
                translated_text = " ".join(translated_text)
                # replace the text on the run
                run.text = translated_text
