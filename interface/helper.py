"""
helper.py: contains utility functions used in the application
"""
import os
import datetime
import numpy as np
import pandas as pd

from django.urls import reverse
from django.core.exceptions import ValidationError
from django.utils.translation import ugettext_lazy as _

from .models import RegisterOrigin, simulationParams, simulationResults

## Function to check if an object is present in a model or not?
def get_or_none(model, *args, **kwargs):
    try:
        return model.objects.get(*args, **kwargs)
    except model.DoesNotExist:
        return None

### Function to validate password
def validate_password(value):
    """Validates that a password is as least 6 characters long and has at least
    1 digit and 1 letter.
    """

    min_length = 6

    if len(value) <= min_length:
        raise ValidationError(_('Password must be at least {0} characters '
                                'long.').format(min_length))

    # check for digit
    if not any(char.isdigit() for char in value):
        raise ValidationError(_('Password must contain at least 1 digit.'))

    # check for letter
    if not any(char.isalpha() for char in value):
        raise ValidationError(_('Password must contain at least 1 letter.'))

### Function to generate activation URL for new users (currently disabled)
def get_activation_url(token, origin_name=None):
    activation_url = reverse("user_activation", kwargs={'token': token})
    origin = RegisterOrigin.objects.filter(name=origin_name).first()

    if origin:
        return '{}?origin={}'.format(activation_url, origin.name)
    else:
        return activation_url

### Function to ensure numpy.dtypes are converted to scalars
def convert(o):
    if isinstance(o, np.generic): return o.item()
    raise TypeError

## Function to validate inputs to create simulation
def validateFormResponse(formData):
    for key in formData.keys():
        ## Transmission coefficients should always be between 0 -- 1
        if 'beta_' in key and key != 'beta_scale':
            if not((float(formData[key][0]) >= 0) or (float(formData[key][0]) <=1)):
                return False

    ## Simulation name should be atleast 2 characters long
    if len(formData['simulation_name'][0]) < 2:
        return False

    ## Num-days to be atleast 1
    if int(formData['num_days'][0]) < 1:
        return False

    min_grp_size = int(formData['min_grp_size'][0])
    max_grp_size = int(formData['max_grp_size'][0])
    avg_associations =int(formData['avg_associations'][0])

    if (min_grp_size <= 0) or (min_grp_size >= max_grp_size):
        return False
    if (max_grp_size <= 0) or (min_grp_size >= max_grp_size):
        return False
    # ## Average number of associates should be atleast 1 and less than 20
    if (avg_associations <= 0) or (avg_associations >= 20):
        return False
    if not((avg_associations > min_grp_size) or (avg_associations < max_grp_size)):
        return False

    ## periodicity == 7
    if int(formData['periodicity'][0]) != 7:
        return False
    return True


