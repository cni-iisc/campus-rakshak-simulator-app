"""
views.py defines the application logic and controls what webpage is rendered on each specific url
"""
import json
from django.utils import timezone
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import ValidationError
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse, reverse_lazy
from django.views.generic import FormView, TemplateView
from django.views.generic.base import View
from django.views.generic.detail import DetailView
from django.views.generic.edit import DeleteView
from rest_framework import viewsets
from django.utils.safestring import mark_safe

#setting up logs
import logging
log = logging.getLogger('interface_log')
log.info("starting the campussim interface")


# custom imports
from .forms import *
from .helper import get_or_none, validate_password
from .mixins import *
from .models import *
from .serializers import *
from .services import (instantiateTask, launchSimulationTask,
                       send_activation_mail, send_forgotten_password_email)

## Rest API Endpoints
class campusTransCoeffViewSet(viewsets.ModelViewSet):
    queryset = campusInstantiation.objects.filter(status='Complete')
    serializer_class = campusTransCoeffSerializer

class simResultsViewSet(viewsets.ModelViewSet):
    queryset = simulationResults.objects.filter(status='A')
    serializer_class = simResultsSerializer

log.info("API end-points are enabled")

def user_activation(request, token):
    token = get_object_or_404(UserRegisterToken, token=token)
    user = token.user
    user.is_active = True
    user.save()
    token.delete()
    messages.success(request, 'Your account was successfully activated !')
    log.info(f"User account for {user} was activated successfully!")
    origin_name = request.GET.get('origin', None)
    origin = RegisterOrigin.objects.filter(name=origin_name).first()
    redirect_url = origin.redirect_url if origin else reverse('login')
    return redirect(redirect_url)


def user_password_reset(request, token):
    token = get_object_or_404(UserPasswordResetToken, token=token)
    errors = []
    if request.POST and request.POST.get("password", False):
        user = token.user
        password = request.POST.get("password")
        try:
            validate_password(password)
        except ValidationError as e:
            errors = e
        else:
            user.set_password(password)
            user.save()
            token.delete()
            message = "Your password has been successfully changed!"
    return render(request, 'interface/auth/password_reset.html', locals())




class RegisterView(AnonymousRequired, FormView):
    template_name = 'interface/auth/register.html'
    form_class = RegisterForm

    def dispatch(self, *args, **kwargs):
        self.origin = self.request.GET.get('origin', None)
        return super().dispatch(*args, **kwargs)

    def get_initial(self):
        return {'origin': self.origin}

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['origin'] = self.origin
        return context

    def form_valid(self, form):
        user = form.save(commit=False)
        user.is_active =True
        print(user)
        user.save()
        # send_activation_mail(self.request, user)
        messages.success(self.request, f"Account created successfully for { user.email }")
        log.info(f"Account created successfully for { user.email }")
        # return render(self.request, 'interface/auth/thanks.html')
        return redirect('login')


class LogInView(AnonymousRequired, FormView):
    template_name = 'interface/auth/login.html'
    form_class = LoginForm

    def dispatch(self, *args, **kwargs):
        self.error = None
        return super().dispatch(*args, **kwargs)

    def get_success_url(self):
        url = self.request.GET.get('next', reverse('profile'))
        return url

    def form_valid(self, form):
        email = form.cleaned_data['email']
        password = form.cleaned_data['password']
        user = authenticate(email=email, password=password)
        if user is None:
            self.error = "Invalid email and / or password"
            return self.form_invalid(form)

        if not user.is_active:
            self.error = "Please activate your account "
            return self.form_invalid(form)
        login(self.request, user)
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['error'] = self.error
        return context


@login_required
def logout_view(request):
    logout(request)
    return redirect(reverse('index'))

class IndexView(AnonymousRequired, AddSnippetsToContext, TemplateView):
    template_name = 'interface/index.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        return context

class AboutView(AddSnippetsToContext, TemplateView):
    template_name = 'interface/about.html'


class ProfileView(LoginRequiredMixin, AddUserToContext, TemplateView):
    template_name = 'interface/profile.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = userModel.objects.filter(email=self.request.user)[0]
        context['user'] = {
            "first_name": user.first_name,
            "last_name": user.last_name,
            "works_at": user.works_at
        }
        context['totCampus'] = campusInstantiation.get_count_by_status(user=self.request.user, status='Complete')
        context['totIntv'] = interventions.get_count_by(user=self.request.user)
        context['totJobs'] = simulationParams.get_count_by(user=self.request.user)
        context['running'] = simulationParams.get_count_by_status(user=self.request.user, status='Running')
        context['complete'] = simulationParams.get_count_by_status(user=self.request.user, status='Complete')
        context['interventions'] = interventions.get_topk_latest(self.request.user, k=3)
        context['simulations'] = simulationParams.get_topk_latest(self.request.user, k=3)
        context['instantiations'] = campusInstantiation.get_topk_latest(self.request.user, k=3)
        return context



class ProfileEditView(LoginRequiredMixin, AddUserToContext, FormView):
    template_name = 'interface/profile_edit.html'
    form_class = EditUserForm
    success_url = reverse_lazy('profile')

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['instance'] = self.request.user
        return kwargs

    def form_valid(self, form):
        form.save()
        return super().form_valid(form)

