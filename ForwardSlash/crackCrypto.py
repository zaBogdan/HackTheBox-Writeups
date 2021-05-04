#!/usr/bin/python2

WORDLIST = '/usr/share/wordlists/rockyou.txt'
CIPHERTEXT = 'files/ciphertext'


print("[!] Loading ROCKYOU wordlist and CIPHERTEXT")
with open(WORDLIST, 'r') as wordlist:
    wordlist = wordlist.readlines()
with open(CIPHERTEXT) as ciphertext:
    ciphertext = ciphertext.read()
print("[+] Both files successfully loaded!")

def format(text):
    return ''.join([i if ord(i) < 128 else ' ' for i in text])

#Using the decrypt function from the original file.
def decrypt(key, msg):
    key = list(key)
    msg = list(msg)
    for char_key in reversed(key):
        for i in reversed(range(len(msg))):
            if i == 0:
                tmp = ord(msg[i]) - (ord(char_key) + ord(msg[-1]))
            else:
                tmp = ord(msg[i]) - (ord(char_key) + ord(msg[i-1]))
            while tmp < 0:
                tmp += 256
            msg[i] = chr(tmp)
    return ''.join(msg)

def bruteforce():
    print("[!] Starting bruteforce")
    for word in wordlist:
        word = str(word.rstrip('\n'))
        decr = decrypt(word, ciphertext)
        if 'encryption' in decr:
            decr = format(decr)
            print '[+] Message has been decrypted: `{}`  with this key: {}'.format(decr,word)
            break

bruteforce()
