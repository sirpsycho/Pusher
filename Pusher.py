#!/usr/bin/python

import sys
import optparse
import getpass
import socket
import os
from time import sleep

try:
  import paramiko
except ImportError:
  print("[!] Could not find dependency 'paramiko'.  Try running 'pip install paramiko'")
  sys.exit()
try:
  from scp import SCPClient
except ImportError:
  print("[!] Could not find dependency 'scp'.  Try running 'pip install scp'")
  sys.exit()




# Get Options
parser = optparse.OptionParser()

parser.add_option('-u', '--username',
                  dest="username",
                  default="",
                  help='SSH username',
                 )
parser.add_option('-p', '--pass',
                  dest="password",
                  default="",
                  help='SSH password (leave blank to be prompted)',
                 )
parser.add_option('-k', '--key',
                  dest="sshkey",
                  default="",
                  help='SSH private key location (ex. /home/user/.ssh/id_rsa)',
                 )
parser.add_option('-S', '--server',
                  dest="server",
                  default="",
                  help='SSH server address (target machine)',
                 )
parser.add_option('-P', '--port',
                  dest="port",
                  default=22,
                  help='SSH port (default is 22)',
                 )
parser.add_option('-a', '--admin',
                  dest="admin",
                  default=False,
                  action="store_true",
                  help='Set this option to run as an administrator (runs "sudo -i" before executing commands)',
                 )
parser.add_option('-s', '--script',
                  dest="script",
                  default="",
                  help='The path to a local script to be uploaded and run on the target machine',
                 )
parser.add_option('-c', '--copyfiles',
                  dest="copyfiles",
                  default="",
                  help='Location of local files to copy to the target machine',
                 )
parser.add_option('-r', '--remotedir',
                  dest="remotedir",
                  default="/tmp/",
                  help='If -c or -s options are defined, this is where files will be placed on the target machine. Default is "/tmp/".',
                 )
parser.add_option('-d', '--debug',
                  dest="debug",
                  default=False,
                  action="store_true",
                  help='Show verbose logging',
                 )
parser.set_usage("""
python Pusher.py -u <user> -S <server/target> -s <script>

Example:
python Pusher.py -u admin -S Remote_Macbook_Pro -s /localfolder/install-script.sh
  -c /localfolder/config.txt -r /remotefolder/InstallDirectory

Pusher.py

Automate installs on remote systems via SSH

This script uploads files and runs custom scripts on a remote Mac or linux host via SSH.
You must select either (or both) of the '-s' and/or '-c' options. '-s' defines a script 
(on your local machine) to be uploaded and ran on the remote machine. '-c' defines any 
extra installation files that need to be uploaded such as a config file or a certificate. 
Note that the file(s) referenced in the -c option are uploaded before the script is run on
the remote machine, so an installer file can be uploaded via -c and then called via a 
simple script defined with -s. Both of these options will upload to the remote directory 
defined by the '-r' option. If no remote directory is specified, the script will upload to 
the default remote directory '/tmp/'.
""")
options, remainder = parser.parse_args()

# set variables defined in options menu
username = options.username
password = options.password
sshkey = options.sshkey
server = options.server
try:
  port = int(options.port)
except:
  print("[!] Invalid port")
  sys.exit()
admin = options.admin
script = options.script
# get the file name of the script from the full path
scriptfilename = script.rsplit('/')[-1]
copyfiles = options.copyfiles
remotedir = options.remotedir
# make sure that the remote directory ends with a '/'
if not remotedir.endswith('/'): remotedir += '/'
debug = options.debug


# make sure all the variables are configured correctly
if script == "" and copyfiles == "":
  print("[!] Please define a script to run with -s or files to copy with -c. Try -h for more options")
  sys.exit()
if debug and script != "": print("[-] Script file set to '%s'" % script)
if debug and copyfiles != "": print("[-] File(s) to upload set to '%s'" % copyfiles)
if server == "":
  server = raw_input('Enter target machine address: ')
  if server == "": sys.exit()
# check if SSH port is open on target
sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
result = sock.connect_ex((server,port))
if result != 0:
  print("[!] Port '%s' is not open on target machine '%s'" % (port, server))
  sys.exit()
if debug: print("[-] Target server set to '%s'" % server)
if username == "":
  username = raw_input('Enter SSH username: ')
  if username == "": sys.exit()
if debug: print("[-] Username set to '%s'" % username)
if sshkey == "":
  usekey = False
  if password == "":
    password = getpass.getpass('Enter password for %s@%s: ' % (username, server))
else:
  usekey = True
if debug and usekey: print("[-] SSH key set to '%s'" % sshkey)
if debug and not usekey: print("[-] SSH Password set")
if debug and admin: print("[-] Admin option set")