class ForgottenPasswordView(TemplateView):
    """
    REFACTOR: Make this a FormView
    We are using a plain html form in the template. Can be done better.
    """
    template_name = 'interface/auth/forgotten_password.html'

    def dispatch(self, *args, **kwargs):
        self.message = None
        return super().dispatch(*args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['message'] = self.message
        return context

    def post(self, *args, **kwargs):
        email = self.request.POST.get('email', '').strip()
        baseuser = get_or_none(userModel, email=email)
        if baseuser is None:
            self.message = "User with the specified email address is found!"
        else:
            self.message = "An email to change the password was sent to the specified address"
            send_forgotten_password_email(self.request, baseuser)
        return self.get(*args, **kwargs)


class addDataView(LoginRequiredMixin, AddUserToContext, View):
    template_name = 'interface/create.html'
    model = campusData
    form_class = addCampusDataForm

    campus_name = ''

    def instantiate(self):
        q = campusInstantiation(
            inst_name = campusData.objects.filter(campus_name=self.campus_name)[0],
            created_by = self.request.user,
            created_on = timezone.now()
        )
        q.save()
        log.info(f'Instantiating campus: { self.campus_name } is saved for user {self.request.user}. ')
        return instantiateTask(self.request)


    def render(self, request):
        context = {
            'form': self.form,
            'title': 'Create a new instatiation of a synthetic campus',
            'instruction': mark_safe('Upload the required files in .csv format to instantiate a synthetic campus for running simulations.<br> For assistance with the expected files, please check the sample files linked with each file upload field.'),
            'instance': self.request.user
        }
        return render(request, self.template_name, context)

    def post(self, request):
        self.form = addCampusDataForm(request.POST, request.FILES)
        self.campus_name = ''
        if self.form.is_valid():
            obj = self.form.save()
            obj.created_by = self.request.user
            self.campus_name = obj.campus_name
            obj.created_on = timezone.now()
            obj.save()
            messages.success(request, f'Data for campus: { self.campus_name } is saved. Please wait while we run this job in the background, on an average you will hear from you us in 2 minutes if the servers are free.')
            log.info(f'Data for campus: { self.campus_name } is saved for user {self.request.user}. ')
            if self.instantiate():
                return redirect('profile')
        else:
            error_string = ' '.join([' '.join(x for x in l) for l in list(self.form.errors.values())])
            messages.error(request, f'While saving the data to the database the following errors were found: { error_string}')
            log.error(f'Errors were encountered while saving data for campus: { self.campus_name } on the database')
        return self.render(request)

    def get(self, request):
        self.form = addCampusDataForm()
        return self.render(request)



class userActivityView(LoginRequiredMixin, AddUserToContext, TemplateView):
    template_name = "interface/user_activity.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['interventions'] = interventions.get_all(self.request.user)
        context['simulations'] = simulationParams.get_all(self.request.user)
        context['campuses'] = campusData.get_all(self.request.user)
        return context

class deleteDataView(LoginRequiredMixin, AddUserToContext, DeleteView):
    template_name = "interface/delete.html"
    model = campusData
    success_url = reverse_lazy('profile')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['type'] = 'campus data'
        return context


class deleteInstantiationView(LoginRequiredMixin, AddUserToContext, DeleteView):
    template_name = "interface/delete.html"
    model = campusInstantiation
    success_url = reverse_lazy('profile')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['type'] = 'campus instantiation'
        return context

class deleteInterventionView(LoginRequiredMixin, AddUserToContext, DeleteView):
    template_name = "interface/delete.html"
    model = interventions
    success_url = reverse_lazy('profile')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['type'] = 'intervention'
        return context

class deleteSimulationView(LoginRequiredMixin, AddUserToContext, DeleteView):
    template_name = "interface/delete.html"
    model = simulationParams
    success_url = reverse_lazy('profile')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['type'] = 'simulation job'
        return context


class createIntervention(LoginRequiredMixin, AddUserToContext, TemplateView):
    template_name = 'interface/create_intervention.html'
    model = interventions

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        return context

    def post(self, request):
        body_unicode = request.body.decode('utf-8')
        received_json = json.loads(body_unicode)
        q = interventions(
            intv_name = received_json['intvName'],
            intv_json = json.dumps(received_json['intvDict']),
            created_by = self.request.user,
            created_on = timezone.now()
        )
        q.save()
        log.info(f"Intervention { received_json['intvName'] } added to the database on { datetime.dateime.now() }")
        return render(request, self.template_name, self.get_context_data())


class updateIntervention(LoginRequiredMixin, AddUserToContext, TemplateView):
    template_name = 'interface/update_intervention.html'
    model = interventions

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['pk'] = self.kwargs.get('pk')
        self.obj = interventions.objects.filter(pk=self.kwargs.get('pk')).first()
        context['intvJSON'] = self.obj.intv_json
        context['intvName'] = str(self.obj.intv_name)
        return context


    def post(self, request, pk):
        body_unicode = request.body.decode('utf-8')
        received_json = json.loads(body_unicode)
        interventions.objects.filter(pk=pk).update(
            intv_name = received_json['intvName'],
            intv_json = json.dumps(received_json['intvDict']),
            created_by = self.request.user,
            updated_at = timezone.now()
        )
        log.info(f"Intervention id { pk } was updated to { received_json['intvName'] } at  { datetime.datetime.now() }")
        return render(request, self.template_name, self.get_context_data())


class createSimulationView(LoginRequiredMixin, AddUserToContext, TemplateView):
    template_name = 'interface/create_simulation.html'
    simName = ''
    def render(self, request):
        context = {
            'form': self.form,
            'instance': self.request.user
        }
        return render(request, self.template_name, context)

    def get_form_kwargs(self):
        kwargs = super(createSimulationView, self).get_form_kwargs()
        kwargs['instance'] = self.request.user
        return kwargs

    def get(self, request):
        self.form = createSimulationForm(instance=self.request.user)
        return self.render(request)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        return context

    def post(self, request):
        if request.method == 'POST':
            formData = dict(request.POST)

            BETA = []
            for key in formData.keys():
                if 'beta_' in key and key != 'beta_scale':
                    _, betaType = key.split('_')
                    BETA.append({
                            'type': int(betaType),
                            'beta': float(formData[key][0]),
                            'alpha': 1 #TODO: get it from the ajax form
                        })

            testing = False
            if formData['enable_testing'][0] == 'on':
                testing = True

            self.simName = formData['simulation_name'][0]

            try:
                obj = testingParams.objects.get(testing_protocol_name='default')
            except testingParams.DoesNotExist:
                obj = testingParams(
                    testing_protocol_name='default',
                    testing_protocol_file=json.load(open('./media/testing_protocol_001.json', 'r')),
                    created_on=timezone.now()
                )
                obj.save()

            q = simulationParams(
                simulation_name=self.simName,
                days_to_simulate=int(formData['num_days'][0]),
                init_infected_seed=int(formData['num_init_infected'][0]),
                simulation_iterations=int(formData['num_iterations'][0]),
                campus_instantiation=campusInstantiation.objects.get(id=int(formData['instantiatedCampus'][0])),
                intervention=interventions.objects.get(id=int(formData['intvName'][0])),
                enable_testing=testing, #eval ensures the form data is a boolean and not a string
                testing_capacity=int(formData['testing_capacity'][0]),
                testing_protocol=testingParams.objects.get(testing_protocol_name='default'), #By default: the default testing protocol will be aded.
                periodicity=int(formData['periodicity'][0]),
                betaScale=int(formData['betaScale'][0]),
                min_grp_size=int(formData['min_grp_size'][0]),
                max_grp_size=int(formData['max_grp_size'][0]),
                avg_associations=int(formData['avg_associations'][0]),
                minimum_hostel_time=float(formData['minimum_hostel_time'][0]),
                created_by=self.request.user,
                created_on=timezone.now(),
                status='Created'
            )
            q.save()
            launchSimulationTask(self.request, int(formData['instantiatedCampus'][0]), BETA)
            messages.info(request, f'Simulation: { self.simName } is created. Please wait while we run the simulation on our servers, typical campus instantiations upto 10,000 agents takes about 2 minutes/ iteration.')
            log.info(f'Simulation: { self.simName } is created')
            return redirect('profile')
        else:
            messages.error(request, f'Errors were encountered while creating simulation { self.simName } job. Please check the inputs and try again')
            log.error(f'Errors were encountered while creating simulation { self.simName } job.')
        return render(request, self.template_name, self.get_context_data())

class viewSimulationView(LoginRequiredMixin, AddUserToContext, DetailView):
    template_name = "interface/view_simulation.html"
    model = simulationParams

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['betas'] = json.loads(simulationParams.objects.filter(pk=self.kwargs.get('pk'))[0].campus_instantiation.trans_coeff_file)
        return context

class visualizeSingleSimulation(LoginRequiredMixin, AddUserToContext, TemplateView):
    template_name = 'interface/visualizeSimulation.html'
    model = simulationResults

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['pk'] = self.kwargs.get('pk')
        self.obj = simulationResults.objects.filter(pk=self.kwargs.get('pk')).first()
        context['results'] = json.dumps(self.obj.agg_results)
        context['status'] = json.dumps(self.obj.status)
        return context

## TODO: Make this a REST service
class visualizeMultiSimulation(LoginRequiredMixin, AddUserToContext, TemplateView):
    template_name = 'interface/visualizeMultiSimulation.html'
    model = simulationResults

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user_sims = simulationResults.objects.filter(created_by=self.request.user, status='A').all()
        data = []
        for sim in user_sims:
            data.append({
                "id": sim.simulation_id.id,
                "name": sim.simulation_id.simulation_name,
                "campus": sim.simulation_id.campus_instantiation.inst_name.campus_name,
                "intv": sim.simulation_id.intervention.intv_name,
                "enable_testing": 1 if sim.simulation_id.enable_testing else 0
            })
        context['results'] = data
        return context
