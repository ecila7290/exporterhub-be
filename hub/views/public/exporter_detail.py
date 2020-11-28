import json

from django.views import View
from django.http import JsonResponse

from hub.models import Exporter

class DetailView(View):
    def get(self, request, exporter_id):
        try:
            readme=Exporter.objects.get(id=exporter_id).readme
            return JsonResponse({"data":readme.decode('utf-8')}, status=200)

        except Exporter.DoesNotExist:
            return JsonResponse({'message':'NO_EXPORTER'}, status=400)