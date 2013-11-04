import numpy
from residuals import Robust
import result as pod_result

try:
    from scipy.optimize import leastsq
except:
    print 'Scipy is not installed'

try:
    from lmfit import minimize, Parameters
except:
    print 'lmfit-py is not installed'


class Algorithm(object):
    def __init__(self):
        pass

    def setName(self, name):
        self.name = name

    def setDataSets(self, data_sets):
        self.data_sets = data_sets

    def setFitter(self, fitter):
        self.fitter = fitter

    def objFunc(self, p):
        res = numpy.array([])

        for i in self.data_sets:
            res = numpy.hstack((res, i.getWeightedResiduals(p)))

        return res

    def solve(self, parameters):
        self.parameters = parameters
        self.parameter_names = [i.name for i in parameters]
        result = self.optimize(parameters)
        return self.createResultsObject(result)

    def optimize(self, parameters):
        assert False, 'The algorithm does not implement the method: optimize'

    def createResultsObject(self, result):
        assert False, 'The algorithm does not implement the method: createResultsObject'

    def _calcNumberOfObservations(self):
        n = 0

        for data_set in self.data_sets:
            n += len(data_set.v)

        return n

    def _calcDegOfFreedomT(self, n):
        return n - 1.0

    def _calcDegOfFreedomE(self, n, p):
        return n - p - 1.0

    def _calcR2(self, ss_err, ss_tot):
        return 1.0 - ss_err / ss_tot

    def _calcStdDev(self, ss_err, residuals):
        return numpy.sqrt(ss_err / len(residuals))

    def _calcSS_err(self, residuals):
        return numpy.sum(numpy.square(residuals))

    def _calcSS_total(self):
        v = numpy.array([])
        for data_set in self.data_sets:
            v = numpy.hstack((v, data_set.v))
        v_mean = v.mean()

        ss_tot = numpy.array([])

        for data_set in self.data_sets:
            ss_tot = numpy.hstack((ss_tot, data_set.getWeightedResiduals(mean_v=v_mean)))

        return numpy.sum(numpy.square(ss_tot))


class scipy_leastsq(Algorithm):
    def __init__(self):
        Algorithm.__init__(self)

        self.ftol = 1.49012e-08
        self.xtol = 1.49012e-08
        self.gtol = 0.0
        self.maxfev = 0
        self.factor = 100
        self.diag = None

    def optimize(self, parameters):
        x0 = [i.init for i in parameters]
        return leastsq(self.objFunc, x0, Dfun=None, full_output=1, ftol=self.ftol, xtol=self.xtol, gtol=self.gtol, maxfev=self.maxfev, factor=self.factor, diag=self.diag)

    def createResultsObject(self, result):
        r = pod_result.Result(self.name, self.data_sets, result)
        r.parameters = self.parameters
        r.parameter_names = self.parameter_names
        r.fitted_parameters = result[0]

        r.cov_matrix = result[1]

        info_dict = result[2]
        r.num_func_evals = info_dict['nfev']
        r.residuals = info_dict['fvec']

        r.message = result[3]
        r.success = result[4] in [1, 2, 3, 4]

        if (result[0] < 0).any():
            r.success = False

        if not r.success:
            return r

        r.n = self._calcNumberOfObservations()
        r.deg_freedom_t = self._calcDegOfFreedomT(r.n)
        r.deg_freedom_e = self._calcDegOfFreedomE(r.n, len(r.fitted_parameters))
        r.ss_tot = self._calcSS_total()
        r.ss_err = self._calcSS_err(r.residuals)
        r.r2 = self._calcR2(r.ss_err, r.ss_tot)
        r.r2_adj = self._calcR2(r.ss_err / r.deg_freedom_e, r.ss_tot / r.deg_freedom_t)
        r.std_dev = self._calcStdDev(r.ss_err, r.residuals)
        r.std_err = self._calcStdErr(r.cov_matrix, r.ss_err, r.n, len(r.fitted_parameters))

        return r

    def _calcStdErr(self, cov_matrix, ss_err, n, p):
        if cov_matrix is None:
            return
        return numpy.sqrt(ss_err / (n - p) * numpy.diag(cov_matrix))


