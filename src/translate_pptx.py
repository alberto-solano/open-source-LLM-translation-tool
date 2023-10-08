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
    # initialize the class
    translator = pptx_translator(
        model_name,
        models_path,
        max_tokens,
        lang_origin_code,
        lang_dest_code,
        loaded_model,
    )

    translator.translate_document(document)

    return document


class pptx_translator:
    """
    Extracted from: https://github.com/ThibaudLamothe/translate-pptx
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
            # load here the model when debugging
            self.model = AutoModelForSeq2SeqLM.from_pretrained(
                os.path.join(models_path, f"{model_name}")
            )
        self.max_tokens = max_tokens
        self.lang_dest_code = lang_dest_code

    def translate_document(self, document):
        print("Translating slides...")
        for slide in tqdm(document.slides):
            self.browse_slide(slide)

    def browse_shape(self, shape):
        """PowerPoint Shapes might be of different kind.
            Each kind of shape has its own way to deal with text.
            This functions aims to root shapes to the right text extractor.

        PARAMETERS:
            shape : pptx.shapes.shapetree.SlideShapes
                Original value.
        RETURNS:
            pptx.shapes.shapetree.SlideShapes
                Modified value.
        """
        # Text into text shape (basic case)
        if shape.has_text_frame:
            return self.change_text_frame_text(shape.text_frame)

        # Text into tables (modification by cell)
        if shape.has_table:
            return self.change_table_text(shape.table)

        # Grouped shapes (using recursivity)
        if shape.shape_type == 6:
            return self.browse_slide(shape)

        return shape

    def change_text_frame_text(self, text_frame):
        """
        Operate text modifications to a shape which contains/is a text_frame.

        PARAMETERS:
        shape : pptx.shapes.shapetree.SlideShapes
            Original value.
        RETURNS:
        text_frame: pptx.shapes.shapetree.SlideShapes
            Modified values.
        """
        # For each paragraph of the shape's text_frame
        for idx in range(len(text_frame.paragraphs)):
            # Prepare new text
            old_text = text_frame.paragraphs[idx].text
            new_text = self.make_text_modification(old_text)

            # Store it in presentation without modifying font parameters
            para = text_frame.paragraphs[idx]
            if len(para.runs) > 0:
                self.replace_paragraph_text_retaining_initial_formatting(
                    para, new_text
                )
            else:
                text_frame.paragraphs[idx].text = new_text

        return text_frame

    def browse_slide(self, slide):
        """All PowerPoint slides are composed of shapes. We are going inside
        each shape in order to translate the text on them

        PARAMETERS:
        slide : pptx.slide.Slides (or pptx.shapes.shapetree.GroupShapes)
            Original values
        RETURNS:
        slide: pptx.slide.Slides (or pptx.shapes.shapetree.GroupShapes)
            Modified values.
        """
        for shape in slide.shapes:
            shape = self.browse_shape(shape)
        return slide

    def change_table_text(self, table):
        """Operate text translation to a shape which contains/is a table.

        PARAMETERS:
        shape : pptx.shapes.shapetree.SlideShapes
            Original value.
        RETURNS:
        table : pptx.shapes.shapetree.SlideShapes
            Modified values.
        """

        # Get table information
        # table = shape.table
        nb_rows = len(table.rows)
        nb_col = len(table.columns)

        # And update each cell
        for col in range(nb_col):
            for row in range(nb_rows):
                self.change_text_frame_text(table.cell(row, col).text_frame)
        return table

    def replace_paragraph_text_retaining_initial_formatting(
        self, paragraph, new_text
    ):
        """Given a paragraph

        PARAMETERS:
        paragraph : pptx.text.text._Paragraph
            Read paragraph with its original value and font parameters
        new_text : str
            Text to input into the paragraph

        INPLACE FUNCTION. NO OUTPUT.
        """
        p = (
            paragraph._p
        )  # the lxml element containing the `<a:p>` paragraph element
        # remove all but the first run
        for idx, run in enumerate(paragraph.runs):
            if idx == 0:
                continue
            p.remove(run._r)
        paragraph.runs[0].text = new_text

    def make_text_modification(self, text):
        # initialization
        translated_text = text
        # do not translate empty or digits
        if not (text == "" or text.isdigit()):
            # preprocessing
            cleaned_text = basic_preprocessing(text)
            # obtains untranslated text list in which each element does not
            # exceed a certain token length
            text_chunks = convert_text(
                cleaned_text, self.tokenizer, self.max_tokens
            )
            translated_chunks = []
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
                translated_chunks.append(translated_text_block)

            # join
            translated_text = " ".join(translated_chunks)

        return translated_text
