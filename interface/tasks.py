from __future__ import absolute_import
from .helper import  convert, run_aggregate_sims
from django.core.files import File
from celery import shared_task
from django.core.mail import EmailMultiAlternatives
from django.conf import settings
from anymail.exceptions import AnymailError
from config.celery import app
from .models import simulationParams, campusInstantiation
from io import StringIO
import json
import pandas as pd
from django.utils import timezone
import sys
import os
import billiard as multiprocessing

## logging
import logging
log = logging.getLogger('celery_log')

## Custom modules taken from submodule
from simulator.staticInst.campus_parse_and_instantiate import campus_parse


@app.task()
def run_instantiate(inputFiles):
    inputFiles = json.loads(inputFiles)
    inputFiles['students'] = pd.DataFrame.from_dict(inputFiles['students'])
    df = pd.DataFrame.from_dict(inputFiles['class'])
    df = df.astype({'faculty_id': int})
    inputFiles['class'] = df
    del df
    inputFiles['timetable'] = pd.DataFrame.from_dict(inputFiles['timetable'])
    inputFiles['staff'] = pd.DataFrame.from_dict(inputFiles['staff'])
    inputFiles['mess'] = pd.DataFrame.from_dict(inputFiles['mess'])
    inputFiles['common_areas'] = pd.DataFrame.from_dict(inputFiles['common_areas'])
    try:
        individuals, interactionSpace, transCoeff =  campus_parse(inputFiles)

        indF = StringIO(json.dumps(individuals, default=convert))
        intF = StringIO(json.dumps(interactionSpace, default=convert))
        campusInstantiation.objects.filter(id=inputFiles['objid'])[0].agent_json.save('individuals.json', File(indF))
        campusInstantiation.objects.filter(id=inputFiles['objid'])[0].interaction_spaces_json.save('interaction_spaces.json', File(intF))

        campusInstantiation.objects.filter(id=inputFiles['objid']).update(
            trans_coeff_file = json.dumps(transCoeff, default=convert),
            status = 'Complete',
            created_on = timezone.now()
        )
        log.info(f"Instantiaion job {campusInstantiation.objects.filter(id=inputFiles['objid'])[0].inst_name.campus_name} was completed successfully.")
        del individuals, interactionSpace, transCoeff
        return True
    except Exception as e:
        campusInstantiation.objects.filter(id=inputFiles['objid']).update(
            status = 'Error',
            created_on = timezone.now()
        )
        log.error(f"Instantiaion job {campusInstantiation.objects.filter(id=inputFiles['objid'])[0].inst_name.campus_name} terminated abruptly with error {e} at {sys.exc_info()}.")
        return False


def run_cmd(prgCall):
    print(prgCall)
    outName = prgCall[1]
    if not os.path.exists(outName):
        os.mkdir(outName)
    os.system(prgCall[0] + outName)

@app.task()
def run_simulation(id, dirName, enable_testing, intv_name):
    obj = simulationParams.objects.filter(id=id)
    obj.update(status='Running')
    obj = obj[0]
    log.info(f"Simulation job { obj.simulation_name } is now running.")
    cmd = f"./simulator/cpp-simulator/drive_simulator --SEED_FIXED_NUMBER --INIT_FIXED_NUMBER_INFECTED { obj.init_infected_seed } --intervention_filename ./{intv_name}.json --NUM_DAYS { obj.days_to_simulate }"

    if(enable_testing):
        cmd += f" --ENABLE_TESTING  --testing_protocol_filename ./testing_protocol.json"

    cmd += f" --input_directory { dirName } --output_directory "

    list_of_sims = [(cmd , f"{ dirName }/{obj.simulation_name.replace(' ', '_')}_{ intv_name }_id_{ i }") for i in range(obj.simulation_iterations)]

    pool = multiprocessing.Pool(multiprocessing.cpu_count() - 1)
    r = pool.map_async(run_cmd, list_of_sims)

    r.wait()
    try:
        log.info(f" Running sims for {obj.simulation_name } are complete")
        simulationParams.objects.filter(id=id).update(
        output_directory=f"{ dirName }/{obj.simulation_name.replace(' ', '_')}_{ intv_name }",
        status='Complete',
        completed_at=timezone.now()
        )
        run_aggregate_sims(id)
        log.info(f"Simulation job { obj.simulation_name } is complete and the results are aggregated.")
        return True
    except Exception as e:
        simulationParams.objects.filter(id=id).update(
            status = 'Error',
            created_on = timezone.now()
        )
        log.error(f"Simulation job { obj.simulation_name } terminated abruptly with error {e} at {sys.exc_info()}.")
        return False

@shared_task(bind=True, max_retries=settings.CELERY_TASK_MAX_RETRIES)
def send_mail(self, recipient, subject, html_message, context, **kwargs):
    # Subject and body can't be empty. Empty string or space return index out of range error
    message = EmailMultiAlternatives(
        subject=subject,
        body=html_message,
        from_email=settings.DJANGO_DEFAULT_FROM_EMAIL,
        to=[recipient]
    )
    message.attach_alternative(" ", "text/html")
    message.merge_data = {
        recipient: context,
    }
    try:
        message.send()
    except AnymailError as e:
        self.retry(e)
