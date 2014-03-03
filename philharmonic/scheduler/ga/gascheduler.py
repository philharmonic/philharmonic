from philharmonic import Schedule
from philharmonic.scheduler.evaluator import normalised_combined_cost

class ScheduleUnit(Schedule):
    def calculate_fitness(self):
        now = self.environment.t
        #TODO: maybe move this method to the Scheduler
        el_prices = self.environment.current_data()
        normalised_cost = normalised_combined_cost(self.cloud, self.environment,
                                                    self, el_prices)
        # TODO: add constraint and SLA penalties
        return normalised_cost
