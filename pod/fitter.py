import scipy
import numpy

import algorithm


class Fitter(object):
    def __init__(self, name=None):
        self.name = name
        self.data_sets = []
        self.parameters = []
        self.initial_values = numpy.array([])
        self._algorithm = None

        self.settings = {}
        self.settings['leastsq_use_default_maxfev'] = True
        self.settings['leastsq_maxfev'] = 0
        self.settings['mode_validate_parameters'] = False
        self.settings['mode_make_params_abs'] = False
        self.settings['mode_penalize_nans'] = True

    def setAlgorithm(self, algorithm):
        self._algorithm = algorithm
        self._algorithm.setName(self.name)
        self._algorithm.setFitter(self)
        self._algorithm.setDataSets(self.data_sets)

    def addDataSet(self, dataSet):
        self.data_sets.append(dataSet)

    def addParameter(self, name, init=None, min=None, max=None, **kws):
        """
        Adds a parameter to the list of parameters that must be fitted.

        addParameter('Vmax', 10.0)
        """

        self.parameters.append(Parameter(name, init=init, min=min, max=max, **kws))

    def solve(self):
        for dset in self.data_sets:
            dset._init(self.parameters)

        if self._algorithm is None:
            self.setAlgorithm(algorithm.scipy_leastsq())

        return self._algorithm.solve(self.parameters)


class Parameter(object):
    def __init__(self, name, init=None, min=None, max=None, **kws):
        self.name = name
        self.init = init
        self.min = min
        self.max = max
        self.kws = kws


def test():
    import datasource
    import model
    import dataset

    f = Fitter()

    # define source of "experimental data"
    function = lambda s, i: (10.0*s/1.0)/(1.0 + s/1.0 + i/5.0)
    data_source = datasource.Generated_ScanDataSource(
        function,
        ['s', 'i'],
        'v',
        [scipy.logspace(-2, 2, 50), scipy.logspace(-2, 2, 10)],
        noise=0.3
    )

    # define model
    model = model.Equation_Model("Vmax*s/Ks/(1 + s/Ks + i/Ki)", ['s', 'i'])

    dataset.ScanDataSet('name', f, data_source, model)

    # specify the optimization algorithm, defaults to scipy_leastsq
    #~ alg = algorithm.scipy_leastsq()
    alg = algorithm.robust_biweight()
    f.setAlgorithm(alg)

    # specify the parameters to be fitted
    f.addParameter('Vmax', init=1.0, min=0, max=100)
    f.addParameter('Ks', init=1.0, min=0, max=10)
    f.addParameter('Ki', init=1.0, min=0, max=10)

    r = f.solve()
    r.writeOutput()
