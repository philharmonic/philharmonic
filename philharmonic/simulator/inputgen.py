"""generate artificial input"""

from philharmonic.scheduler.generic.model import Machine, Server

def small_infrastructure():
    num_servers = 3
    Machine.resource_types = ['RAM', '#CPUs']
    RAM = [4]*num_servers
    numCPUs = [2]*num_servers
    servers = []
    for i in range(num_servers):
        s = Server(RAM[i], numCPUs[i])
        servers.append(s)
    return servers
