from setuptools import setup  # type: ignore
from setuptools import find_packages

setup(
    name='eew_nagios',
    version='1.0',
    description=('Custom Nagios Plugins to check EEW Aquisionion servers ' +
                 'and Instruments'),
    author='Jonathan Gosset',
    author_email='jonathan.gosset@nrcan-rncan.gc.ca',
    packages=find_packages(exclude=('tests')),
    package_data={
        'eew_nagios': [
            'data/*.config'
        ]
    },
    python_requires='>3.7',
    # Requires python packages
    install_requires=[
        'requests'
    ],
    extras_require={
        'dev': [
            'pytest',
            'mypy'
        ]
    },
    entry_points={
        'console_scripts': [
            'check_apollo_availability = \
                eew_nagios.bin.check_apollo_availability:main',
            'check_guralp_availability = \
                eew_nagios.bin.check_guralp_availability:main'
        ]
    }
)
