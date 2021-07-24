"""
managers.py: handles the create operation on the models
- Currently used only for user creation
"""
from django.contrib.auth.models import BaseUserManager, Group

class UserManager(BaseUserManager):
    def __create_user(self, email, password, is_staff=False, is_active=False, is_superuser=False, **kwargs):
        if not email:
            raise ValueError('Users must have an email address')

        email = self.normalize_email(email)
        user = self.model(email=email, is_active=is_active, is_staff=is_staff, is_superuser=is_superuser, **kwargs)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_user(self, email, password, is_staff=False, **kwargs):
        user = self.__create_user(email, password, is_staff=is_staff, is_active=False, is_superuser=False)
        grp = Group.objects.get(name='user') #default user group
        grp.user_set.add(user)
        return user

    def create_superuser(self, email, password):
        user = self.__create_user(email, password, is_staff=True, is_active=True, is_superuser=True)
        grp = Group.objects.get(name='admin')
        grp.user_set.add(user)
        return user

    def create(self, **kwargs):
        return self.create_user(**kwargs)
