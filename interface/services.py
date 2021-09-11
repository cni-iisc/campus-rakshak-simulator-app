"""
services.py: queries models to get required inputs to launch a task in the background.
- this scripts abstracts the functions specified in tasks.py
"""
import uuid
from io import StringIO

import os
import pandas as pd
from django.urls import reverse
from django.contrib.sites.shortcuts import get_current_site
from .tasks import run_simulation, send_mail, run_instantiate
from .helper import get_activation_url, convert
from .models import (UserRegisterToken, UserPasswordResetToken, campusInstantiation, simulationParams)
import json
from simulator.staticInst.config import configCreate
from django.contrib import messages
import logging
log = logging.getLogger('interface_log')

def send_template_email(recipient, subject, html_message, context):
    # TODO: Enable this when the mail configurations are in place
    # return send_mail.delay(recipient, subject, html_message, context)
    return True

def send_activation_mail(request, user):
    to_email = user.email
    UserRegisterToken.objects.filter(user=user).delete()

    # TODO: check if it exsists
    user_token = UserRegisterToken.objects.create(
        user=user,
        token=uuid.uuid4())

    subject = f"Campussim: New Account Activation for {user}"
    html_message = f"""
    Dear  {user},

    To activate your campussim user account, click on the following link:
    """

    context = {
        'protocol': request.is_secure() and 'https' or 'http',
        'domain': get_current_site(request).domain,
        'url': get_activation_url(user_token.token, request.GET.get('origin', None)),
        'full_name': user.get_full_name(),
    }
    log.info(f'Account activation email was sent to {to_email}')
    send_template_email(to_email, subject, html_message, context)


def send_forgotten_password_email(request, user):
    to_email = user.email
    UserPasswordResetToken.objects.filter(user=user).delete()

    # TODO: check if it exsists
    user_token = UserPasswordResetToken.objects.create(
        user=user,
        token=uuid.uuid4())

    subject = f"Campussim: New Account Activation for {user}"
    html_message = f"""
    Dear  {user},

    To reset the password for your campussim user account, click on the following link:
    """
    context = {
        'protocol': request.is_secure() and 'https' or 'http',
        'domain': get_current_site(request).domain,
        'url': reverse("user_password_reset", kwargs={"token": user_token.token}),
        'full_name': user.get_full_name()
    }

    log.info(f'Forgot password link email was sent to {to_email}')
    send_template_email(to_email, subject, html_message, context)


def updateTransCoeff(campusId, BETA):
    transmission_coefficients_json = json.loads(campusInstantiation.objects.get(id=campusId).trans_coeff_file)
    for i in range(len(BETA)):
        for e in transmission_coefficients_json:
           if (e['type'] == BETA[i]['type']):
               if e['beta'] != int(BETA[i]['beta']):
                    e['beta'] = int(BETA[i]['beta']) #TODO: Add ALPHA parameter when it is available

    campusInstantiation.objects.filter(id=campusId).update(
        trans_coeff_file=json.dumps(
            transmission_coefficients_json,
            default=convert
        )
    )
    return True

def addConfigJSON(obj, outPath):
    min_group_size =  int(obj.min_grp_size)
    max_group_size = int(obj.max_grp_size)
    beta_scaling_factor = int(obj.betaScale)
    avg_num_assns =  int(obj.avg_associations)
    periodicity = int(obj.periodicity)
    minimum_hostel_time = float(obj.minimum_hostel_time)
    testing_capacity = int(obj.testing_capacity)

    configJSON = configCreate(min_group_size, max_group_size, beta_scaling_factor, avg_num_assns, periodicity, minimum_hostel_time, testing_capacity)
    f = open(f"{ outPath }/config.json", "w")
    f.write(json.dumps(configJSON))
    f.close()
    return True

