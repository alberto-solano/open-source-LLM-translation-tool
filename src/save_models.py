from transformers import AutoModelForSeq2SeqLM
import os
import wget

filepath = os.path.abspath(__file__)
projpath = os.path.abspath(os.path.join(filepath, "..", ".."))
models_path = os.path.join(projpath, "models")

if not os.path.exists(models_path):
    os.makedirs(models_path)

# checkpoint = "facebook/nllb-200-distilled-600M"
# checkpoint = 'facebook/nllb-200-1.3B'
# checkpoint = 'facebook/nllb-200-1.3B'
checkpoint = "facebook/nllb-200-distilled-1.3B"

output_path = os.path.join(models_path, checkpoint.split("/")[-1])
fasttext = os.path.join(models_path, "lid218e.bin")
if not os.path.exists(fasttext):
    print("downloading lid218bin")
    wget.download(
        "https://dl.fbaipublicfiles.com/nllb/lid/lid218e.bin", out=fasttext
    )

# download the model on local if you you want by uncomment the following lines:
#if not os.path.exists(os.path.join(output_path, "pytorch_model.bin")):
#    model = AutoModelForSeq2SeqLM.from_pretrained(checkpoint)
#    model.save_pretrained(output_path)
#    del model
