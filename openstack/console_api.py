'''
Created on Oct 4, 2012

@author: kermit

The Royal Philharmonic Orchestra Goes to the Bathroom
'''
import subprocess

def list_files():
    resp = subprocess.call("ls -hal", shell=True)
    print(resp)
    
def basic_test():
    list_files()
if __name__ == '__main__':
    basic_test()