def instantiateTask(request):
    user = request.user
    obj = campusInstantiation.get_latest(user=user) #gives id of the object
    obj = campusInstantiation.objects.filter(created_by=user, id=obj.id)[0]

    inputFiles = {
        'students': pd.read_csv(StringIO(obj.inst_name.students_csv.read().decode('utf-8')), delimiter=',').to_dict(),
        'class': pd.read_csv(StringIO(obj.inst_name.classes_csv.read().decode('utf-8')), delimiter=',').to_dict(),
        'timetable': pd.read_csv(StringIO(obj.inst_name.timetable_csv.read().decode('utf-8')), delimiter=',', header=None, names=[i for i in range(24)]).to_dict(),
        'staff': pd.read_csv(StringIO(obj.inst_name.staff_csv.read().decode('utf-8')), delimiter=',').to_dict(),
        'mess': pd.read_csv(StringIO(obj.inst_name.mess_csv.read().decode('utf-8')), delimiter=',').to_dict(),
        'common_areas': pd.read_csv(StringIO(obj.inst_name.common_areas_csv.read().decode('utf-8')), delimiter=',').to_dict(),
        'campus_setup' : pd.read_csv(StringIO(obj.inst_name.campus_setup_csv.read().decode('utf-8')), delimiter=',').to_dict(),
        'objid': obj.id
    }
    campusInstantiation.objects.filter(created_by=user, id=obj.id).update(status='Running')
    run_instantiate.apply_async(queue='instQueue', kwargs={'inputFiles': json.dumps(inputFiles)})
    return True
    # if res.get():
    #     messages.success(request, f"instantiation job name: { obj.inst_name } is complete")
    #     log.info(f"instantiation job name: { obj.inst_name } is complete")
    # else:
    #     messages.error(request, f"instantiation job name: { obj.inst_name } has failed. Please check the input files used.")
    #     log.error(f"instantiation job name: { obj.inst_name } has failed.")



def launchSimulationTask(request, campusId, BETA):
    user = request.user
    obj = simulationParams.get_latest(user=user) #gives id of the object
    obj = simulationParams.objects.filter(created_by=user, id=obj.id)[0]

    dirName = os.path.splitext(obj.campus_instantiation.agent_json.path)[0]
    dirName = dirName.rsplit('/', 1)[0]

    if not os.path.exists(dirName):
        os.mkdir(dirName)

    updateTransCoeff(campusId, BETA)

    f = open(f"{ dirName }/{ obj.intervention.intv_name }.json", "w")
    f.write(json.dumps(json.loads(obj.intervention.intv_json)))
    f.close()


    json.dump(json.loads(obj.campus_instantiation.trans_coeff_file), open(f"{ dirName }/transmission_coefficients.json", 'w'), default=convert)
    json.dump(obj.testing_protocol.testing_protocol_file, open(f"{ dirName }/testing_protocol.json", 'w'), default=convert)
    addConfigJSON(obj, dirName)

    simulationParams.objects.filter(created_by=user, id=obj.id).update(status='Queued')
    res = run_simulation.apply_async(queue='simQueue', kwargs={'id': obj.id, 'dirName': dirName, 'enable_testing': obj.enable_testing, 'intv_name': obj.intervention.intv_name})
    # if res.get():
    #     messages.success(request, f"Simulation job name: { obj.simulation_name } is complete")
    #     log.info(f"Simulation job name: { obj.simulation_name } is complete")
    # else:
    #     messages.error(request, f"Simulation job name: { obj.simulation_name } has failed. Please check the inputs used.")
    #     log.error(f"Simulation job name: { obj.simulation_name } has failed.")




def send_result_available_email(request, user):
    to_email = user.email
    simulationResults.objects.filter(user=user, completed_at=datetime.datetime.now())
    subject = ""
    html_message = """
    <html>
        <h4>Simulation Result update from campussim</h4>
    </html>
    """
    context = {
        'protocol': request.is_secure() and 'https' or 'http',
        'domain': get_current_site(request).domain,
        'full_name': user.full_name
    }
    log.info(f'Account activation email was sent to {to_email}')
    send_template_email(to_email, subject, html_message, context)


def send_instantion_complete_mail(request, user):
    to_email = user.email
    campusInstantiation.objects.filter(user=user, completed_at=datetime.datetime.now())
    subject = "Campussim"
    html_message = """
    <html>
        <h4>Simulation Result update from campussim</h4>
    </html>
    """
    context = {
        'protocol': request.is_secure() and 'https' or 'http',
        'domain': get_current_site(request).domain,
        'full_name': user.full_name
    }
    send_template_email(to_email, subject, html_message, context)
