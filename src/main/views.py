import os

import whisper
from django.http import HttpRequest, HttpResponse
from django.shortcuts import render


def process_file(f):
    upload_dir = "uploads/"
    if not os.path.exists(upload_dir):
        os.makedirs(upload_dir)

    file_path = os.path.join(upload_dir, f.name)
    with open(file_path, "wb+") as dest:
        for chunk in f.chunks():
            dest.write(chunk)
    return file_path


def index(request: HttpRequest):
    if request.method == "POST":
        filename = process_file(request.FILES["file_upload"])
        model = whisper.load_model("base")
        result = model.transcribe(filename)
        return HttpResponse(result["text"])

    return render(request, "index.html")
