'''
Created on Oct 4, 2012

@author: kermit

The Royal Philharmonic Orchestra Goes to the Bathroom
'''
import subprocess

def list_files():
    resp = subprocess.call("ls -hal", shell=True)
    print(resp)

def execute(command):
    resp = subprocess.call(command, shell=True)
    return resp

def authenticate():
    command = ". ~/creds/openrc"
    if execute(command)==0: print("success!")

def instance_info(instance_name):
    command = "nova show " + instance_name
    print(execute(command))
    
def basic_test():
    #list_files()
    authenticate()
    instance_info("test-image")

if __name__ == '__main__':
    basic_test()
