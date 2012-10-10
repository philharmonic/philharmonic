'''
Created on Oct 9, 2012

@author: kermit
'''

historical_en_prices_file = "en_prices.csv"

# the command to execute as a benchmark
command = "ssh 192.168.100.4 ls"

# time to sleep between checking if the benchmark finished or needs to be paused
sleep_interval = 5 # seconds
