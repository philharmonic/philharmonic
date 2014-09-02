Development
-----------
Development packages

    pip install -r requirements/dev.txt

(for the experimental workflow, install from `requirements/extra.txt` as well)

To test just run this from the project's root

    nosy

Debugging
---------
To enter ipdb on errors:

    ipython --pdb -- simulate.py --conf=philharmonic.settings.ga

Code organisation
-----------------
Some useful facts.

### Settings

The settings systems can be used throughout the codebase by simply doing
`from philharmonic import conf` and then using the various properties therein.
An important note is that `philharmonic._setup()` is assumed to be called
in order to load any custom settings module.