def sendcommand(sshshell, cmd, showoutput=False):
  if showoutput: print("\n[-] sending command: " + cmd)
  sshshell.sendall('\n' + cmd + '\necho CmdComplete\n')
  output = ""
  while True:
    sleep(0.1)
    output += sshshell.recv(65535)
    if "CmdComplete" in output:
      if showoutput:
        # remove color from output before displaying
        newoutput = output.replace('\033[', '')
        print("[-] Received output from remote host: \n" + '\033[93m' + newoutput.split('echo CmdComplete')[0] + '\033[0m' + "\n")
      break

def sendsudo(sshshell):
  sshshell.sendall('\nsudo -i\n')
  output = ""
  # try for 10 seconds then time out
  timeout = 10
  for i in range(timeout):
    if i == timeout:
      print("[!] Process timed out waiting for administrator password prompt")
      sys.exit()
    else:
      output += sshshell.recv(65535)
      if "Password:" in output:
        if debug: print("[-] Received password prompt")
        break
      sleep(1)
  if debug: print("[-] inputting password")
  sshshell.sendall(password + '\n')

  output = ""
  # try for 10 seconds then time out
  timeout = 10
  for i in range(timeout):
    if i == timeout:
      print("[!] Process timed out waiting for administrator login - does this user have sudo privileges?")
      sys.exit()
    else:
      output += sshshell.recv(65535)
      if 'root#' in output:
        if debug: print("[-] sudo command successful")
        break

# create SSH client
ssh = paramiko.SSHClient()
# auto-accept the "save new SSH key???" prompt
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())

# initiate SSH connection
try:
  if usekey:
    # Using SSH key
    ssh.connect(server, port=port, username=username, key_filename=sshkey, look_for_keys=False, allow_agent=False)
  else:
    # Using SSH password
    ssh.connect(server, port=port, username=username, password=password, look_for_keys=False, allow_agent=False)
  if debug: print("[-] Connected to '%s'" % server)
except paramiko.ssh_exception.AuthenticationException:
  print("[!] Username or password incorrect on '%s'" % server)
except paramiko.ssh_exception.NoValidConnectionsError:
  print("[!] Unable to initiate SSH connection to '%s' on port '%s'" % (server, port))

# initiate shell
try:
  sshshell = ssh.invoke_shell()
  sleep(0.5)
  sshshell.sendall("\n")
  sleep(0.1)
  print("[-] Successfully initiated SSH shell")
except:
  print("[!] Error initiating SSH shell")
  sys.exit()

# Create the destination directory if it does not already exist
if debug:
  print("[-] Creating remote directory if it does not already exist")
  sendcommand(sshshell, "mkdir -p " + remotedir, True)
else:
  sendcommand(sshshell, "mkdir -p " + remotedir)

# if the copyfiles variable is defined, copy the local files to the target directory
if copyfiles:
  # check if local files exist
  if not (os.path.isfile(copyfiles) or os.path.isdir(copyfiles)):
    print("[!] Could not find local files '%s'" % copyfiles)
    sys.exit()
  if debug: print("[-] copying files from '%s' on local machine to '%s' on '%s'" % (copyfiles, remotedir, server))
  scpclient = SCPClient(ssh.get_transport())
  try:
    scpclient.put(copyfiles, remotedir)
    if debug: print("[-] copied files from '%s' to %s:'%s' with no error" % (copyfiles, server, remotedir))
  except:
    print("[!] Error copying localhost:'%s' to %s:'%s'" % (copyfiles, server, remotedir))
    sys.exit()


# if a script is provided, run upload & run it on the target machine
if script:

  # First, copy the script to the remote machine

  # check if the script exists on the local machine
  if not (os.path.isfile(script) or os.path.isdir(script)):
    print("[!] Could not find script at '%s'" % script)
    sys.exit()
  if debug: print("[-] copying script from '%s' on local machine to '%s' on '%s'" % (script, remotedir, server))
  scpclient = SCPClient(ssh.get_transport())
  try:
    scpclient.put(script, remotedir)
    if debug: print("[-] copied script from '%s' to %s:'%s' with no error" % (script, server, remotedir))
  except:
    print("[!] Error copying localhost:'%s' to %s:'%s'" % (script, server, remotedir))
    raise
    sys.exit()

  # Now, execute the script on the remote machine
  if admin:
    if debug: print("[-] Attempting sudo command")
    sendsudo(sshshell)
  if debug:
    print("[-] Enabling execute permission on remote script")
    sendcommand(sshshell, 'chmod +x ' + remotedir + scriptfilename + '\n', True)
  else:
    sendcommand(sshshell, 'chmod +x ' + remotedir + scriptfilename + '\n')
  sleep(0.1)
  print("[-] Executing script on remote host")
  sendcommand(sshshell, remotedir + scriptfilename + '\n', True)

print("[-] Done\n")





