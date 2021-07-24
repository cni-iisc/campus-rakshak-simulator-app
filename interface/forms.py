"""
forms.py: describes the strucutre and definition of the forms used in the application
"""
from django import forms
from django.utils.safestring import mark_safe
from django.core.exceptions import ValidationError
from django.utils.translation import ugettext_lazy as _

from .models import userModel, campusData, campusInstantiation, interventions
from .helper import get_or_none, validate_password

import pandas as pd

## Registration form for new users
class RegisterForm(forms.Form):
    first_name = forms.CharField(label=_('First Name'), widget=forms.TextInput())
    last_name = forms.CharField(label=_('Last Name'), widget=forms.TextInput())
    works_at = forms.CharField(label=_('Organization'), widget=forms.TextInput())
    email = forms.EmailField(widget=forms.EmailInput())
    password = forms.CharField(label=_("Password"), widget=forms.PasswordInput(), help_text=mark_safe("Passwords are to be atleast 7 characters long and containing 1 letter and 1 number"))

    def __init__(self, *args, **kwargs):
        super(RegisterForm, self).__init__(*args, **kwargs)

    def clean_password(self):
        password = self.cleaned_data.get("password")
        self._validate_password_strength(self.cleaned_data.get('password'))
        return password

    def clean_email(self):
        email = self.cleaned_data.get("email")
        user = get_or_none(userModel, email=email)
        if user is not None:
            raise ValidationError(_("User with the same email is already registered"))
        return email

    def _validate_password_strength(self, value):
        validate_password(value)

    def save(self, commit=True):
        user = userModel.objects.create_user(
                first_name=self.cleaned_data.get('first_name'),
                last_name=self.cleaned_data.get('last_name'),
                email=self.cleaned_data.get('email'),
                works_at=self.cleaned_data.get('works_at'),
                password=self.cleaned_data.get('password'))
        if commit:
            user.save()
        return user


## User login form
class LoginForm(forms.Form):
    email = forms.EmailField(
        label="Email",
        widget=forms.EmailInput(attrs={'placeholder': 'Email', 'autofocus': ''}))
    password = forms.CharField(
        widget=forms.PasswordInput()
        )

## Form for users to update their account information
class EditUserForm(forms.ModelForm):
    class Meta:
        model = userModel
        fields = ('first_name', 'last_name')
        labels = {
            'first_name': 'First Name',
            'last_name': 'Last Name',
            'works_at': 'Organization',
        }

## Form to instantiate a new synthetic campus in campussim, expects file uploads
class addCampusDataForm(forms.ModelForm):
    class Meta:
        model = campusData
        fields = ('campus_name', 'classes_csv', 'common_areas_csv', 'mess_csv', 'staff_csv', 'students_csv', 'timetable_csv')
        labels = {
            "campus_name": mark_safe("This will be the unique name for each campus<br>"),
            "classes_csv": mark_safe("This contains Class index, Class Strength, Duration, Faculty, Type of class, days.<br> <small>View Sample <a target='_blank' href='/static/sampleData/classes.csv'>Class Detail file</a></small><br>"),
            "common_areas_csv": mark_safe("This contains common areas.<br> <small>View Sample <a target='_blank' href='/static/sampleData/common_areas.csv'>Common Areas details file</a></small><br>"),
            "mess_csv": mark_safe("This contains Mess index,active duration of the mess, and the average time spent in the mess.<br> <small>View Sample <a target='_blank' href='/static/sampleData/mess.csv'>Mess details file</a></small><br>"),
            "staff_csv": mark_safe("This contains Staff index and the department they are associated with, along with their interaction space.<br> <small>View Sample <a target='_blank' href='/static/sampleData/staff.csv'>Staff detail file</a></small><br>"),
            "students_csv": mark_safe("This contains Student index, Hostel index, Mess index, Department index.<br> <small>View Sample <a target='_blank' href='/static/sampleData/student.csv'>Student Detail file</a></small><br>"),
            "timetable_csv": mark_safe("This contains Student index, and the subsequent columns will have the list of classes they take.<br> <small>View Sample <a target='_blank' href='/static/sampleData/timetable.csv'>Timetable detail file</a></small><br>")
        }
    ##TODO [SS]: Review
    def clean(self):
        cleaned_data = super(addCampusDataForm, self).clean()
        return cleaned_data

