"""
serializers.py: defines the serializers for the API services written on-top of models
The serializers query the objects stored in a model using their `id` field
"""
from rest_framework import serializers
from .models import campusInstantiation, simulationParams, simulationResults

## API for transmission coefficient JSONs for all campus instantiations, search by 'object id'
class campusTransCoeffSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = campusInstantiation
        fields = ['id', 'trans_coeff_file']

## API for aggregated simulation results for all simulations done, search by 'object id'
class simResultsSerializer(serializers.HyperlinkedModelSerializer):
    simulation_id = serializers.HyperlinkedRelatedField(view_name='rest_sim_result', queryset=simulationParams.objects.all())
    class Meta:
        model = simulationResults
        fields = ['simulation_id', 'agg_results']
