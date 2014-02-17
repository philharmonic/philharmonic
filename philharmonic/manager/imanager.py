from philharmonic import conf

class IManager(object):
    """abstract cloud manager. Asks the scheduler what to do, given the current
    state of the environment and arbitrates the actions to the cloud.

    """

    factory = {
        "scheduler": None,
        "environment": None,
        "cloud": None,
        "driver": None
    }

    def _empty(self):
        return None

    def _create(self, cls):
        return (cls or self._empty)()

    def __init__(self):
        """Create manager's assets."""
        self.scheduler = self._create(self.factory['scheduler'])
        self.environment = self._create(self.factory['environment'])
        self.cloud = self._create(self.factory['cloud'])
        if self.cloud:
            self.cloud.driver = self.factory['driver']

    def run(self):
        raise NotImplemented


from philharmonic.utils import deprecated

class ManagerFactory(object):
    """Easier manager creation"""

    @staticmethod
    @deprecated
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
