Development
-----------
Development packages:

    pip install -r requirements/dev.txt

(for the experimental workflow, install from `requirements/extra.txt` as well)

To test just run this from the project's root:

    nosetests

or to run the tests continusly, monitoring file changes:

    nosy

Debugging
---------
To enter ipdb on errors:

    ipython --pdb -- simulate.py --conf=philharmonic.settings.ga

Profiling
---------
From the terminal run:

    python simulate.py profile --conf=philharmonic.settings.bcf -l 20 -s cumtime

where `conf` is the configuration you would like to analyse.

Alternatively open an IPython prompt and run:

    from philharmonic.profiler import profile_run
    %prun profile_run()

To profile memory usage, run the desired executable from the terminal:

    mprof run ./simulate.py explore
    mprof plot

Code organisation
-----------------
Some useful facts.

### Settings

The settings systems can be used throughout the codebase by simply doing
`from philharmonic import conf` and then using the various properties therein.
An important note is that `philharmonic._setup()` is assumed to be called
in order to load any custom settings module.
