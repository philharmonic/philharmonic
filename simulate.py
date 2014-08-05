#!/usr/bin/env python

import click

#from philharmonic import conf_test
import philharmonic

# TODO: combine this with schedule.py

@click.command()
@click.option('--conf', default='philharmonic.settings.base',
              help='The main conf module to load.')
def load_settings_run(conf):
    philharmonic._setup(conf)
    from philharmonic.simulator.simulator import run
    run()

# TODO: inputgen command

if __name__ == "__main__":
    load_settings_run()
