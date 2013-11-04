import jinja2
import numpy
import os
import pkg_resources
import re
import itertools


class DefaultOutput(object):
    def __init__(self, result, **kwargs):
        self.result = result

        template_text = pkg_resources.resource_stream(__name__, 'templates/txt_output.jinja2').read()
        self.template = jinja2.Template(template_text)
        self.template.globals.update(zip=zip)

    def writeOutput(self):
        if not self.result.success:
            print 'Optimization of this dataset was unsuccessful.'
            return

        r2 = "{0:g}".format(self.result.r2)
        r2adj = "{0:g}".format(self.result.r2_adj)
        sd = "{0:g}".format(self.result.std_dev)
        msg = self.result.message
        eqn = "eqn not specified yet"

        paramLength = max(map(len, self.result.parameter_names))

        par = []
        var = []
        err = []

        for i in range(len(self.result.parameter_names)):
            par.append("{p:{minWidth}}".format(p=self.result.parameter_names[i], minWidth=paramLength))
            var.append("{v:>10.5g}".format(v=self.result.fitted_parameters[i]))

            if self.result.cov_matrix is not None:
                err.append(" +/- {e:10.5g}".format(e=self.result.std_err[i]))
            else:
                err.append('')

        text = self.template.render(r2=r2, r2adj=r2adj, sd=sd, message=msg, equation=eqn, par=par, var=var, err=err)

        print text


class ParametersTxtOutput(object):
    def __init__(self, result, **kwargs):
        self.result = result

        template_text = pkg_resources.resource_stream(__name__, 'templates/txt_output.jinja2').read()
        self.template = jinja2.Template(template_text)
        self.template.globals.update(zip=zip)

    def writeOutput(self):
        r2 = "{0:g}".format(self.result.r2)
        r2adj = "{0:g}".format(self.result.r2_adj)
        sd = "{0:g}".format(self.result.std_dev)
        msg = self.result.message
        eqn = "eqn not specified yet"

        paramLength = len(max(self.result.parameter_names))

        par = []
        var = []
        err = []

        for i in range(len(self.result.parameter_names)):
            par.append("{p:{minWidth}}".format(p=self.result.parameter_names[i], minWidth=paramLength))
            var.append("{v:>10.5g}".format(v=self.result.fitted_parameters[i]))

            if self.result.cov_matrix is not None:
                err.append(" +/- {e:10.5g}".format(e=self.result.std_err[i]))
            else:
                err.append('')

        text = self.template.render(r2=r2, r2adj=r2adj, sd=sd, message=msg, equation=eqn, par=par, var=var, err=err)

        filepath = 'pod_results/{0}.txt'.format(self.result.name)
        dirpath = os.path.dirname(filepath)
        if not os.path.exists(dirpath):
            os.makedirs(dirpath)

        f = open(filepath, 'w')
        f.write(text)
        f.close()

# class ParametersCsvOutput(object):
#     def writeresult(self, name):
#         if not self.success:
#             print 'Optimization of this dataset was unsuccessful.'
#             return

#         csv_file = open('pod_results/' + name + '.csv', 'a')
#         csv_writer = csv.writer(csv_file)
#         csv_writer.writerow(['Adj R2', self.r2_adj])
#         csv_writer.writerow(['R2', self.r2])
#         for i in range(len(self.parameter_names)):
#             print self.parameter_names[i], '=', (self.fitted_parameters)[i]
#             csv_writer.writerow([self.parameter_names[i], (self.fitted_parameters)[i]])
#         csv_writer.writerow([])
#         csv_file.close()


class Data3DOutput(object):
    def __init__(self, result, **kwargs):
        self.result = result
        self.data_set_y = {}

        template_text = pkg_resources.resource_stream(__name__, 'templates/dat3d.jinja2').read()
        self.template = jinja2.Template(template_text)

    def assignYNameToDataSeries(self, data_set_name, y_name):
        self.data_set_y[data_set_name] = y_name

    def writeOutput(self):
        for ds in self.result.data_sets:
            x_name = ds.x_variable
            y_name = self.data_set_y[ds.name]

            dsys = []
            for s in ds.data_series:
                dsys.append(s.assay_conditions[y_name])

            text = self.template.render(x_name=x_name, y_name=y_name, data_series=ds.data_series, dsys=dsys)

            filepath = 'pod_results/{0}_{1}.dat'.format(self.result.name, ds.name)
            dirpath = os.path.dirname(filepath)
            if not os.path.exists(dirpath):
                os.makedirs(dirpath)

            f = open(filepath, 'w')
            f.write(text)
            f.close()


