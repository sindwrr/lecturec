from django.http import HttpRequest
from django.shortcuts import render
from pytube import YouTube


def process_file(f):
    with open(f"uploads/{f.name}", "wb+") as dest:
        for chunk in f.chunks():
            dest.write(chunk)


# Create your views here.
def index(request: HttpRequest):
    if request.method == "POST":
        process_file(request.FILES["file_upload"])
    return render(request, "index.html")