#         cleaned_data = super(addCampusDataForm, self).clean()
#         classesData=pd.read_csv(self.cleaned_data.get('classes_csv'))
#         # commonAreasData=pd.read_csv(self.cleaned_data.get('common_areas_csv'))
#         colNames=list(classesData.dtypes.to_dict())
#         dataTypes=list(classesData.dtypes.to_dict().items())
#         # print(dataTypes[0][1])
#         for i in range(4):
#             my_type = 'int64'
#             if(dataTypes[i][1] != my_type):
#                 self._errors['classes_csv']=self.error_class(['Data type Error'])
#         if(dataTypes[4][1] != 'obj'):
#             self._errors['classes_csv']=self.error_class(['Data type Error'])
#
#         return cleaned_data

## Form to specify the parameters for launching a simulation
class createSimulationForm(forms.Form):
    simulation_name = forms.CharField(
        label="Simulation name",
        initial="campus Simulation",
        required=True,
    )
    num_days = forms.IntegerField(
        label="Number of days to simulate",
        initial="120",
        required=True,
    )
    num_init_infected = forms.IntegerField(
        label="Initial infection value",
        initial="100",
        required=True,
    )
    num_iterations = forms.IntegerField(
        label="Number of simulation iterations that will be run for the intervention",
        initial="10",
        required=True,
    )
    periodicity = forms.IntegerField(
        label="Periodicity of schedule",
        initial="7",
        required=True,
    )
    enable_testing = forms.BooleanField(
        label="Enable testing in the simulation?",
        initial=True,
    )
    testing_capacity = forms.IntegerField(
        label="Number of tests that can be done per day by the campus",
        initial="100",
        required=True,
    )
    betaScale = forms.FloatField(
        label="Scaling factor for the transmission coefficients at all smaller interaction spaces",
        initial="9",
        required=True,
    )
    min_grp_size = forms.IntegerField(
        label="Minimum number of people that a student is expected to interact with at their hostel",
        initial="10",
        required=True,
    )
    max_grp_size = forms.IntegerField(
        label="Maximum number of people that a student is expected to interact with at their hostel",
        initial="15",
        required=True,
    )
    avg_associations = forms.FloatField(
        label="Average number of people that a student is expected to interact with at their hostel",
        initial="5",
        required=True,
    )
    minimum_hostel_time = forms.FloatField(
        label="Minimum amount of time a student could spend in the hostel",
        initial="1",
        required=True,
    )


    def __init__(self, *args, **kwargs):
        user = kwargs.pop('instance', None)
        super(createSimulationForm, self).__init__(*args, **kwargs)
        campus_queryset = campusInstantiation.objects.filter(created_by=user, status='Complete')
        intv_queryset = interventions.objects.filter(created_by=user)

        campusChoices = []
        for campus in campus_queryset:
            campusChoices.append((campus.id, campus.inst_name))

        interventionChoices = []
        for intv in intv_queryset:
            interventionChoices.append( (intv.id, intv.intv_name) )

        self.fields['instantiatedCampus'] = forms.ChoiceField(
                label = 'Select the campus instantiation to run the simulations',
                choices=campusChoices,
                required=True,
            )
        self.fields['intvName'] = forms.ChoiceField(
                label = 'Select the intervention to simulate',
                choices=interventionChoices,
                required=True,
            )

#
#     def clean(self):
#         cleaned_data = super(addCampusDataForm, self).clean()
#         numDays = self.cleaned_data.get('num_days')
#         avg_no_associations = self.cleaned_data.get('avg_associations')
#         minimum_grp_size = self.cleaned_data.get('min_grp_size')
#         maximum_grp_size = self.cleaned_data.get('max_grp_size')
#         betaScaleValue = self.cleaned_data.get('betaScale')
#         periodicityValue = self.cleaned_data.get('periodicity')
#
#         if(numDays<1):
#             raise forms.ValidationError('Number of Days should be atleast 1')
#
#         if(avg_no_associations<1):
#             raise forms.ValidationError('Number of average associations should be atleast 1')
#
#         if(avg_no_associations>20):
#             raise forms.ValidationError('Maximum limit for average associations is 20')
#
#         if(avg_no_associations>maximum_grp_size or avg_no_associations<minimum_grp_size):
#             raise forms.ValidationError('Average number of associations should be between maximum and minimum group size')
#
#         if((betaScaleValue < 0) or (betaScaleValue > 1)):
#             raise forms.ValidationError('Beta Scale should lie between 0 and 1')
#
#         if(minimum_grp_size <= 0 or minimum_grp_size >= maximum_grp_size):
#             raise forms.ValidationError('Minimum Group size should be greater than 0 and less than Maximum Group size')
#
#         if(maximum_grp_size <= 0 or minimum_grp_size >= maximum_grp_size):
#             raise forms.ValidationError('Maximum Group size should be greater than 0 and greater than Minimum Group size')
#
#         if(periodicityValue != 7):
#             raise forms.ValidationError('Please set periodicity value to 7')
#
#         return cleaned_data