class PgfPlots3DOutput(object):
    def __init__(self, result, **kwargs):
        self.result = result
        self.data_set_y = {}
        self.reverse_x = kwargs.get('reverse_x', False)
        self.reverse_y = kwargs.get('reverse_y', False)

        self.replacements = {
            '_': 'us',
            '0': 'zero',
            '1': 'one',
            '2': 'two',
            '3': 'three',
            '4': 'four',
            '5': 'five',
            '6': 'six',
            '7': 'seven',
            '8': 'eight',
            '9': 'nine',
        }

        template_text = pkg_resources.resource_stream(__name__, 'templates/pgfplots_3d.jinja2').read()
        self.template = jinja2.Template(template_text)

    def writeOutput(self):
        r2 = "{0:g}".format(self.result.r2)
        r2adj = "{0:g}".format(self.result.r2_adj)
        sd = "{0:g}".format(self.result.std_dev)

        par = []
        var = []

        for i in range(len(self.result.parameter_names)):
            p = self.result.parameter_names[i]

            for j in self.replacements:
                p = p.replace(j, self.replacements[j])

            par.append(p)
            var.append("{v}".format(v=self.result.fitted_parameters[i]))

        for dataset in self.result.data_sets:
            datafile = 'pod_results/{0}_{1}.dat'.format(self.result.name, dataset.name)
            datafile = os.path.abspath(datafile)

            variable_value_sets = [set(dataset.variables[:, dataset.variable_names.index(i)]) for i in dataset.variable_names]
            xy_candidates = []

            for v, s in zip(dataset.variable_names, variable_value_sets):
                if len(s) > 1:
                    xy_candidates.append(v)

            xy_combinations = itertools.combinations(xy_candidates, 2)

            for xy_combo in xy_combinations:
                xcolumn = xy_combo[0]
                ycolumn = xy_combo[1]
                zcolumn = dataset.v_name

                constant_variables = list(set(dataset.variable_names)-set(xy_combo))
                constant_variable_values = [set(dataset.variables[:, dataset.variable_names.index(i)]) for i in constant_variables]

                constant_combinations = itertools.product(*constant_variable_values)

                for constant_combo in constant_combinations:
                    expression = '<not supported by pod simulator>'

                    constants_string = ''

                    if hasattr(dataset.model, 'expression'):
                        expression = dataset.model.expression

                        # replace x and y variables
                        expression = re.sub(r'\b{0}\b'.format(xcolumn), 'x', expression)
                        expression = re.sub(r'\b{0}\b'.format(ycolumn), 'y', expression)

                        for constant, value in zip(constant_variables, constant_combo):
                            constants_string = '{}{}{}'.format(constants_string, constant, value)
                            expression = re.sub(r'\b{0}\b'.format(constant), str(value), expression)

                        # replace python symbols with pgfplots symbols
                        expression = expression.replace('**', '^')

                        # make replacements only in parameters, to avoid replacing actual numerals
                        for p in self.result.parameter_names:
                            replacement_p = p
                            for j in self.replacements:
                                replacement_p = replacement_p.replace(j, self.replacements[j])

                            expression = expression.replace(p, '\\{0}'.format(replacement_p))

                    render_params = {
                        'xcolumn': xcolumn,
                        'ycolumn': ycolumn,
                        'zcolumn': zcolumn,
                        'reverse_x': self.reverse_x,
                        'reverse_y': self.reverse_y,
                        'r2': r2,
                        'r2adj': r2adj,
                        'sd': sd,
                        'expression': expression,
                        'par': par,
                        'var': var,
                        'xdom': 10,
                        'ydom': 10,
                        'zlabel': 'v',
                        'ylabel': ycolumn,
                        'xlabel': xcolumn,
                        'datafile': datafile,
                    }

                    text = self.template.render(**render_params)

                    filepath = 'pod_results/{0}_{1}_3d_{2}vs{3}_{4}.tikz.tex'.format(self.result.name, dataset.name, xcolumn, ycolumn, constants_string)
                    dirpath = os.path.dirname(filepath)
                    if not os.path.exists(dirpath):
                        os.makedirs(dirpath)

                    f = open(filepath, 'w')
                    f.write(text)
                    f.close()


