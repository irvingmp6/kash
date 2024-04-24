from setuptools import find_packages, setup
from _version import __version__

setup(
    name='kash',
    version=__version__,
    author = "Irving Martinez",
    packages=find_packages(),
    install_requires =[
        'numpy==1.24.4',
        'pandas==2.0.3',
        'python-dateutil==2.8.2',
        'pytz==2023.3.post1',
        'six==1.16.0',
        'tzdata==2023.3',
        'coverage'
    ],
    entry_points = {
        'console_scripts': [
            'kash = src.__main__:main',
        ]
    }
)