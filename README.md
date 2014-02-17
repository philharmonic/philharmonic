Philharmonic is a Python program offering a simple OpenStack controller that pauses and/or suspends instances based on the electricity prices.

Installation
============

    pip install -e bzr+ssh://bazaar.launchpad.net/+branch/philharmonic/#egg=philharmonic

Dependencies
------------
Ubuntu dependencies

    sudo apt-get install python-numpy python-pandas python-pysnmp4 python-soappy python-twisted python-twisted-web

OR

    pip install -r requirements.txt

Development
-----------
Development packages

    pip install nose nosy nose-exclude yanc ipdbplugin mock coverage

OR

    pip install -r requirements/dev.txt

To test just run this from the project's root

    nosy