class ResidualPlotOutput(object):
    def __init__(self, result):
        self.result = result

        template_text = pkg_resources.resource_stream(__name__, 'templates/pgfplots_residuals.jinja2').read()
        self.template = jinja2.Template(template_text)

    def writeOutput(self):
        r2 = "{0:g}".format(self.result.r2)
        r2adj = "{0:g}".format(self.result.r2_adj)
        sd = "{0:g}".format(self.result.std_dev)

        for dataset in self.result.data_sets:
            # absmax = numpy.abs(numpy.max(dataset.getWeightedResiduals(parameter_set=self.result.fitted_parameters)))
            absmax = numpy.max(numpy.abs(dataset.getWeightedResiduals(parameter_set=self.result.fitted_parameters)))

            datafile = 'pod_results/{0}_{1}.dat'.format(self.result.name, dataset.name)
            datafile = os.path.abspath(datafile)

            x_list = dataset.variable_names

            for x in x_list:
                render_params = {
                    'ylabel': '$\sqrt{{w}}({0} - \hat{{{0}}})$'.format(dataset.v_name),
                    'xlabel': x,
                    'ycolumn': 'residuals_weighted'.format(dataset.v_name),
                    'xcolumn': x,
                    'r2': r2,
                    'r2adj': r2adj,
                    'sd': sd,
                    'absmax': absmax,
                    'datafile': datafile,
                }

                text = self.template.render(**render_params)

                filepath = 'pod_results/{0}_{1}_residualplot_{2}.tikz.tex'.format(self.result.name, dataset.name, x)
                dirpath = os.path.dirname(filepath)
                if not os.path.exists(dirpath):
                    os.makedirs(dirpath)

                f = open(filepath, 'w')
                f.write(text)
                f.close()

            x = '{}_cap'.format(dataset.v_name)

            render_params = {
                'ylabel': '$\sqrt{{w}}({0} - \hat{{{0}}})$'.format(dataset.v_name),
                'xlabel': '$\hat{{{0}}}$'.format(dataset.v_name),
                'ycolumn': 'residuals_weighted'.format(dataset.v_name),
                'xcolumn': x,
                'r2': r2,
                'r2adj': r2adj,
                'sd': sd,
                'absmax': absmax,
                'datafile': datafile,
            }

            text = self.template.render(**render_params)

            filepath = 'pod_results/{0}_{1}_residualplot_{2}.tikz.tex'.format(self.result.name, dataset.name, x)
            dirpath = os.path.dirname(filepath)
            if not os.path.exists(dirpath):
                os.makedirs(dirpath)

            f = open(filepath, 'w')
            f.write(text)
            f.close()


class FullDataTableOutput(object):
    def __init__(self, result):
        self.result = result

    def writeOutput(self):
        map(self.writeDataSetOutput, self.result.data_sets)

    def writeDataSetOutput(self, dataset):
        labels = []

        # Add variables
        labels.extend(dataset.variable_names)
        data = dataset.variables.copy()

        # Add v
        labels.append(dataset.v_name)
        data = numpy.hstack((data, dataset.v.reshape(len(dataset.v), 1)))

        # Add vcap
        labels.append('{}_cap'.format(dataset.v_name))
        vcap = dataset.getSimulatedY(self.result.fitted_parameters)
        data = numpy.hstack((data, vcap.reshape(len(vcap), 1)))

        # Add unweighted residuals
        labels.append("residuals")
        residuals = dataset.getResiduals(self.result.fitted_parameters)
        data = numpy.hstack((data, residuals.reshape(len(residuals), 1)))

        # Add weighted residuals
        labels.append("residuals_weighted")
        residuals = dataset.getWeightedResiduals(self.result.fitted_parameters)
        data = numpy.hstack((data, residuals.reshape(len(residuals), 1)))

        # Add weights
        if hasattr(dataset.weighter, 'Wi'):
            labels.append("weights")
            weights = numpy.array(dataset.weighter.Wi)
            data = numpy.hstack((data, weights.reshape(len(weights), 1)))

        if hasattr(dataset.weighter, 'wi'):
            labels.append("biweight_1")
            weights = numpy.array(dataset.weighter.wi)
            data = numpy.hstack((data, weights.reshape(len(weights), 1)))

        if hasattr(dataset.weighter, 'Wi') and hasattr(dataset.weighter, 'wi'):
            labels.append("biweight_2")
            weights = numpy.array(dataset.weighter.Wi)/numpy.array(dataset.weighter.wi)
            data = numpy.hstack((data, weights.reshape(len(weights), 1)))

        filepath = 'pod_results/{0}_{1}.dat'.format(self.result.name, dataset.name)
        dirpath = os.path.dirname(filepath)
        if not os.path.exists(dirpath):
            os.makedirs(dirpath)

        f = open(filepath, 'w')
        for l in labels:
            f.write('{label}\t'.format(label=l))
        f.write('\n')
        numpy.savetxt(f, data, delimiter='\t')
        f.close()
