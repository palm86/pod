pod
===

Modular nonlinear parameter optimization library

Installation
------------

```shell
$ python setup.py build
$ sudo python setup.py install
```

Example
-------

```python
import pod

f = pod.Fitter()

# Define source of "experimental data". The Michealis-Menten equation for
# competitive inhibition with some added noise in this case.
function = lambda s, i: (10.0*s/1.0)/(1.0 + s/1.0 + i/5.0)
data = pod.Generated_ScanDataSource(
    function,
    ['s', 'i'],
    'v',
    [scipy.logspace(-2, 2, 50), scipy.logspace(-2, 2, 10)],
    noise=0.3
)

# Define model. The same Michaelis-Menten equation, but no noise this time.
model = pod.Equation_Model("Vmax*s/Ks/(1 + s/Ks + i/Ki)", ['s', 'i'])

# A data set is a data/model pair. Multiple data sets may be provided; they
# will be fitted simultaneously.
pod.ScanDataSet('name', f, data, model)

# Specify the optimization algorithm, defaults to scipy_leastsq
alg = pod.robust_biweight()
f.setAlgorithm(alg)

# Specify the parameters to be fitted. The parameters from all the data
# sets must be specified here. Not all algorithms honour constraints!
f.addParameter('Vmax', init=1.0, min=0, max=100)
f.addParameter('Ks', init=1.0, min=0, max=10)
f.addParameter('Ki', init=1.0, min=0, max=10)

# And solve!
r = f.solve()
r.writeOutput()
```
