"""
mixins.py: defines classes that share methods to inheriting classes in the application
- Eg: 'AnonymousRequired' mixin ensures that the class (specified in views.py) that inherits
this mixin is available only when the user is un-authenticated.
"""
from django.urls import reverse
from django.shortcuts import redirect
from django.http import Http404

class AddSnippetsToContext:
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        return context


class AddUserToContext:
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['user'] = self.request.user
        return context


class AnonymousRequired:
    def dispatch(self, *args, **kwargs):
        if self.request.user.is_authenticated:
            return redirect(reverse('profile'))
        return super().dispatch(*args, **kwargs)
