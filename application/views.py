from django.shortcuts import render, redirect
from .models import Translation
from django.conf import settings
from django.http import (
    FileResponse,
    HttpResponseNotFound,
    HttpResponse,
    JsonResponse,
)
import os
from .forms import DocumentForm
from translation_app import translate_document
import json
from transformers import AutoTokenizer
from utils import load_model, convert_text, language_detection


# JSON file
with open("json/reversed_available_languages.json", "r") as f:
    available_languages = json.load(f)
# JSON file
with open("json/available_languages.json", "r") as f:
    available_language_codes = json.load(f)

# load the model in the first place
model_name = "nllb-200-distilled-600M"
max_tokens = 150
model = load_model(f"facebook/{model_name}")


def home(request):
    # get the first 10 documents by date
    translations = Translation.objects.order_by("-translation_date")[:10]
    context = {"translations": translations}
    return render(request, "home.html", context)


def detect_language(request):
    if request.method == "POST":
        input_text = request.POST.get("input_text", "")
        detected_language_code = language_detection([input_text])
        detected_language = available_language_codes.get(
            detected_language_code
        )
        return JsonResponse({"detected_language": detected_language})

    return JsonResponse({"error": "Invalid request method."})


def translation_interface(request):
    tokenizer = None
    context = {
        "available_languages": available_languages,
        "tokenizer_loaded": False,
    }
    if request.method == "POST":
        translated_text = []
        input_text = request.POST.get("input_text", "")
        selected_language = request.POST.get("original_language", "")
        target_language = request.POST.get("target_language", "")
        # load the tokenizer
        tokenizer = AutoTokenizer.from_pretrained(
            os.path.join("facebook/", model_name),
            src_lang=selected_language,
        )

        text_chunks = convert_text(input_text, tokenizer, max_tokens)
        for text_chunk in text_chunks:
            inputs = tokenizer(text_chunk, return_tensors="pt")
            translated_tokens = model.generate(
                **inputs,
                forced_bos_token_id=tokenizer.lang_code_to_id[target_language],
            )

            translated_text_block = tokenizer.batch_decode(
                translated_tokens, skip_special_tokens=True
            )[0]
            translated_text.append(translated_text_block)

        # join and substitute in docx properties
        translated_text = " ".join(translated_text)
        return JsonResponse({"translated_text": translated_text})

    return render(request, "translation_interface.html", context=context)


def upload_document(request):
    if request.method == "POST":
        form = DocumentForm(request.POST, request.FILES)
        if form.is_valid():
            # path to temp folder
            temp_folder = "input/tmp/"

            if not os.path.exists(temp_folder):
                os.makedirs(temp_folder)

            # save the file on temp folder
            temp_file_path = os.path.join(
                temp_folder, form.cleaned_data["translated_document"].name
            )
            with open(temp_file_path, "wb") as temp_file:
                for chunk in form.cleaned_data["translated_document"].chunks():
                    temp_file.write(chunk)

            # get the target language selected on the form
            target_language = request.POST.get("target_language")

            # translate the document
            translate_document(
                form.cleaned_data["translated_document"].name,
                target_language,
                model,
            )

            # add a new row in the table when saving the file in `translate_document`
            # added manually the preffix translated
            translated_file_name = (
                "translated_" + form.cleaned_data["translated_document"].name
            )
            Translation.objects.create(
                translated_document=translated_file_name
            )
            return redirect("home")
    else:
        form = DocumentForm()

    return render(
        request,
        "upload_document.html",
        {"form": form, "available_languages": available_languages},
    )


def serve_translated_document(request, filename):
    file_path = os.path.join(settings.MEDIA_ROOT, filename)
    if os.path.exists(file_path):
        response = FileResponse(open(file_path, "rb"))
        return response
    else:
        # file not found
        return HttpResponseNotFound("File not found")


def delete_all_translations(request):
    if request.method == "POST":
        # remove all registries in Translation table
        Translation.objects.all().delete()
        # remove all the files
        folder = "media/translated_documents/"
        for file in os.listdir(folder):
            os.remove(os.path.join(folder, file))

        response_data = {"message": "Deleted all registries"}
        return HttpResponse(
            json.dumps(response_data), content_type="application/json"
        )
    return redirect("home")
