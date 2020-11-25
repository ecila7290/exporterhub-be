import json
import requests
import base64

from django.views import View
from django.http import JsonResponse

from .models import Exporter, Release, Category
from my_settings import TOKEN

api_url='https://api.github.com/repos/'

headers={'Authorization':TOKEN}

class RepositoryView(View):
    def get_repo(self, repo_url):
        repo_api_url     = api_url+repo_url.replace('https://github.com/','')
        readme_api_url   = repo_api_url+'/readme'
        release_api_url  = repo_api_url+'/releases'
        default_logo_url = "https://avatars3.githubusercontent.com/u/3380462?v=4"
        repo             = requests.get(repo_api_url, headers=headers)
        
        if repo.status_code==200:
            repo_data    = repo.json()
            readme       = requests.get(readme_api_url, headers=headers)
            readme_data  = readme.json()
            release      = requests.get(release_api_url, headers=headers)
            release_data = release.json()
            
            data={
                "name"           : repo_data["name"],
                "logo_url"       : default_logo_url,
                "stars"          : repo_data["stargazers_count"],
                "description"    : repo_data["description"],
                "readme_url"     : repo_url+"/blob/master/README.md",
                "readme"         : readme_data["content"],
                "release"        : [{
                        "release_version": release["tag_name"],
                        "release_date"   : release["created_at"],
                        "release_url"    : release["html_url"]
                } for release in release_data]
            }
            return data
        return False

    def post(self, request):
        try:
            categories={
                "Database"     : 1,
                "Hardware"     : 2,
                "HTTP"         : 3,
                "Library"      : 4,
                "Logging"      : 5,
                "Messaging"    : 6,
                "Miscellaneous": 7,
                "Monitoring"   : 8,
                "Software"     : 9,
                "Storage"      : 10
            }

            data      = json.loads(request.body)
            repo_url  = data["repo_url"]
            category  = data["category"]

            if Exporter.objects.filter(repository_url=repo_url).exists():
                return JsonResponse({'message':'EXISTING_REPOSITORY'}, status=400)
                
            if "prometheus/" in repo_url:
                official = 1
            else:
                official = 2

            repo_info = self.get_repo(repo_url)

            if repo_info:
                exporter=Exporter.objects.create(
                    category_id    = categories[category],
                    official_id    = official,
                    name           = repo_info["name"],
                    logo_url       = repo_info["logo_url"],
                    stars          = repo_info["stars"],
                    repository_url = repo_url,
                    description    = repo_info["description"],
                    readme_url     = repo_info["readme_url"],
                    readme         = base64.b64decode(repo_info["readme"]),
                )
            
                release=sorted(repo_info["release"], key=lambda x: x["release_date"])
                for info in release:
                    Release(
                        exporter_id = exporter.id,
                        release_url = info["release_url"],
                        version     = info["release_version"],
                        date        = info["release_date"]
                    ).save()
                return JsonResponse({'message':'SUCCESS'}, status=201)

            return JsonResponse({'message':'WRONG_REPOSITORY'}, status=400)

        except KeyError:
            return JsonResponse({'message':'KEY_ERROR'}, status=400)

    def get(self, request):
        try:
            exporters=Exporter.objects.all()
            data={"exporters":
                [
                    {
                        "exporter_id"    : exporter.id,
                        "name"           : exporter.name,
                        "logo_url"       : exporter.logo_url,
                        "category"       : exporter.category.name,
                        "official"       : exporter.official.name,
                        "stars"          : exporter.stars,
                        "repository_url" : exporter.repository_url,
                        "description"    : exporter.description,
                        "release"        : [{
                            "release_version": release.version,
                            "release_date"   : release.date,
                            "release_url"    : release.release_url
                        } for release in exporter.release_set.all()],
                    }
                for exporter in exporters]
            }
            return JsonResponse(data, status=200)

        except Exception as e:
            return JsonResponse({'message':f"{e}"}, status=400)

    def delete(self, request):
        try:
            exporter_id=request.GET['exporter_id']
            exporter=Exporter.objects.get(id=exporter_id)
            exporter.delete()
            return JsonResponse({'message':'SUCCESS'}, status=200)

        except KeyError as e:
            return JsonResponse({'message':f"{e}_MISSING"}, status=400)
        except Exporter.DoesNotExist:
            return JsonResponse({'message':'NO_EXPORTER'}, status=400)

class CategoryView(View):
    def get(self, request):
        categories=Category.objects.all()
        data={"categories":
        [{   
            "category_id"  : category.id,
            "category_name": category.name
        }
        for category in categories]
        }
        return JsonResponse(data, status=200)

class MainView(View):
    def get(self, request):
        try:
            exporters=Exporter.objects.all()
            data={"exporters":
                [
                    {
                        "exporter_id"    : exporter.id,
                        "name"           : exporter.name,
                        "logo_url"       : exporter.logo_url,
                        "category"       : exporter.category.name,
                        "official"       : exporter.official.name,
                        "stars"          : exporter.stars,
                        "repository_url" : exporter.repository_url,
                        "description"    : exporter.description,
                        "release"        : [{
                            "release_version": release.version,
                            "release_date"   : release.date,
                            "release_url"    : release.release_url
                        } for release in exporter.release_set.all()],
                    }
                for exporter in exporters]
            }

            return JsonResponse(data, status=200)
        except Exception as e:
            return JsonResponse({'message':f"{e}"}, status=400)

class DetailView(View):
    def get(self, request, exporter_id):
        try:
            readme=Exporter.objects.get(id=exporter_id).readme
            return JsonResponse({"data":readme.decode('utf-8')}, status=200)

        except Exporter.DoesNotExist:
            return JsonResponse({'message':'NO_EXPORTER'}, status=400)