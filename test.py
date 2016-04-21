import paramiko

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('dev-uportal1.usd.edu',username='Toben.Archer',password=
