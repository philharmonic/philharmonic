'''
Created on Oct 9, 2012

@author: kermit
'''

historical_en_prices_file = "../../io/energy_price_data-test.csv"

# Benchmark
#===========

# if scripted == False, will do just a local dummy benchmark
scripted = False
# for True ...

# host on which the benchmark VM is deployed (for energy measurements)
host = "snowwhite"

# VM (instance) which executes the benchmark  
instance = "kermit-test"

# the command to execute as a benchmark (use ssh to execute something in a VM)
#command = "/usr/bin/ssh 192.168.100.4 ls"
command = "./benchmark.sh"

# time to sleep between checking if the benchmark finished or needs to be paused
sleep_interval = 1 # seconds
