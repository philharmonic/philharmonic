'''
Created on Oct 9, 2012

@author: kermit
'''

from philharmonic import conf
from energy_predictor import EnergyPredictor
from philharmonic.scheduler.ischeduler import IScheduler
from philharmonic.logger import log
from philharmonic.cloud.model import Schedule, Pause, Unpause

class PeakPauser(IScheduler):

    def __init__(self, cloud=None, driver=None):
        IScheduler.__init__(self, cloud, driver)
        self.paused=False

    # TODO: use price data from environment, not directly from file
    # !!!
    def parse_prices(self, location, percentage_to_pause):
        self.energy_price = EnergyPredictor(location, percentage_to_pause)

    def price_is_expensive(self, time=None):
        return self.energy_price.is_expensive(time)

    def pause(self, vm):
        if not self.paused: # this should be checked in the model
            vm.pause() # TODO: think if this interface is better
            # and decide what to do with this manual Schedule mgmt:
            pause = Pause(vm)
            t = self.environment.get_time()
            #import ipdb; ipdb.set_trace()
            self.schedule.add(pause, t)
            if not conf.dummy: # TODO: this should go inside vm.pause()
                openstack.pause(conf.instance)
            self.paused = True
            log("paused")

    def unpause(self, vm):
        if self.paused: # see pause()
            vm.unpause()
            if not conf.dummy: # TODO: this should go inside vm.unpause()
                openstack.unpause(conf.instance)
            log("unpaused")
            self.paused = False

    def initialize(self):
        #openstack.dummy = conf.dummy
        #openstack.authenticate()
        self.parse_prices(conf.historical_en_prices, conf.percentage_to_pause)
        # act on a set of VMs, not only one
        for vm in self.cloud.vms:
            self.unpause(vm) # in case the VM was paused before we started

    def finalize(self):
        self.unpause()  # don't leave a VM hanging after the experiment's done

    def reevaluate(self):
        """Look at the current state of the Cloud and el. prices in the
        environment and schedule pause/unpause actions if necessary.

        @returns: a Schedule with a time series of actions.

        """
        self.schedule = Schedule()
        t = self.environment.get_time()
        if self.price_is_expensive(t):
            for vm in self.cloud.vms: #TODO: green instances only
                self.pause(vm)
        else:
            for vm in self.cloud.vms: #TODO: green instances only
                self.unpause(vm)
        return self.schedule

