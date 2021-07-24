"""
admin.py: registers the models to the Django application
`models' refer to the definition of database tables specified in `models.py'
"""
from django.contrib import admin
from .models import *

## Adds the models to the Django admin site
admin.site.register(campusData)
admin.site.register(campusInstantiation)
admin.site.register(interventions)
admin.site.register(testingParams)
admin.site.register(simulationParams)
admin.site.register(simulationResults)

## This defines the behaviors for the fields defined in the user model
@admin.register(userModel)
class UserModelAdmin(admin.ModelAdmin):
    list_display = ('email', 'first_name', 'last_name', 'works_at')
    readonly_fields = ('created_at',)
    search_fields = ['email', 'first_name', 'last_name', 'works_at']

## RegisterOrigin used for generating and maintaining user-access tokens
## The user-access tokens are used to verify a new user and for resetting user password
## This works when the email templates are enabled
@admin.register(RegisterOrigin)
class RegisterOriginAdmin(admin.ModelAdmin):
    list_display = ('name', 'redirect_url')
