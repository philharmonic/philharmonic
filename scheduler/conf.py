'''
Created on Oct 9, 2012

@author: kermit
'''

historical_en_prices_file = "en_prices.csv"

# the command to execute as a benchmark
#command = "/usr/bin/ssh 192.168.100.4 ls"
command = "./benchmark.sh"

# time to sleep between checking if the benchmark finished or needs to be paused
sleep_interval = 1 # seconds
