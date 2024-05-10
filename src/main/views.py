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
        uploaded_file = request.FILES.get("file_upload")
        if uploaded_file:
            filename = process_file(uploaded_file)
            model = whisper.load_model("small")
            result = model.transcribe(filename)

            transcript_dir = "transcripts/"
            if not os.path.exists(transcript_dir):
                os.makedirs(transcript_dir)

            file_path = os.path.join(transcript_dir, "text.txt")
            with open(file_path, "w") as dest:
                dest.write(result["text"])

            with open(file_path, "rb") as f:
                response = HttpResponse(
                    f.read(), content_type="application/octet-stream"
                )
                response["Content-Disposition"] = (
                    f"attachment; filename={os.path.basename(file_path)}"
                )
                return response
        else:
            return HttpResponse("No file uploaded", status=400)

    return render(request, "index.html")
