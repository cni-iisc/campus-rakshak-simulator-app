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
        widget=forms.EmailInput(attrs={'placeholder': '', 'autofocus': ''}))
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
            "campus_name": mark_safe("Name for the instatiation"),
            "classes_csv": mark_safe("This contains Class index, Class Strength, Duration, Faculty, Type of class, days.<br> <small>View Sample <a target='_blank' href='/static/sampleData/classes.csv'>Class Detail file</a></small><br>"),
            "common_areas_csv": mark_safe("This contains common areas.<br> <small>View Sample <a target='_blank' href='/static/sampleData/common_areas.csv'>Common Areas details file</a></small><br>"),
            "mess_csv": mark_safe("This contains Mess index,active duration of the mess, and the average time spent in the mess.<br> <small>View Sample <a target='_blank' href='/static/sampleData/mess.csv'>Mess details file</a></small><br>"),
            "staff_csv": mark_safe("This contains Staff index and the department they are associated with, along with their interaction space.<br> <small>View Sample <a target='_blank' href='/static/sampleData/staff.csv'>Staff detail file</a></small><br>"),
            "students_csv": mark_safe("This contains Student index, Hostel index, Mess index, Department index.<br> <small>View Sample <a target='_blank' href='/static/sampleData/student.csv'>Student Detail file</a></small><br>"),
            "timetable_csv": mark_safe("This contains Student index, and the subsequent columns will have the list of classes they take.<br> <small>View Sample <a target='_blank' href='/static/sampleData/timetable.csv'>Timetable detail file</a></small><br>")
        }

    def clean(self):
        cleaned_data = super(addCampusDataForm, self).clean()
        ## TODO: Validate the Timtetable.csv with proper validation rules
        if self.cleaned_data.get('campus_name') is None:
            raise ValidationError({"campus_name": "The name of the instantiation should not be empty"})

        try:
            classes_csv = pd.read_csv(self.cleaned_data.get('classes_csv'))
            common_areas_csv = pd.read_csv(self.cleaned_data.get('common_areas_csv'))
            mess_csv = pd.read_csv(self.cleaned_data.get('mess_csv'))
            staff_csv = pd.read_csv(self.cleaned_data.get('staff_csv'))
            students_csv = pd.read_csv(self.cleaned_data.get('students_csv'))

            expected_classes_cols = ['class_id', 'dept', 'faculty_id', 'active_duration', 'days']
            expected_common_areas_cols = ['type', 'number', 'average_time_spent', 'starting_id','active_duration']
            expected_mess_cols = ['mess_id', 'active_duration', 'average_time_spent']
            expected_staff_cols = ['staff_id', 'dept_associated', 'interaction_space', 'residence_block', 'adult_family_members', 'num_children']
            expected_students_cols = ['id', 'age', 'hostel', 'mess', 'dept_id']


            if not set(expected_classes_cols).issubset(classes_csv.columns.tolist()):
                raise ValidationError({"classes.csv": "One or more required columns names are missing in classes.csv. Please refer the sample file and re-upload"})
            if not set(expected_common_areas_cols).issubset(common_areas_csv.columns.tolist()):
                raise ValidationError({"common_areas_csv": "One or more required columns names are missing in common_areas.csv. Please refer the sample file and re-upload"})
            if not set(expected_mess_cols).issubset(mess_csv.columns.tolist()):
                raise ValidationError({"mess_csv": "One or more required columns names are missing in mess.csv. Please refer the sample file and re-upload"})
            if not set(expected_staff_cols).issubset(staff_csv.columns.tolist()):
                raise ValidationError({"staff_csv": "One or more required columns names are missing in staff.csv. Please refer the sample file and re-upload"})
            if not set(expected_students_cols).issubset(students_csv.columns.tolist()):
                raise ValidationError({"students_csv": "One or more required columns names are missing in students.csv. Please refer the sample file and re-upload"})
        except:
            raise ValidationError(_("Ensure files uploaded are only in .csv format"))
        return cleaned_data


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
        initial="12",
        required=True,
    )
    minimum_hostel_time = forms.FloatField(
        label="Minimum amount of time a student could spend in the hostel",
        initial="1",
        required=True,
    )


    def __init__(self, campus_queryset, intv_queryset, *args, **kwargs):
        super(createSimulationForm, self).__init__(*args, **kwargs)
        campusChoices = [(campus.id, campus.inst_name) for campus in campus_queryset]
        interventionChoices = [(intv.id, intv.intv_name) for intv in intv_queryset]

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
