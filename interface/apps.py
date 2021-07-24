"""
apps.py: serves as the link with `config` and the `application logic`
"""
from django.apps import AppConfig
from django.db.models.signals import post_migrate

## This method creates user groups if they are not present
## Campussim defines three user groups
## 1. user == end users (campus administrators and authorities) of the tool
## 2. admin == developers of campussim 
def create_user_groups(sender, **kwargs):
    from django.contrib.auth.models import Group

    Group.objects.get_or_create(name='user')
    Group.objects.get_or_create(name='admin')

class InterfaceConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'interface'

    def ready(self):
        post_migrate.connect(create_user_groups, sender=self)
