import cProfile

import philharmonic

def profile(conf_module='philharmonic.settings.ga_profile'):
    from philharmonic import conf
    conf.prompt_configuration = False
    from philharmonic.simulator.simulator import run
    run()

def profile_run(conf_module='philharmonic.settings.ga_profile'):
    import philharmonic
    philharmonic._setup(conf_module)
    profile(conf_module)

def prun(cmd, globals_ctx, locals_ctx, lines=10, sort_by=None):
    """mimic IPython's %prun magic function"""
    import cProfile
    import pstats
    prof = cProfile.Profile()
    prof = prof.runctx(cmd, globals_ctx, locals_ctx)
    stats = pstats.Stats(prof).strip_dirs()
    if sort_by is not None:
        stats = stats.sort_stats(sort_by)
    stats.print_stats(lines)

def prun_real():
    """supposed to get the actual IPython's %prun execution, but not working"""
    from IPython import get_ipython
    ipython = get_ipython()
    ipython.magic("prun profile_run()")

if __name__ == "__main__":
    cProfile.run('profile_run()')
