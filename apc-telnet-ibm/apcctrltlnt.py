import telnetlib
import time
host='192.168.1.254'
user='admn'
password='admn'
tel=telnetlib.Telnet(host)

def sendcom(cmd=b""):
    print(cmd)
    tel.write(cmd)
    tel.write(bytes("\r", encoding='ascii'))


def login():
    for e in range(2):
        sendcom(cmd=b"")
    tel.read_until(b"Username:")
    sendcom(b"admn")
    tel.read_until(b"Password:")
    sendcom(b'admn')
    tel.read_until(b"Switched CDU:")

def command(cmdlist):
    login()
    for cmd in cmdlist:
        print(cmd.encode())
        sendcom(cmd.encode())


    sendcom(b'exit')

if __name__ == "__main__":
    cmdlist=[]
    for num in range(13,17):
        onoff='OFF '
        outlname='Master_'
        cmdlist.append(''.join([onoff,outlname,str(num)]))
    print(cmdlist)
    command(cmdlist)
        #print(''.join([onoff,outlname,str(num)]))