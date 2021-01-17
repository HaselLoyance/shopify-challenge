from django.http import JsonResponse
from django.shortcuts import render
from django.views.decorators.http import require_POST
from app.business import save_images
import json


def get_request_body(request: 'WSGIRequest') -> dict:
    return json.loads(request.body.decode('utf-8'))


def index(request: 'WSGIRequest') -> 'HTMLResponse':
    return render(request, 'app/index.html')


@require_POST
def new_images(request: 'WSGIRequest') -> JsonResponse:
    data = get_request_body(request)

    save_images(data['images'])

    return JsonResponse({'status': '200'}, status=200)
