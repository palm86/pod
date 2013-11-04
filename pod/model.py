import numpy

class Pysces_Model(object):
    def __init__(self, psc_file, variable_names, v_name, psc_string=None):
        self.psc_file = psc_file
        self.psc_string = psc_string
        self.variable_names = variable_names
        self.v_name = 'J_{0}'.format(v_name) if v_name[0:2] != 'J_' else v_name

    def _init(self, parameters):
        import pysces
        if self.psc_string is None:
            self.mod = pysces.model(self.psc_file)
        else:
            self.mod = pysces.model(self.psc_file, loader='string', fString=self.psc_string)
        self.mod.SetQuiet()

        self.parameter_names = [i.name for i in parameters]

    def setParameterSet(self, parameter_set):
        for name, value in zip(self.parameter_names, parameter_set):
            setattr(self.mod, name, value)

    def getSimulatedY(self, variables):
        y = []

        for row in variables:
            for col in range(len(self.variable_names)):
                setattr(self.mod, self.variable_names[col], row[col])
            self.mod.doState()
            y.append(getattr(self.mod, self.v_name))

        y = numpy.array(y)
        # y = y.reshape(len(y), 1)

        return y

    def prepareForPickle(self):
        del self.mod


class Equation_Model(object):
    def __init__(self, expression, variable_names):
        self.expression = expression
        self.variable_names = variable_names

    def _init(self, parameters):
        self.parameter_names = [i.name for i in parameters]

    def setParameterSet(self, parameter_set):
        self.parameter_set = parameter_set

    def getSimulatedY(self, variables):
        # args = [variables[:,i] for i in range(len(variables[0]))] + list(self.parameter_set)

        local = {}
        for i in range(len(self.variable_names)):
            local[self.variable_names[i]] = variables[:,i]

        for k, v in zip(self.parameter_names, self.parameter_set):
            local[k] = v

        y = eval(self.expression, {}, local)
        return numpy.array(y)

    def prepareForPickle(self):
        pass