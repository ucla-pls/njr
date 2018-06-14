from django.shortcuts import render
from django.http import HttpResponse
from app.models import Class

def index(request):
    return render(request, "app/index.html", { 'example' : Class.objects.all()[:5] })