### Function to aggregate resutls from specified number of simulatoin iterations and serialize
def run_aggregate_sims(simPK):
    num_iterations = simulationParams.objects.get(id=simPK).simulation_iterations
    dirName = simulationParams.objects.get(id=simPK).output_directory

    affected = pd.DataFrame()
    cases = pd.DataFrame()
    fatalities = pd.DataFrame()
    recovered = pd.DataFrame()
    disease_label_stats = pd.DataFrame()

    #aggregate across runs
    for i in range(num_iterations):
        affected = pd.concat([affected, pd.read_csv(f"{ dirName }_id_{ i }/num_affected.csv")], ignore_index=True)
        cases = pd.concat([cases, pd.read_csv(f"{ dirName }_id_{ i }/num_cases.csv")], ignore_index=True)
        fatalities = pd.concat([fatalities, pd.read_csv(f"{ dirName }_id_{ i }/num_fatalities.csv")], ignore_index=True)
        recovered = pd.concat([recovered, pd.read_csv(f"{ dirName }_id_{ i }/num_recovered.csv")], ignore_index=True)
        disease_label_stats = pd.concat([disease_label_stats, pd.read_csv(f"{ dirName }_id_{ i }/disease_label_stats.csv")], ignore_index=True)

    #remove simulation result
    os.system(f"rm -rf { dirName }*")

    fatalities["daily_fatalities"] = fatalities["num_fatalities"].diff().fillna(0)
    recovered["daily_recovered"] = recovered["num_recovered"].diff().fillna(0)
    disease_label_stats['cumulative_tests'] = disease_label_stats['people_tested']
    disease_label_stats['daily_positive_cases'] = disease_label_stats['cumulative_positive_cases'].diff().fillna(0)
    #forcing initial negative values to zero
    fatalities["daily_fatalities"][fatalities["daily_fatalities"]<0]=0
    recovered["daily_recovered"][recovered["daily_recovered"]<0]=0
    disease_label_stats['daily_positive_cases'][disease_label_stats['daily_positive_cases']<0]=0

    #aggregate the data
    affected = affected.groupby(by=['Time']).agg(['std', 'mean']).reset_index()
    affected.columns = ['_'.join(filter(None, col)).strip() for col in affected.columns.values]
    cases = cases.cumsum().diff(periods=4)
    cases = cases.groupby(by=['Time']).agg(['std', 'mean']).reset_index()
    cases.columns = ['_'.join(filter(None, col)).strip() for col in cases.columns.values]
    fatalities = fatalities.groupby(by=['Time']).agg(['std', 'mean']).reset_index()
    fatalities.columns = ['_'.join(filter(None, col)).strip() for col in fatalities.columns.values]
    recovered = recovered.groupby(by=['Time']).agg(['std', 'mean']).reset_index()
    recovered.columns = ['_'.join(filter(None, col)).strip() for col in recovered.columns.values]
    disease_label_stats = disease_label_stats.groupby(by=['Time']).agg(['std', 'mean']).reset_index()
    disease_label_stats.columns = ['_'.join(filter(None, col)).strip() for col in disease_label_stats.columns.values]

    data = {
        "intervention": simulationParams.objects.get(id=simPK).intervention.intv_name,
        "time": affected['Time'].values.tolist(),
        "daily": {
                "infected":{
                    "mean": cases['num_cases_mean'].values.tolist(),
                    "std": cases['num_cases_std'].values.tolist()
                },
                "recovered":{
                    "mean": recovered['daily_recovered_mean'].values.tolist(),
                    "std": recovered['daily_recovered_std'].values.tolist()  
                },
                "fatalities":{
                    "mean": fatalities['daily_fatalities_mean'].values.tolist(),
                    "std": fatalities['daily_fatalities_std'].values.tolist()
                    
                },
                "positive_cases":{
                    "mean": disease_label_stats['daily_positive_cases_mean'].values.tolist(),
                    "std": disease_label_stats['daily_positive_cases_std'].values.tolist()
                },
                "people_tested":{
                    "mean": disease_label_stats['requested_tests_mean'].values.tolist(),
                    "std": disease_label_stats['requested_tests_std'].values.tolist()
                },
        },
        "cumulative": {

                    "infected":{
                        "mean":affected['num_affected_mean'].values.tolist(),
                        "std":affected['num_affected_std'].values.tolist()
                    },
                    "recovered":{
                        "mean": recovered['num_recovered_mean'].values.tolist(),
                        "std": recovered['num_recovered_std'].values.tolist()
                    },
                    "fatalities":{
                        "mean": fatalities['num_fatalities_mean'].values.tolist(),
                        "std": fatalities['num_fatalities_std'].values.tolist()
                    },
                    "positive_cases":{
                        "mean": disease_label_stats['cumulative_positive_cases_mean'].values.tolist(),
                        "std": disease_label_stats['cumulative_positive_cases_std'].values.tolist()
                    },
                    "people_tested":{
                        "mean": disease_label_stats['cumulative_tests_mean'].values.tolist(),
                        "std": disease_label_stats['cumulative_tests_std'].values.tolist()
                    },
        },
    }

    sim = simulationResults(
        simulation_id=simulationParams.objects.get(id=simPK),
        agg_results=data,
        status='A',
        completed_at=datetime.datetime.now(),
        created_by = simulationParams.objects.get(id=simPK).created_by
    )
    sim.save()
    return True
