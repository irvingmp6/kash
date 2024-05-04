from setuptools import find_packages, setup

setup(
    name='kash',
    version='0.1.1',
    author = "Irving Martinez",
    packages=find_packages(),
    install_requires =[
        'coverage==7.5.0',
        'numpy==1.26.4',
        'pandas==2.2.2',
        'python-dateutil==2.9.0.post0',
        'pytz==2024.1',
        'setuptools==69.5.1',
        'six==1.16.0',
        'tzdata==2024.1',
    ],
    entry_points = {
        'console_scripts': [
            'kash = src.__main__:main',
        ]
    }
)