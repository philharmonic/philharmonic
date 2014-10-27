Philharmonic
============
[![Build Status](https://travis-ci.org/philharmonic/philharmonic.svg)](https://travis-ci.org/philharmonic/philharmonic) [![Coverage Status](https://img.shields.io/coveralls/philharmonic/philharmonic.svg)](https://coveralls.io/r/philharmonic/philharmonic)

Philharmonic is a cloud simulator & partial OpenStack manager written in Python.
It compares the energy and cost efficiency of different dynamic VM scheduling
algorithms in a realistic environment with real-time electricity prices and
temperature-dependent cooling.
It offers a simple OpenStack controller that pauses and/or suspends instances
based on the electricity prices, although this experimental part is not the
focus of development any more.

Installation
------------

    pip install -e git+ssh://git@github.com:philharmonic/philharmonic.git#egg=philharmonic

### Dependencies

Ubuntu dependencies

    sudo apt-get install python-numpy python-pandas python-matplotlib python-scipy python-pysnmp4 python-soappy python-twisted python-twisted-web

or

    pip install -r requirements.txt

*Note:* creating a virtualenv with `--system-site-packages` and still
installing the scientific packages via `apt-get` is much faster as no
compiling is necessary.

### Compiling Cython sources

Before using the package, it is necessary to build the Cython sources.

    python setup.py build_ext --inplace

Running
-------
First it is necessary to generate the input datasets.

    python simulate.py inputgen [--conf=philharmonic.settings.ga]

Then the simulation can be started. To use the default settings:

    python simulate.py run

To pass different settings use the `--conf` flag, e.g.:

    python simulate.py run --conf=philharmonic.settings.ga


Contributing
------------
Read [HACKING.md](https://github.com/philharmonic/philharmonic/blob/master/HACKING.md)
file for some information on how the code is organised.

License
-------
Philharmonic is distributed under the GNU General Public License - see the
accompanying [LICENSE](https://github.com/philharmonic/philharmonic/blob/master/LICENSE) file for more details.
