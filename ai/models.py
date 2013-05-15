from django.db import models
from pybrain.tools.shortcuts import buildNetwork
from pybrain.structure import BiasUnit, TanhLayer, GaussianLayer, GateLayer, LSTMLayer, MDLSTMLayer, SigmoidLayer, SoftmaxLayer, StateDependentLayer, FeedForwardNetwork, FullConnection, RecurrentNetwork
from pybrain.datasets import UnsupervisedDataSet, SupervisedDataSet
# Create your models here.


class Network(models.Model):
    name = models.CharField(max_length=50)
    date = models.DateTimeField('run date')
    network_type = models.CharField(max_length=50)
    inputs = models.FileField(upload_to='documents/')
    email = models.EmailField()

    def __unicode__(self):
        return self.name

    def handle_uploaded_file(self, f):
        destination = open(self.inputs.__str__(), 'wb+')
        for chunk in f.chunks():
            destination.write(chunk)
        destination.close()

    def run(self):
