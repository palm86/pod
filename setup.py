from distutils.core import setup

setup(name='pod',
    version='0.1',
    description='Kinetic Parameter Optimization Utility',
    author='Danie Palm',
    author_email='dcpalm@sun.ac.za',
    packages=['pod'],
    license = 'BSD (2-clause)',
    package_dir = {'': ''},
    package_data={'pod': ['templates/*']}
    )
