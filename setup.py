'''
Created on 14. 9. 2012.

@author: kermit
'''

import os

from setuptools import setup, find_packages
from Cython.Build import cythonize

def read(fname):
    return open(os.path.join(os.path.dirname(__file__), fname)).read()

setup(
    name = "philharmonic",
    version = "0.1",
    packages = find_packages(),
    install_requires = ['pandas>=0.8.0',
                        'numpy>=1.6.1',
                        'pysnmp>=4.2',
#                        '"Twisted Web">=12.2',
                        'SOAPpy>=0.12'],
    # sudo apt-get intsall python-twisted-web
    ext_modules = cythonize('**/*.pyx'),
    zip_safe = True,

    # metadata for upload to PyPI
    author = "Drazen Lucanin",
    author_email = "kermit666@gmail.com",
    #url = "http://pypi.python.org/pypi/foc-forecaster",
    long_description=read('README.md'),
    entry_points = {
        'console_scripts' : ['ph=simulate:cli', 'philharmonic=simulate:cli']
    }
)
