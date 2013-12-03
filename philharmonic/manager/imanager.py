

class IManager(object):
    """abstract cloud manager. Asks the scheduler what to do, given the current
    state of the environment and arbitrates the actions to the cloud.

    """

    def __init__(self, scheduler):
        """Create manager's assets."""
        self.scheduler = scheduler

    def run(self):
        raise NotImplemented
