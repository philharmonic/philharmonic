#!/bin/bash
#ssh 192.168.100.4 
# ServerAliveInterval - koliko cesto slati upite je li server ziv
# ServerAliveCountMax - koliko neodgovorenih upita tolerirati
ssh -o "ServerAliveInterval=60" -o "ServerAliveCountMax=7200" 192.168.100.4 python projekti/lp/berserk/trunk/berserk.py
