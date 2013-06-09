import pickle
import os
import multiprocessing

from django.db import models
from pybrain.tools.shortcuts import buildNetwork
from pybrain.structure import GaussianLayer, LSTMLayer, SigmoidLayer, SoftmaxLayer, LinearLayer, TanhLayer
from pybrain.datasets import SupervisedDataSet, SequentialDataSet, ClassificationDataSet
from pybrain.supervised.trainers import BackpropTrainer

# Create your models here.


class Network(models.Model):
    name = models.CharField(max_length=50)
    date = models.DateTimeField('run date')
    inputs = models.FileField(upload_to='documents')
    email = models.EmailField()
    sequential = models.BooleanField()
    done = models.BooleanField(default=False)

    def __unicode__(self):
        return self.name

    def handle_uploaded_file(self, f):
        destination = open(self.inputs.__str__(), 'wb+')
        for chunk in f.chunks():
            destination.write(chunk)
        destination.close()

    #Works with data sets
    def makeSupervisedDS(self, inp, target, inp_samples, target_samples):
        ds = SupervisedDataSet(inp, target)
        i = 0
        for _ in inp_samples:
            ds.addSample(tuple(inp_samples[i]), tuple(target_samples[i]))
            i += 1
        return ds

    def makeSequentialDS(self, inp, target, sequences):
        ds = SequentialDataSet(inp, target)
        for sequence in sequences:
            for (inpt, tar) in zip(sequence, sequence[1:]):
                ds.newSequence()
                ds.appendLinked(inpt, tar)
        return ds

    def makeClassificationDS(self, inp, inp_samples, target_samples):
        ds = ClassificationDataSet(inp)
        i = 0
        for _ in inp_samples:
            ds.addSample(inp_samples[i], target_samples[i])
            i += 1
        ds._convertToOneOfMany()
        return ds

    def parseLine(self, line):
        res = []
        work = line.split(' ')
        for i in range(len(work)):
            res.append(int(work[i]))
        return tuple(res)

    def readFile(self):
        self.inputs.open(mode='rb')
        line = self.inputs.readline()
        inpt = []
        target = []
        if line == 'INPUT\n':
            self.sequential = False
            line = self.inputs.readline()
            counter = 0
            while line != 'TARGET\n':
                inpt.append(self.parseLine(line))
                line = self.inputs.readline()
                counter += 1
            line = self.inputs.readline()
            self.input_length = counter
            while counter != 0:
                target.append(self.parseLine(line))
                line = self.inputs.readline()
                counter -= 1
            print inpt
            print target
        else:
            self.sequential = True
            inpt.append(self.parseLine(line))
            for line in self.inputs:
                inpt.append(self.parseLine(line))
            print inpt
        self.inputs.close()
        return inpt, target

    bias = [False, True]
    recurrent = [False, True]
    layers = ['GaussianLayer', 'LSTMLayer', 'SigmoidLayer', 'SoftmaxLayer', 'LinearLayer', 'TanhLayer']

    def getTop3(self):
        runs = SingleRun.objects.filter(net=self)
        mins = [1., 1., 1.]
        min_id = [0, 0, 0]
        for run in runs:
            if run.best_run < mins[0]:
                mins[2] = mins[1]
                mins[1] = mins[0]
                mins[0] = run.best_run
                min_id[2] = min_id[1]
                min_id[1] = min_id[0]
                min_id[0] = run.id
            elif run.best_run < mins[1]:
                mins[2] = mins[1]
                mins[1] = run.best_run
                min_id[2] = min_id[1]
                min_id[1] = run.id
            elif run.best_run < mins[2]:
                mins[2] = run.best_run
                min_id[2] = run.id
        return min_id

    def chk(self, processes):
        isDone = False
        toRemove = []
        while not isDone:
            flag = False
            for tr in toRemove:
                processes.remove(tr)
                toRemove = []
            for process in processes:
                if process.is_alive():
                    flag = True
                else:
                    toRemove.append(process)
                    if flag:
                        isDone = True
        self.done = True
        self.save()

    def run(self):
        inp, tar = self.readFile()
        try:
            os.mkdir('/home/mmaxy/PycharmProjects/coursework/files/errors/' + self.name + '/')
            os.mkdir('/home/mmaxy/PycharmProjects/coursework/files/xmls/' + self.name + '/')
        except:
            pass
        if self.sequential:
            ds = self.makeSequentialDS(len(inp[0]), len(inp[0]), inp)
            processes = []
            for b in self.bias:
                for r in self.recurrent:
                    for hidden in self.layers:
                        for out in self.layers:
                            tmp = ds.copy()
                            sr = SingleRun(bias=b,
                                           recurrent=r,
                                           hidden_layer=hidden,
                                           output_layer=out,
                                           name=str(1 + len(processes)),
                                           net=self,
                                           net_type='sequences')
                            sr.save()
                            p = multiprocessing.Process(target=sr.run, args=(tmp,))
                            processes.append(p)
                            p.start()
            self.chk(processes)
        else:
            ds = self.makeClassificationDS(len(inp[0]), inp, tar)
            processes = []
            for b in self.bias:
                for r in self.recurrent:
                    for hidden in self.layers:
                        for out in self.layers:
                            tmp = ds.copy()
                            sr = SingleRun(bias=b,
                                           recurrent=r,
                                           hidden_layer=hidden,
                                           output_layer=out,
                                           name=str(1 + len(processes)),
                                           net=self)
                            p = multiprocessing.Process(target=sr.run, args=(tmp,))
                            processes.append(p)
                            p.start()
            ds = self.makeSupervisedDS(len(inp[0]), len(tar[0]), inp, tar)
            for b in self.bias:
                for r in self.recurrent:
                    for hidden in self.layers:
                        for out in self.layers:
                            tmp = ds.copy()
                            sr = SingleRun(bias=b,
                                           recurrent=r,
                                           hidden_layer=hidden,
                                           output_layer=out,
                                           name=str(1 + len(processes)),
                                           net=self)
                            p = multiprocessing.Process(target=sr.run, args=(tmp,))
                            processes.append(p)
                            p.start()
            self.chk(processes)


