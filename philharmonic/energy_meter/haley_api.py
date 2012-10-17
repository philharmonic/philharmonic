'''
Created on Jun 15, 2012

@author: kermit
'''

#from pysnmp.entity.rfc3413.oneliner import cmdgen
from pysnmp.v4.entity.rfc3413.oneliner import cmdgen
from pyasn1.type.univ import ObjectIdentifier
import pandas as pd

from exception import *

class Wattmeter(object):
    '''
    Meassures energy consumption for the HALEY cluster
    '''

    def __init__(self):
        '''
        Constructor
        '''
        # use Mibble to log in to your SNMP device and read this code
        self._main_prefix = "1.3.6.1.4.1.534.6.6.6.1.2.2.1"
        create_prefix = lambda x : self._main_prefix + "." + str(x)
        self._index_prefix = create_prefix(1) 
        self._label_prefix = create_prefix(2)
        self._operational_state_prefix = create_prefix(3)
        self._current_prefix = create_prefix(4)
        self._max_current_prefix = create_prefix(5)
        self._voltage_prefix = create_prefix(6)
        self._active_power_prefix = create_prefix(7)
        self._apparent_power_prefix = create_prefix(8)
        self._power_factor_prefix = create_prefix(9)
        self._current_upper_warning_prefix = create_prefix(21)
        self._current_upper_critical_prefix = create_prefix(23)
        
        self._build_machine_dic()
        
    def _query(self, prefix, identifier):
        # GET Command Generator
        url = "powerman.infosys.tuwien.ac.at"
        user = "kermit"
        pw = "kermit123"
        port = 161
        wait_time = 1 # seconds
        retries_num = 5
        code = prefix + "." + str(identifier)
        
        snmp = cmdgen.CommandGenerator()
        errorIndication, errorStatus, errorIndex, varBinds = snmp.getCmd(
            # USER DATA
            #-----------------
            # SNMP v1
            #cmdgen.CommunityData('test-agent', 'public', 0),
            # SNMP v2
            #authData = cmdgen.CommunityData('test-agent', 'public'),
            # SNMP v3
            cmdgen.UsmUserData(user, authKey=pw, privKey=pw),
            # TARGET
            #-------------
            cmdgen.UdpTransportTarget((url, port), timeout=wait_time, retries=retries_num),
            # Plain OID
            #(1,3,6,1,2,1,1,1,0),
            # ((mib-name, mib-symbol), instance-id)
            #(('SNMPv2-MIB', 'sysObjectID'), 0)
            ObjectIdentifier(code)
            )
        if errorIndication:
            print(errorIndication)
        else:
            if errorStatus:
                print('%s at %s\n' % (
                    errorStatus.prettyPrint(),
                    errorIndex and varBinds[int(errorIndex)-1] or '?'
                    ))
            else:
                for name, val in varBinds:
                    #print '%s = %s' % (name.prettyPrint(), val.prettyPrint())
                    return val.prettyPrint()
    
    
    def _build_machine_dic(self):
        self._machine_id = {}
        indices = range(12,20)
        for index in indices:
            label = self._query(self._label_prefix, index).lower()
            self._machine_id[label] = index
            
    def _abstract_query_on_machine(self,  prefix, machine):
        identifier = self._machine_id[machine]
        return float(self._query(prefix, identifier))
        
    def measure_single(self, machine, metric):
        """
        Returns the desired metric (e.g. active power consumption in Watts) for a machine.
        @param machine: string representing a machine (e.g. "snowwhite")
        @param metric: string, name of the metric (see bellow for available strings)
        @return: float consumption 
        """
        prefix = None
        if metric == "active_power":
            prefix = self._active_power_prefix
        elif metric == "apparent_power":
            prefix = self._apparent_power_prefix
        else:
            raise UnknownMetricError
        return self._abstract_query_on_machine(prefix, machine)
        
    def measure_multiple(self, machines, metrics):
        """
        Fetch measures on machines, metrics
        @param machines: list of machine names 
        @param metrics: list of method objects to get metrics
        
        @return: Pandas Series of measured values indexed by (machine, metric)
        e.g.:
        machine      metric                   value
        -------------------------------------------------
        snowwhite    active_power             38
                     apparent_power           57
        bashful      active_power             50
                     apparent_power           78
        """
        index_tuples = [(machine, metric) for machine in machines for metric in metrics]
        index = pd.MultiIndex.from_tuples(index_tuples, names=["machine", "metric"])
        measured_values = []
        for machine, metric in index_tuples:
            measured_values.append(self.measure_single(machine, metric))
        measured_series = pd.Series(measured_values, index = index)
        return measured_series
            
            
            