'''
Created on Jun 15, 2012

@author: kermit
'''
#from pylab import *
import matplotlib.pyplot as plt
import numpy as np

from haley_api import Wattmeter
from continuous_energy_meter import ContinuousEnergyMeter
from runner_til_keypressed import RunnerTilKeypressed

machines = ["snowwhite", "grumpy"]
metrics = ["active_power", "apparent_power"]

def draw_current_state():
    plt.hold(True)
    en_meter = Wattmeter()
    colors = ["r", "b"]
    #machines = ["grumpy", "snowwhite", "sneezy"]
    results = en_meter.multiple(machines, metrics)
    mat = np.matrix(results[1:])
    positions = np.arange(0,len(machines)*len(metrics),len(metrics))
    print(mat)
    rows = len(np.array(mat[:,0].T)[0])
    for i in range(rows):
        data_row = np.array(mat[i, :])[0]
        plt.bar(positions, data_row, color = colors[i])
        positions = [position+1 for position in positions]
    plt.show()
    
def draw_state_long():
    # gather data
    #machines = ["grumpy", "snowwhite", "sneezy"]
    interval = 1 # seconds
    cont_en_meter = ContinuousEnergyMeter(machines, metrics, interval)
    runner = RunnerTilKeypressed()
    runner.run(cont_en_meter)
    # draw it
    print ("Gonna draw this:")
    data = cont_en_meter.get_all_data() 
    print(data)
    #plt.plot(data)
    plt.figure()
    data.plot()
    #plt.show()
    
    
if __name__ == '__main__':
    #draw_current_state()
    draw_state_long()