class SingleRun(models.Model):
    net = models.ForeignKey(Network)
    name = models.CharField(max_length=50)
    bias = models.BooleanField()
    recurrent = models.BooleanField()
    hidden_layer = models.CharField(max_length=50)
    output_layer = models.CharField(max_length=50)
    net_type = models.CharField(max_length=50)
    error_log = models.FileField(upload_to='media/errors/')
    ready_xml = models.FileField(upload_to='media/xmls/')
    best_run = models.FloatField(null=True, blank=True)
    total_runs = models.IntegerField(blank=True, null=True)

    layer = {'GaussianLayer': GaussianLayer, 'LSTMLayer': LSTMLayer, 'SigmoidLayer': SigmoidLayer,
             'SoftmaxLayer': SoftmaxLayer, 'LinearLayer': LinearLayer, 'TanhLayer': TanhLayer}

    def createNetwork(self, inpt, hidden, target):
        n = buildNetwork(inpt, hidden, target, hiddenclass=self.layer[self.hidden_layer],
                         outclass=self.layer[self.output_layer], bias=self.bias, recurrent=self.recurrent)
        return n

    def train(self, net, ds):
        trainer = BackpropTrainer(net, ds)
        out = trainer.trainUntilConvergence(maxEpochs=500)
        return out

    def getURL(self):
        return 'http://127.0.0.1:8000/media/xmls/' + self.net.name + '/' + self.name

    def run(self, ds):
        if self.net_type == 'classification':
            n = self.createNetwork(len(ds['input'][0]),
                                   int(1.5 * len(ds['input'][0])),
                                   1)
        elif self.net_type == 'sequences':
            n = self.createNetwork(len(ds['input'][0]),
                                   int(1.3 * (len(ds['input'][0]) + len(ds['target'][0]))),
                                   len(ds['target'][0]))
        else:
            n = self.createNetwork(len(ds['input'][0]),
                                   int(1.3 * (len(ds['input'][0]) + len(ds['target'][0]))),
                                   len(ds['target'][0]))
        out = self.train(n, ds)
        self.best_run = min(out[0])
        self.total_runs = len(out[0])
        #self.error_log.path = 'media/errors/' + self.net.name + '/' + self.name
        #self.ready_xml.path = 'media/xmls/' + self.net.name + '/' + self.name
        error = open('/home/mmaxy/PycharmProjects/coursework/files/errors/' + self.net.name + '/' + self.name, 'wb')
        for s in out[0]:
            error.write(str(s))
            error.write('\n')
        error.close()
        xml = open('/home/mmaxy/PycharmProjects/coursework/files/xmls/' + self.net.name + '/' + self.name, 'w')
        pickle.dump(n, xml)
        xml.close()
        self.save()