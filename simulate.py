#!/usr/bin/env python

import click

#from philharmonic import conf_test
import philharmonic

# TODO: combine this with schedule.py

@click.group()
def cli():
    """The philharmonic command line interface."""
    pass

@cli.command('run')
@click.option('--conf', default='philharmonic.settings.base',
              help='The main conf module to load.')
@click.option('--scheduler', '-s', default=None,
              help='The scheduler class to use.')
def load_settings_run(conf, scheduler):
    philharmonic._setup(conf)
    from philharmonic.simulator.simulator import run
    run(custom_scheduler=scheduler)

# TODO: see if the --conf option can be a part of the cli group

@cli.command('inputgen')
@click.option('--conf', default='philharmonic.settings.base',
              help='The main conf module to load.')
def cli_inputgen(conf):
    philharmonic._setup(conf)
    from philharmonic.simulator.inputgen import generate_fixed_input
    generate_fixed_input()

@cli.command('explore')
@click.option('--conf', default='philharmonic.settings.ga_explore',
              help='The main conf module to load.')
def cli_explore(conf):
    philharmonic._setup(conf)
    from philharmonic.explorer import explore
    explore()

@cli.command('profile')
@click.option('--conf', default='philharmonic.settings.ga_profile',
              help='The main conf module to load.')
@click.option('--lines', '-l', default=10,
              help='Number of lines to show.')
@click.option('--sort', '-s', default=None,
              help='Column to sort by.')
def cli_profile(conf, lines, sort):
    philharmonic._setup(conf)
    from philharmonic import profiler
    profiler.prun('profiler.profile(conf_module={})'.format(conf),
                  globals(), locals(), lines, sort)

if __name__ == "__main__":
    #load_settings_run()
    cli()
