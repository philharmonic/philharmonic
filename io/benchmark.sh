#!/bin/bash
#ssh 192.168.100.4 
# ServerAliveInterval - koliko cesto slati upite je li server ziv
# ServerAliveCountMax - koliko neodgovorenih upita tolerirati
#ssh -o "ServerAliveInterval=60" -o "ServerAliveCountMax=7200" 192.168.100.4 python projekti/lp/berserk/trunk/berserk.py
#ssh 192.168.100.4 "cd projekti/lp/berserk/trunk/; python berserk.py"

ssh kermit@192.168.100.4 "cd ~/projekti/lp/berserk/trunk/; nohup python berserk.py > berserk.out 2>berserk.err < /dev/null &"
