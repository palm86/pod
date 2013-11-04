from residuals import Unweighted


class ScanDataSet(object):

    def __init__(self, name, fitter, data_source, model, weighter=None):
        self.name = name
        self.fitter = fitter
        self.data_source = data_source
        self.model = model
        self.weighter = weighter

        if not self.weighter:
            self.weighter = Unweighted()

        self.variables = self.data_source.variables
        self.v = self.data_source.v
        self.variable_names = self.data_source.variable_names
        self.v_name = self.data_source.v_name

        self.fitter.addDataSet(self)

    def _init(self, parameter_names):
        self.model._init(parameter_names)

    def getWeightedResiduals(self, parameter_set=None, mean_v=None):
        if not parameter_set is None:
            self.model.setParameterSet(parameter_set)
            v_cap = self.model.getSimulatedY(self.variables)
            residuals = self.weighter.getResiduals(self, v_cap)

        else:
            residuals = self.weighter.getResiduals(self, mean_v)

        return residuals

    def getResiduals(self, parameter_set=None, mean_v=None):
        if not parameter_set is None:
            v_cap = self.getSimulatedY(parameter_set)
            residuals = self.v - v_cap

        else:
            residuals = self.v - mean_v

        return residuals

    def getSimulatedY(self, parameter_set):
        self.model.setParameterSet(parameter_set)
        return self.model.getSimulatedY(self.variables)
