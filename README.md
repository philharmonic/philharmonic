Philharmonic is a Python program offering a simple OpenStack controller that pauses and/or suspends instances based on the electricity prices.

Installation
-------------

    pip install -e bzr+ssh://bazaar.launchpad.net/+branch/philharmonic/#egg=philharmonic

Extra
-----

Ubuntu dependencies

    sudo apt-get install python-numpy python-pandas python-pysnmp4 python-soappy python-twisted python-twisted-web

Development packages

    pip install nose nosy nose-exclude yanc ipdbplugin

To test just run this from the project's root

    nosy

