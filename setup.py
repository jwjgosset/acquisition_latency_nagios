from setuptools import setup  # type: ignore
from setuptools import find_packages

setup(
    name='acquisition_nagios',
    version='1.2.2',
    description=('Custom Nagios Plugins to check EEW Aquisionion servers ' +
                 'and Instruments'),
    author='Jonathan Gosset',
    author_email='jonathan.gosset@nrcan-rncan.gc.ca',
    packages=find_packages(exclude=('tests')),
    package_data={
        'acquisition_nagios': [
            'data/*.config'
        ]
    },
    python_requires='>3.7',
    # Requires python packages
    install_requires=[
        'requests',
        'click'
    ],
    extras_require={
        'dev': [
            'pytest',
            'pytest-cov',
            'mypy'
        ]
    },
    entry_points={
        'console_scripts': [
            'check_apollo_availability = \
                acquisition_nagios.bin.check_apollo_availability:main',
            'check_guralp_availability = \
                acquisition_nagios.bin.check_guralp_availability:main'
        ]
    }
)
