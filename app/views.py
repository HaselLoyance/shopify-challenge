from django.shortcuts import render

def index(request: 'WSGIRequest') -> 'HTMLResponse':
    return render(request, 'app/index.html')

