import output


class Result(object):
    def __init__(self, name, data_sets, result):
        self.name = name
        self.data_sets = data_sets
        self.result = result
        self.outputClasses = {output.DefaultOutput: {}}
        self.outputs = [output.DefaultOutput(self)]

    def _prepareForPickle(self):
        for dset in self.data_sets:
            dset.model.prepareForPickle()
        del self.outputs

    def _initAfterPickle(self):
        for dset in self.data_sets:
            dset._init(self.parameters)

        self.outputs = []
        for oc in self.outputClasses:
            # self.outputs.append(oc(self))
            self.outputs.append(oc(self, **self.outputClasses[oc]))

    def writeOutput(self, output=None):
        if output:
            if type(output) is list:
                for o in output:
                    o.writeOutput()
            else:
                output.writeOutput()
        else:
            for o in self.outputs:
                o.writeOutput()

    def addOutputClass(self, outputClass, **kwargs):
        self.outputClasses[outputClass] = kwargs
        self.outputs.append(outputClass(self, **kwargs))
