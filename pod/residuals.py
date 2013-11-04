import numpy
import itertools


class Unweighted(object):
    def getResiduals(self, dataset, vcap):
        print dataset.v - vcap
        return (dataset.v - vcap)


# class HalfWeighted(object):
#     def getResiduals(self, dataset, vcap):
#         return (dataset.v - vcap) / numpy.sqrt(numpy.abs(vcap))


# class ScaledResidualProvider(object):
#     def getResiduals(self, dataset, vcap):
#         return (dataset.v - vcap) / vcap


# class WeightedResidualProvider(object):
#     def __init__(self, weights):
#         self.weights = weights

#     def getResiduals(self, dataset, vcap):
#         return numpy.sqrt(self.weights)*(dataset.v - vcap)


class Robust(object):
    def __init__(self):
        self.sigma_ratio = None
        self.iterations = 0
        self.n = 50

    def adjustWeighting(self, vcap_prev, e):
        self.iterations += 1
        self.vcap_prev = vcap_prev

        # For the first n iterations we leave the weights alone
        if self.iterations < self.n + 1:
            self.sigma_ratio = self.get_sigma_ratio(e)
            self.wi = self.get_wi(self.sigma_ratio, self.vcap_prev)
            self.ui = (numpy.sqrt(self.wi)*(self.v - self.vcap_prev))/(6.0*numpy.median(numpy.abs(numpy.sqrt(self.wi)*(self.v - self.vcap_prev))))
            self.Wi = numpy.array(map(self.get_Wi, self.wi, self.ui))
        # Then we use a logistic function that decreases towards zero
        elif self.iterations < self.n + 101:
            self.sigma_ratio = self.get_sigma_ratio(e)
            new_wi = self.get_wi(self.sigma_ratio, self.vcap_prev)
            self.wi = self.wi + (new_wi - self.wi)/(1 + numpy.exp(1*(self.iterations-100)))
            self.ui = (numpy.sqrt(self.wi)*(self.v - self.vcap_prev))/(6.0*numpy.median(numpy.abs(numpy.sqrt(self.wi)*(self.v - self.vcap_prev))))
            self.Wi = numpy.array(map(self.get_Wi, self.wi, self.ui))
        # Finally we scale the weights with zero
        else:
            pass

    def get_sigma_ratio(self, e):
        sigmas = []

        i = range(len(self.vcap_prev))
        pairs = itertools.product(i, i)

        for p in pairs:
            i = p[0]
            j = p[1]

            if not i == j:
                if ((e[j]**2 - e[i]**2)/(self.vcap_prev[j]**2 - self.vcap_prev[i]**2)) < 0:
                    sigmaij = 1e20
                elif ((e[i]**2*self.vcap_prev[j]**2 - e[j]**2*self.vcap_prev[i]**2)/(self.vcap_prev[j]**2 - self.vcap_prev[i]**2)) < 0:
                    sigmaij = 0
                else:
                    sigmaij = (self.vcap_prev[i]**2*e[j]**2 - self.vcap_prev[j]**2*e[i]**2)/(e[i]**2 - e[j]**2)

                sigmas.append(sigmaij)

        return numpy.sqrt(numpy.median(numpy.array(sigmas)))

    def get_wi(self, sigma_ratio, vi):
        return (sigma_ratio**2 + self.v_mean**2) / (sigma_ratio**2 + vi**2)

    def get_Wi(self, w, u):
        if abs(u) <= 1:
            return w*(1-u**2)**2
        else:
            return 0.0

    def getResiduals(self, dataset, vcap):
        if self.iterations == 0:
            self.v = dataset.v
            self.v_mean = dataset.v.mean()
            self.wi = self.get_wi(self.v_mean, dataset.v)

            return numpy.sqrt(self.wi)*(self.v - vcap)
        else:
            return numpy.sqrt(self.Wi)*(self.v - vcap)
