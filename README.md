Philharmonic
============
[![Build Status](https://travis-ci.org/philharmonic/philharmonic.svg)](https://travis-ci.org/philharmonic/philharmonic) [![Coverage Status](https://img.shields.io/coveralls/philharmonic/philharmonic.svg)](https://coveralls.io/r/philharmonic/philharmonic)

Philharmonic is a geo-distributed cloud simulator written in Python.
It compares the energy and cost efficiency of different dynamic VM scheduling
algorithms in a realistic environment with real-time electricity prices and
temperature-dependent cooling.
It offers a simple OpenStack controller that actually pauses and/or suspends
instances based on the electricity prices, although this experimental
part is not the focus of development any more.

Installation
------------

If you have Python, pip and virtualenv set up, install the necessary
dependencies within a cloned repository.

    pip install -e .

Or if you don't have the repository cloned and just want to try it out you can
directly install from the git repository.

    pip install -e git+ssh://git@github.com:philharmonic/philharmonic.git#egg=philharmonic

Both of these commands will automatically pull in all the dependencies, but if
you want to use your system's package manager to speed up the installation
a bit, read below.

### Dependencies

Ubuntu dependencies

    sudo apt-get install python-numpy python-pandas python-matplotlib \
        python-scipy python-pysnmp4 python-soappy python-twisted \
        python-twisted-web

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

Philharmonic is used in the terminal through a command line interface (CLI).
First it is necessary to generate the input datasets (optionally setting
the `--conf` flag - see below).

    python simulate.py inputgen [--conf=philharmonic.settings.ga]

Then the simulation can be started. To use the default settings:

    python simulate.py run

### Configuration

The main settings to all the subcommands are defined through a config file
passed to the CLI. The config file is specified in Python and can inherit
and override properties from other config files. To pass different settings
use the `--conf` flag, e.g.:

    python simulate.py run --conf=philharmonic.settings.ga

This configuration sets various simulator and scheduler settings, as well as the
locations of various input comma separated value (CSV) files
and output directories.


Contributing
------------
Read [HACKING.md](https://github.com/philharmonic/philharmonic/blob/master/HACKING.md)
file for some information on how the code is organised.

License
-------
Philharmonic is distributed under the GNU General Public License - see the
accompanying
[LICENSE](https://github.com/philharmonic/philharmonic/blob/master/LICENSE) file
for more details.
