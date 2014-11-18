PYTHON_SETTINGS=--pdb
PROFILE_SETTINGS=-l 40 -s cumtime
PHILHARMONIC_SETTINGS=--conf philharmonic.settings.ga
PYTHON=ipython -- 

test:
	nosetests

build:
	python setup.py build_ext --inplace

buildtest:
	$(MAKE) build
	$(MAKE) test

profile:
	$(PYTHON) simulate.py profile \
		$(PROFILE_SETTINGS) $(PHILHARMONIC_SETTINGS)

run:
	$(PYTHON) simulate.py run  $(PHILHARMONIC_SETTINGS)
