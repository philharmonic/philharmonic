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
        """Pass a conf module to read paramenters from. The method creates
        a scheduler instance and constructs a manager with it.
        The manager's constructor will link it with the appropriate
        environment and cloud objects.

        """
        # schedulers to choose from
        from philharmonic.scheduler import PeakPauser, NoScheduler
        # managers to choose from
        from philharmonic.manager.manager import Manager
        from philharmonic.simulator.simulator import Simulator

        # create the scheduler
        ChosenScheduler = locals()[conf.scheduler]
        if not ChosenScheduler:
            scheduler = NoScheduler()
        else:
            scheduler = ChosenScheduler()
        # connect everything in a manager
        ChosenManager = locals()[conf.manager]
        manager = ChosenManager(scheduler)
        return manager

#TODO: rethink the order of creation
