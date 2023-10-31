import os
from tqdm import tqdm
import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont


def save_translated_doc(document, output_path, document_type):
    """Function to save translated and untranslated documents in a certain
    location.

    Parameters
    ----------
    document : File containing all the document info, could be a pandas
    dataframe if the input document was a pdf or a word or pptx document

    output_path : str
        Path to where the translation will be stored at

    document_type : str
        Extension of the input document
    Returns
    -------
    """
    if not os.path.exists(os.path.dirname(output_path)):
        os.makedirs(os.path.dirname(output_path))

    if document_type == "docx":
        # when word document object we just call the save method from the class
        document.save(output_path)
    elif document_type == "pptx":
        # when pptx document object we just call the save method from the class
        document.save(output_path)
    else:
        # when the document is PDF we must overwrite the translated text over
        # the original text on every image given their positions
        overwrite_text_on_images(document)

    print("Document saved.")


def overwrite_text_on_images(document):
    """Function needed for replacing the translated pdf text chunks over
    the images extracted from the input pdf

    Parameters
    ----------
    document : pd.DataFrame
    Input document after OCR

    Returns
    -------
    The document images are automatically saved
    """

    # define necessary paths
    filepath = os.path.abspath(__file__)
    projpath = os.path.abspath(os.path.join(filepath, "..", ".."))
    img_path = os.path.join(projpath, "input", "tmp")
    output_path = os.path.join(projpath, "media", "translated_documents")

    # tmp folder contains the images extracted from the pdf so we will iter
    # over them

    images = [file for file in os.listdir(img_path) if file.endswith(".png") and file.startswith('page_')]
    pdf_file = [file for file in os.listdir(img_path) if file.endswith(".pdf")][0]
    translated_images = []
    print("Overriting text on PDF images...")
    # images are named 'page_i.png', order the image list
    ordered_imgs = sorted(
        images, key=lambda x: int(x.replace("page_", "").replace(".png", ""))
    )
    for image in tqdm(ordered_imgs):
        # Load the image
        path = os.path.join(img_path, image)
        img = cv2.imread(path)
        # get the page(all in the format ``page_{}.png'')
        page = int(image.split(".")[0].replace("page_", ""))
        # filter for the boxes on the page
        aux = document[document.page == page]
        # blank page case
        if len(aux) < 1:
            continue
        # overlaping correction
        aux = overalapping_correction(aux)
        # iter over the boxes of that page
        for idx, attributes in aux.iterrows():
            upper_left = (attributes.xmin, attributes.ymax)
            bottom_right = (attributes.xmax, attributes.ymin)
            translated_text = attributes.translated_paragraph
            # inpaint the original image
            img = inpaint_algorithm(
                img, upper_left, bottom_right, translated_text
            )

        # at the end we save the image
        cv2.imwrite(os.path.join(img_path, "translated_" + image), img)
        # open the image with PIL
        pil_im = Image.open(os.path.join(img_path, "translated_" + image))
        pil_im = pil_im.convert(
            "RGB"
        )  # to prevent errors: cannot save mode RGBA
        translated_images.append(pil_im)

    # make a single pdf from img list
    image = translated_images[0]
    translated_images.pop(0)
    image.save(
        os.path.join(output_path, "translated_" + pdf_file),
        "PDF",
        resolution=100.0,
        save_all=True,
        append_images=translated_images,
    )


