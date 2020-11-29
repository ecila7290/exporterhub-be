import requests
import base64

from django.core.management.base import BaseCommand

from hub.models import Exporter, Release
from my_settings import TOKEN

api_url='https://api.github.com/repos/'

headers={'Authorization':TOKEN}

class Command(BaseCommand):
    help="Update exporters' GitHub repository information."

    def handle(self,*args, **options):
        exporters = Exporter.objects.select_related('category', 'official').prefetch_related('release_set').order_by('id')
        repo_urls = exporters.values_list('repository_url', flat=True)
        
        for repo_url in repo_urls:
            repo_api_url    = api_url+repo_url.replace('https://github.com/','')
            readme_api_url  = repo_api_url+'/readme'
            release_api_url = repo_api_url+'/releases'
            repository      = requests.get(repo_api_url, headers=headers)

            if repository.status_code==200:
                repo_data    = repository.json()
                readme       = requests.get(readme_api_url, headers=headers)
                readme_data  = readme.json()
                release      = requests.get(release_api_url, headers=headers)
                release_data = release.json()[0]

                if str(exporters.get(repository_url=repo_url).modified_at) < repo_data['updated_at']:
                    exporter=exporters.get(repository_url=repo_url)
                    exporter.update(
                        stars       = repo_data["stargazers_count"],
                        description = repo_data["description"],
                        readme      = base64.b64decode(readme_data["content"])
                    )
                    self.stdout.write(self.style.SUCCESS('SUCCESSFULLY_UPDATED_REPOSITORY_INFO'))

                    if release_data and (str(exporter.release_set.last()) < release_data[0]['created_at']):
                        Release.objects.create(
                            exporter_id=exporter.id,
                            release_url=release_data['created_at'],
                            version=release_data['tag_name'],
                            release_url=release_data['html_url']
                        )
                
                        self.stdout.write(self.style.SUCCESS('SUCCESSFULLY_UPDATED_RELEASE_INFO'))

                else:
                    self.stdout.write(self.style.SUCCESS('NO_CHANGES_MADE'))
            else:
                self.stdout.write(self.style.ERROR(f"ERROR_CHECK_REPOSITORY({repo_url})"))
