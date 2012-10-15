'''
Created on Oct 4, 2012

@author: kermit

The Royal Philharmonic Orchestra Goes to the Bathroom
'''
import subprocess

dummy = False

def list_files():
    resp = subprocess.call("ls -hal", shell=True)
    print(resp)

def execute(command):
    if not dummy:
        resp = subprocess.call(command, shell=True)
        if resp==0:
            print("Executed command '%s' - sucess!" % (command))
        return resp
    else:
        print("Dummy execute command: '%s'" % (command))
        return 0

def authenticate():
    command = ". ~/creds/openrc"
    print(execute(command))
    #if execute(command)==0: print("success!")

def instance_info(instance_name):
    command = "nova show " + instance_name
    print(execute(command))

def suspend(instance):
    command = "nova suspend " + instance
    print(execute(command))

def resume(instance):
    command = "nova resume " + instance
    print(execute(command))

def pause(instance):
    command = "nova pause " + instance
    print(execute(command))

def unpause(instance):
    command = "nova unpause " + instance
    print(execute(command))

def migrate(instance, machine):
    pass

    
def basic_test():
    #list_files()
    authenticate()
    instance_info("kermit-test")
    #pause("kermit-test")

if __name__ == '__main__':
    basic_test()