def inpaint_algorithm(image, upper_left, bottom_right, translated_text):
    """Function to interpolate the background of a text box with a rectangular mask"""
    # band of pixels in which compute the median
    outer_pixels = 5
    # get the median of the pixels just in the outer border of our bbox:
    #   _____
    #
    # |    |
    # ____

    # conditions over the height
    up_contour = image[
        upper_left[1] : (upper_left[1] + outer_pixels),
        upper_left[0] : bottom_right[0],
        :,
    ].reshape(outer_pixels, -1, 3)
    bottom_contour = image[
        (bottom_right[1] - outer_pixels) : bottom_right[1],
        upper_left[0] : bottom_right[0],
        :,
    ].reshape(outer_pixels, -1, 3)
    # conditions over the width
    left_contour = image[
        bottom_right[1] : upper_left[1],
        (upper_left[0] - outer_pixels) : upper_left[0],
        :,
    ].reshape(outer_pixels, -1, 3)
    right_contour = image[
        bottom_right[1] : upper_left[1],
        bottom_right[0] : (bottom_right[0] + outer_pixels),
        :,
    ].reshape(outer_pixels, -1, 3)

    # concatenate over the 2º axis
    border = np.concatenate(
        (up_contour, bottom_contour, left_contour, right_contour), axis=1
    )

    # calculate the median color of the pixel borders
    median_color = np.median(border, axis=(0, 1))

    # draw a rectangle in that colour
    image = cv2.rectangle(
        image, upper_left, bottom_right, color=median_color, thickness=-1
    )

    # write text on the image
    image = write_text_on_rectangle(
        image,
        translated_text,
        {
            "left": upper_left[0],
            "top": bottom_right[1],
            "right": bottom_right[0],
            "bottom": upper_left[1],
        },
        "arial.ttf",
    )

    # back to numpy array
    image = np.array(image)

    return image


def write_text_on_rectangle(image, text, coords, font):
    """
    coords: (left=w, top=x, right=y, bottom=z)
    """
    # opens the image
    img = Image.fromarray(image)

    max_width = coords.get("right") - coords.get("left")
    max_height = coords.get("bottom") - coords.get("top")

    FONT_SIZE = 72
    FONT_FAMILY = f"/home/ubuntu/LLM-translator/fonts/{font}"

    # initialization
    line_heights = 1e10
    draw = ImageDraw.Draw(img)

    while line_heights > max_height:
        # create the ImageFont instance
        font = ImageFont.truetype(FONT_FAMILY, size=FONT_SIZE)

        # get shorter lines
        lines = text_wrap(text, font, max_width)

        # TODO: add a margin to add between lines
        origin = (coords.get("left"), coords.get("top"))
        line_heights = get_y_and_heights(lines, font, draw, origin)

        # decrease the font several points
        FONT_SIZE -= 2

    # finally write the text
    short_text = "\n".join(lines)
    draw.text(
        origin,
        short_text,
        font=font,
        fill="black",
    )
    return img


def get_y_and_heights(text_wrapped, font, draw, origin):
    """
    Gets the vertical size of a given text:
    https://stackoverflow.com/questions/43060479/
    """
    short_text = "\n".join(text_wrapped)
    bbox = draw.textbbox(origin, short_text, font=font)
    # bbox returns (left, top, right, bottom) bounding box
    height_text = bbox[3] - bbox[1]
    return height_text


def text_wrap(text, font, max_width):
    lines = []
    # If the width of the text is smaller than image width
    # we don't need to split it, just add it to the lines array
    # and return
    if font.getsize(text)[0] <= max_width:
        lines.append(text)
    else:
        # split the line by spaces to get words
        words = text.split(" ")
        i = 0
        # append every word to a line while its width is shorter than image
        # width
        while i < len(words):
            line = ""
            while (
                i < len(words)
                and font.getsize(line + words[i])[0] <= max_width
            ):
                line = line + words[i] + " "
                i += 1
            if not line:
                line = words[i]
                i += 1
            # when the line gets longer than the max width do not append the
            # word, add the line to the lines array
            lines.append(line.strip())
    return lines


def overalapping_correction(df):
    """corrects the overlapping of bboxes by readjusting their ypos"""
    aux = df.copy()

    # initialize the first bottom value of the bbox in the 'y' coord
    ymax_prev, xmin_prev, xmax_prev = aux.iloc[0].loc[["ymax", "xmin", "xmax"]]

    for row in aux[1:].itertuples():
        ymin, ymax, xmin, xmax = row.ymin, row.ymax, row.xmin, row.xmax

        # overlapping conditions
        condition_1 = ymin < ymax_prev
        condition_2 = (xmin < xmax_prev) & (xmax > xmax_prev)
        condition_3 = (xmax > xmin_prev) & (xmax < xmax_prev)
        overlapping_condition = condition_1 & (condition_2 | condition_3)

        if overlapping_condition:
            # update the row in the dataframe
            aux["ymin"].at[row.Index] = ymax_prev

        # update the prev
        ymax_prev, xmin_prev, xmax_prev = ymax, xmin, xmax

    return aux
