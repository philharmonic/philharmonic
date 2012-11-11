'''
Created on 14. 9. 2012.

@author: kermit
'''
from setuptools import setup, find_packages
import os


def read(fname):
    return open(os.path.join(os.path.dirname(__file__), fname)).read()

setup(
    name = "philharmonic",
    version = "0.1",
    packages = find_packages(),
    install_requires = ['pandas>=0.8.0',
                        'numpy>=1.6.1'],
    zip_safe = True,
    
    # metadata for upload to PyPI
    author = "Drazen Lucanin",
    author_email = "kermit666@gmail.com",
    #url = "http://pypi.python.org/pypi/foc-forecaster",
    long_description=read('README.md')
)
