# Pusher

Push files and run scripts on remote machines

This script automates the process of pushing files and/or running custom scripts on a remote machine. The script communicates with remote machines over SSH and is compatible with remote machines running *nix-style operating systems (including Mac / OS X).


# Background

Recently given the task of pushing out installs to a number of networked Macs, I wrote this script as a way of automating and simplifying the process. The install required that a zip file consisting of an installer, a certificate, and a configuration file was uploaded to a specific directory on a target machine. Then, the zip file was to be unzipped and the installer script ran with administrator (root) privileges. While this was possible to accomplish manually, it seemed like a good opportunity to automate the process.


# Features

- Use an SSH password or an SSH private key
- Define a custom SSH port
- Use the '-a' option to run as root
- Choose a directory on the remote machine to place files (the script will try to create the directory if it is not already there)
- Choose between uploading and running a custom script ('-s' option) or just upload files with the '-c' option



# Help Menu

```
bash# ./Pusher.py -h

Usage: 
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


Options:
  -h, --help            show this help message and exit
  -u USERNAME, --username=USERNAME
                        SSH username
  -p PASSWORD, --pass=PASSWORD
                        SSH password (leave blank to be prompted)
  -k SSHKEY, --key=SSHKEY
                        SSH private key location (ex. /home/user/.ssh/id_rsa)
  -S SERVER, --server=SERVER
                        SSH server address (target machine)
  -P PORT, --port=PORT  SSH port (default is 22)
  -a, --admin           Set this option to run as an administrator (runs "sudo
                        -i" before executing commands)
  -s SCRIPT, --script=SCRIPT
                        The path to a local script to be uploaded and run on
                        the target machine
  -c COPYFILES, --copyfiles=COPYFILES
                        Location of local files to copy to the target machine
  -r REMOTEDIR, --remotedir=REMOTEDIR
                        If -c or -s options are defined, this is where files
                        will be placed on the target machine. Default is
                        "/tmp/".
  -d, --debug           Show verbose logging

```
