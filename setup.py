from setuptools import setup

from socrata2sql import __version__


setup(
    name='socrata2sql',
    version=__version__,
    description='SQL loader for Socrata data sets',
    url='http://github.com/DallasMorningNews/socrata2sql',
    author='Andrew Chavez / The Dallas Morning News',
    author_email='newsapps@dallasnews.com',
    license='MIT',
    packages=['socrata2sql'],
    install_requires=[
        'docopt~=0.6',
        'progress~=1.4',
        'sodapy~=1.5',
        'SQLalchemy~=1.2',
        'tabulate~=0.8',
        'geoalchemy2~=0.5',
    ],
    entry_points={
        'console_scripts': [
            'socrata2sql=socrata2sql.cli:main',
        ],
    },
    python_requires=">=3"
)
