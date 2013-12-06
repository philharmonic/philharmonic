from philharmonic import conf

class IManager(object):
    """abstract cloud manager. Asks the scheduler what to do, given the current
    state of the environment and arbitrates the actions to the cloud.

    """

    #def set_scheduler(self, scheduler):
    #    self._scheduler

    #scheduler = property(set_scheduler, get_scheduler, "the scheduler instance")

    def __init__(self, scheduler):
        """Create manager's assets."""
        self.scheduler = scheduler

    def run(self):
        raise NotImplemented



class ManagerFactory(object):
    """Easier manager creation"""

    @staticmethod
    def create_from_conf(conf):
        """pass a conf module to read paramenters from"""

        # schedulers to choose from
        from philharmonic.scheduler.peak_pauser import PeakPauser, NoScheduler
        # managers to choose from
        from philharmonic.manager.manager import Manager
        from philharmonic.simulator.simulator import Simulator

        # create the scheduler
        ChosenScheduler = globals()[conf.scheduler]
        if not ChosenScheduler:
            scheduler = NoScheduler()
        else:
            scheduler = ChosenScheduler()
        # connect everything in a manager
        ChosenManager = globals()[conf.manager]
        manager = ChosenManager(scheduler)
        return manager

#TODO: rethink the order of creation