class robust_biweight(scipy_leastsq):
    def setFitter(self, fitter):
        self.fitter = fitter

        for dataset in self.fitter.data_sets:
            dataset.weighter = Robust()

    def optimize(self, parameters):
        # print "Start optimization"
        x0 = [i.init for i in parameters]
        res = leastsq(self.objFunc, x0, Dfun=None, full_output=1, ftol=self.ftol, xtol=self.xtol, gtol=self.gtol, maxfev=self.maxfev, factor=self.factor, diag=self.diag)

        iterations = 0
        parameters_unchanged = 0

        while(True):
            x0 = res[0]

            # print "Adjust weighting"
            for ds in self.fitter.data_sets:
                v_cap = ds.getSimulatedY(x0)
                e = ds.getResiduals(x0)
                ds.weighter.adjustWeighting(v_cap, e)

            # print 'Re-optimize'
            res = leastsq(self.objFunc, x0, Dfun=None, full_output=1, ftol=self.ftol, xtol=self.xtol, gtol=self.gtol, maxfev=self.maxfev, factor=self.factor, diag=self.diag)

            # if (res[0] == x0).all():
            if self.parameters_unchanged(res[0], x0):
                parameters_unchanged += 1
                if parameters_unchanged > 5:
                    print "Solution converged after {} iterations".format(iterations-5)
                    break
            else:
                parameters_unchanged = 0

            iterations += 1
            # If we don't have convergence after 150 cycles (where weights stop changing)
            # there is no point in further iterations.
            if iterations >= 200:
                print "Max iterations ({}) reached before convergence".format(iterations)
                break

            if (res[0] < 0).any():
                print "No solution found after {} iterations (negative parameters)".format(iterations)
                break

        return res

    def parameters_unchanged(self, a, b):
        """
        Checks whether the elements of a and b agree up to the first 5 digits
        """
        sig = 5
        return (
            (a == b).all()
            or ((a*10**sig).astype(numpy.int32) == (b*10**sig).astype(numpy.int32)).all()
        )

    def _calcNumberOfObservations(self):
        n = 0

        for data_set in self.data_sets:
            wi = data_set.weighter.wi
            Wi = data_set.weighter.Wi
            n += numpy.sum(Wi/wi)

        return n


class lmfit_minimize(Algorithm):
    def __init__(self):
        Algorithm.__init__(self)

        self.kws = {}
        self.kws['engine'] = 'leastsq'  # {'leastsq, anneal, lbfgsb'}

    def funcWrapper(self, parameters):
        p = [parameters[v].value for v in parameters]
        return self.objFunc(p)

    def buildLmfitParameters(self, parameters):
        lp = Parameters()

        for p in parameters:
            lp.add(p.name, value=p.init, min=p.min, max=p.max)
            for k in p.kws:
                setattr(lp[p.name], k, p.kws[k])

        return lp

    def optimize(self, parameters):
        self.lmfit_parameters = self.buildLmfitParameters(parameters)

        return minimize(self.funcWrapper, self.lmfit_parameters, **self.kws)

    def createResultsObject(self, result):
        # lmfit_py's results contains stuff that cannot be pickled
        r = pod_result.Result(self.name, self.data_sets, None)
        r.parameters = self.parameters
        r.lmfit_parameters = self.lmfit_parameters
        r.parameter_names = self.parameter_names

        r.fitted_parameters = []
        for pn in r.parameter_names:
            r.fitted_parameters.append(r.lmfit_parameters[pn].value)

        r.std_err = None
        if result.errorbars:
            r.std_err = []
            for pn in r.parameter_names:
                r.std_err.append(r.lmfit_parameters[pn].stderr)

        r.num_func_evals = result.nfev
        r.residuals = result.residual

        if result.errorbars:
            r.cov_matrix = result.covar
            r.covar_scaled = result.scale_covar

        r.message = result.lmdif_message
        r.success = result.success

        if not r.success:
            return r

        r.n = self._calcNumberOfObservations()
        r.deg_freedom_t = self._calcDegOfFreedomT(r.n)
        r.deg_freedom_e = self._calcDegOfFreedomE(r.n, len(r.fitted_parameters))
        r.ss_tot = self._calcSS_total()
        r.ss_err = self._calcSS_err(r.residuals)
        r.r2 = self._calcR2(r.ss_err, r.ss_tot)
        r.r2_adj = self._calcR2(r.ss_err / r.deg_freedom_e, r.ss_tot / r.deg_freedom_t)
        r.std_dev = self._calcStdDev(r.ss_err, r.residuals)

        return r
