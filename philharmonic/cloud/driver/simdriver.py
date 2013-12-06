"""dummy cloud driver that stores all the actions applied to it
and provides data about the current state.

"""

from philharmonic import Pause, Unpause, Migration

events = None

def connect():
    global events
    events = []

def store(action):
    t = self.environment.t
    event = (t, action)
    events.append(event) #TODO: timestamp

def suspend(instance):
    raise NotImplemented

def resume(instance):
    raise NotImplemented

def pause(instance):
    action = Pause(instance)
    store(action)

def unpause(instance):
    action = Unpause(instance)
    store(action)

def migrate(instance, machine):
    action = Unpause(instance, machine)
    store(action)
