import numpy
import itertools
import scipy
import random


class CSV_ScanDataSource(object):
    """ We assume a CSV file with data in columns, the last column is the observed rate"""

    def __init__(self, csv_file, variable_names, v_name):
        self.csv_file = csv_file
        self.variable_names = variable_names
        self.v_name = v_name

        try:
            data = numpy.genfromtxt(fname=self.csv_file, comments='#', delimiter=',', skip_header=1, missing='')
            self.variables = data[:, :-1]
            self.v = data[:, -1]
        except:
            print 'The data file format is invalid'
            raise


class Generated_ScanDataSource(object):
    def __init__(self, function, variable_names, v_name, ranges, relative_noise=0, constant_noise=0, outliers=0):
        self.function = function
        self.variable_names = variable_names
        self.v_name = v_name
        self.ranges = ranges
        self.relative_noise = relative_noise
        self.constant_noise = constant_noise

        self.variables = None
        self.v = numpy.array([])

        for w in itertools.product(*ranges):
            v = self.function(*w)

            r1 = random.random()
            r2 = random.random()

            v = v + v*self.relative_noise*(r1 - 0.5) + self.constant_noise*(r2 - 0.5)

            self.v = numpy.hstack((self.v, v))

            if self.variables is None:
                self.variables = numpy.array(w)
            else:
                self.variables = numpy.vstack((self.variables, w))

        for i in range(outliers):
            a = 0
            b = len(self.v) - 1
            self.v[random.randint(a, b)] = self.v[random.randint(a, b)]*(1.0 + 0.3)


class Pysces_ScanDataSource(object):
    def __init__(self, psc_file, variable_names, v_name, ranges, psc_string=None):
        self.psc_file = psc_file
        self.psc_string = psc_string
        self.variable_names = variable_names
        self.v_name = 'J_{0}'.format(v_name) if v_name[0:2] != 'J_' else v_name
        self.ranges = ranges

        import pysces
        if self.psc_string is None:
            self.mod = pysces.model(self.psc_file)
        else:
            self.mod = pysces.model(self.psc_file, loader='string', fString=self.psc_string)
        self.mod.SetQuiet()

        self.variables = None
        self.v = numpy.array([])

        self.scanner = pysces.Scanner(self.mod)
        for n, r in zip(self.variable_names, self.ranges):
            self.scanner.addScanParameter(n, r[0], r[1], r[2])
        self.scanner.addUserOutput(self.v_name)
        self.scanner.Run()
        results = self.scanner.getResultMatrix()
        self.variables = results[:, 0:-1]
        self.v = results[:, -1]
        # self.v = self.v.reshape(len(self.v), 1)