import os
import tempfile

import spacy
import whisper
from django.http import HttpRequest, HttpResponse
from django.shortcuts import render
from pytube import YouTube

# Load SpaCy models for English and Russian
nlp_en = spacy.load("en_core_web_sm")
nlp_ru = spacy.load("ru_core_news_sm")


def process_file(f):
    upload_dir = "uploads/"
    if not os.path.exists(upload_dir):
        os.makedirs(upload_dir)

    file_path = os.path.join(upload_dir, f.name)
    with open(file_path, "wb+") as dest:
        for chunk in f.chunks():
            dest.write(chunk)
    return file_path


def process_youtube_link(link):
    yt = YouTube(link)
    audio_stream = yt.streams.filter(only_audio=True).first()

    temp_dir = "yt/"
    if not os.path.exists(temp_dir):
        os.makedirs(temp_dir)

    # Sanitize file name to avoid issues with special characters
    sanitized_title = "".join(char if char.isalnum() else "_" for char in yt.title)
    file_path = os.path.join(temp_dir, sanitized_title + ".mp4")

    audio_stream.download(output_path=temp_dir, filename=sanitized_title + ".mp4")
    return file_path


def segment_into_paragraphs(text, lang="en", min_sentences=3):
    if lang == "en":
        nlp = nlp_en
    elif lang == "ru":
        nlp = nlp_ru
    else:
        raise ValueError("Unsupported language")

    doc = nlp(text)
    paragraphs = []
    paragraph = []
    sentence_count = 0

    for sent in doc.sents:
        paragraph.append(sent.text)
        sentence_count += 1
        if sentence_count >= min_sentences and sent.text.endswith((".", "!", "?")):
            paragraphs.append(" ".join(paragraph))
            paragraph = []
            sentence_count = 0
    if paragraph:
        paragraphs.append(" ".join(paragraph))
    return "\n\n".join(paragraphs)


def index(request: HttpRequest):
    if request.method == "POST":
        uploaded_file = request.FILES.get("file_upload")
        youtube_link = request.POST.get("youtube_link")
        model_choice = request.POST.get("model", "small")
        min_sentences = int(request.POST.get("min_sentences", 3))

        if uploaded_file:
            filename = process_file(uploaded_file)
        elif youtube_link:
            filename = process_youtube_link(youtube_link)
        else:
            return HttpResponse("No file uploaded or link provided", status=400)

        model = whisper.load_model(model_choice)
        result = model.transcribe(filename)

        # Determine the language from the transcribed text
        lang = "en" if all(ord(char) < 128 for char in result["text"]) else "ru"

        # Segment the transcribed text into paragraphs
        segmented_text = segment_into_paragraphs(
            result["text"], lang=lang, min_sentences=min_sentences
        )

        transcript_dir = "transcripts/"
        if not os.path.exists(transcript_dir):
            os.makedirs(transcript_dir)

        file_path = os.path.join(transcript_dir, "text.txt")
        with open(file_path, "w") as dest:
            dest.write(segmented_text)

        with open(file_path, "rb") as f:
            response = HttpResponse(f.read(), content_type="application/octet-stream")
            response["Content-Disposition"] = (
                f"attachment; filename={os.path.basename(file_path)}"
            )
            return response

    return render(request, "index.html")


def info(request: HttpRequest):
    return render(request, "info.html")
