#!/bin/usr/python3

import os

path = "/tmp/SSH"
while True:
    obj = os.scandir(path=path)
    for entry in obj:
        if entry.is_file():
            f = open(path+entry.name,"r")
            print(f.read())
