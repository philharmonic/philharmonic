Philharmonic is a Python program offering a simple OpenStack controller that pauses and/or suspends instances based on the electricity prices.

Installation
============

    pip install -e bzr+ssh://bazaar.launchpad.net/+branch/philharmonic/#egg=philharmonic

Dependencies
------------
Ubuntu dependencies

    sudo apt-get install python-numpy python-pandas python-matplotlib python-scipy python-pysnmp4 python-soappy python-twisted python-twisted-web

OR

    pip install -r requirements.txt

*Note:* creating a virtualenv with `--system-site-packages` and still
installing the scientific packages via `apt-get` is much faster as no
compiling is necessary.

Development
-----------
Development packages

    pip install -r requirements/dev.txt

(for the experimental workflow, install from `requirements/extra.txt` as well)

To test just run this from the project's root

    nosy

Running
=======

To use default settings:

    python simulate.py

To pass different settings:

    python simulate.py --conf=philharmonic.settings.ga


Contributing
============

Settings
--------
Just `import philharmonic.conf` (`philharmonic._setup` assumed to be called) and
use any properties in this module.

Debugging
---------
To enter ipdb on errors:

    ipython --pdb -- simulate.py --conf=philharmonic.settings.ga

Code status
-----------

* [![Build Status](https://travis-ci.org/philharmonic/philharmonic.svg)](https://travis-ci.org/philharmonic/philharmonic)

License
-------
Philharmonic is distributed under the GNU General Public License - see the
accompanying LICENSE file for more details.
