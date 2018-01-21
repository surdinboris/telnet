import serial
import time
import telnetlib
import tkinter as tk
import tkinter.scrolledtext as tkst
from tkinter import *
import os
import re
######Config file parsing part##############
conf=open(os.path.join(os.getcwd(),'apctk.conf'), 'r')
sysentry = {}
for row in conf.readlines():
    if re.search(r"^delay:(\d{1,})",row): #delay parameter
        delay = re.search(r".*delay:(\d{1,})",row)[1]
        print('found delay %s' %delay)
    else: #regular row
        confrow=re.search(r"^<(.*)>.*output groups:(.*)",row)
        if confrow:
            sysname=confrow[1]
            groupstr=confrow[2].replace(" ", "").replace("\t", "")
            groups=groupstr.rstrip(';').split(";")
            sysentry[sysname]=groups
for i in sysentry.items():
    print(i)

######Serial part##############
def crconn():
    ser = serial.Serial(
        'COM5',
        timeout=3,
        baudrate=9600,
        xonxoff=0,
        stopbits=1,
        parity=serial.PARITY_NONE,
        bytesize=8)
    return(ser)

def sendcom(ser,cmd):
    print('Passing command %s'% cmd)
    ser.write(cmd.encode())
    ser.write(bytes("\r", encoding='ascii'))
    time.sleep(2)

def handler(ser,comm): #login/accept handler
    promt=ser.readlines()
    while len(promt) == 0: # activating new session
        print('Trying to bring up serial connection...')
        conn_init(ser)
        promt=ser.readlines()
    if promt[-1] == b'User Name : ': #login prompt - login procedure execution
        print('Logging in...')
        sendcom(ser,'apc')
        ser.read_until(b'Password : ')
        sendcom(ser,'apc')
        ser.read_until(b'apc>')
        for c in comm:
            sendcom(ser,c)
    elif promt[-1] == b'apc>': #already logged in - not need to enter
        print('Already logged in...')
        for c in comm:
            sendcom(ser, c)
    else: #unexpected login prompt state
        raise BaseException(SyntaxError)

def conn_init(ser): #initiation procedure for console - need to send enter two  or more times fastly
    for x in range(3):
        ser.write(bytes("\r", encoding='ascii'))

def command(comm,type):
    print('Got command {} of type {}'.format(comm, type))
    ser=crconn()
    if type == 'config':
        handler(ser,[comm,'reboot','YES'])
    elif type == 'action':
        handler(ser, [comm])
    else:  # unexpected login prompt state
        raise BaseException(ConnectionError)
    print('Closing session.')
    ser.close()
    return True

def print_to_gui(txtstr):
    gui._texbox.config(state="normal")
    gui._texbox.insert('end', txtstr)
    gui._texbox.config(state="disabled")
    gui._root.update()

def getver(): #returns aos version
    ser=crconn()
    handler(ser,['about'])
    ser.read_until(b"aos")
    ser.read_until(b"v")
    ver=ser.readlines()
    return ver[0].decode('ascii')

# usage:
#print(getver())
# command("lcdBlink id#:1 1", 'action')
#command("olReboot all", 'action')
# command("tcpip -S enable -i 192.168.0.159 -s 255.255.255.0 -g 0.0.0.0 -h pdu-7", 'config')

######Telnet part##############
def texecute(systype, host):  # patterns generation & execution
    tel = telnetlib.Telnet('9.151.140.15{}'.format(host))
    tel.read_until(b'User Name')
    sendtel(tel,b'apc')
    tel.read_until(b'Password  :')
    sendtel(tel,b'apc')

    if systype == 'f2_3ph':
        #cmdlist=['olReboot all']
        cmdlist =[]
        # for num in range(13, 17):
        #     onoff = 'OFF '
        #     outlname = 'Master_'
        #     cmdlist.append(''.join([onoff, outlname, str(num)]))
        # print(cmdlist)
        commtel(tel,cmdlist)

def sendtel(tel,tcmd):
    tel.write(tcmd)
    time.sleep(1)
    tel.write(b'\r')
    time.sleep(1)

def commtel(tel,cmdlist):
    for tcmd in cmdlist:
        print(tcmd.encode())
        sendtel(tel,tcmd.encode())
    sendtel(tel,b'exit')

texecute('f2_3ph', 1)

######GUI part##############
class ApcGui():

    def __init__(self):
        self.run = True
        self._root = Tk()
        self._root.title('LED test config\control tool')
        self._root.resizable(width=False,height=False)
        #main window
        self._mainframe = tk.Frame(self._root)
        self._mainframe.grid(row=0, column=0, sticky=(E, W, N, S))
        #output part
        self._textboxframe=tk.LabelFrame(self._mainframe, text='Work log')
        self._textboxframe.grid(row=0, column=1, sticky=(W,N))
        self._textboxframe.columnconfigure(0, weight=1)
        self._textboxframe.rowconfigure(0, weight=1)
        self._texbox = tkst.ScrolledText(self._textboxframe,wrap='word', width=45, height=10, state='disabled')
        self._texbox.grid(row=0, column=0, sticky=W, padx=5)
        #config part
        self._configframe=tk.LabelFrame(self._mainframe, text='Config')
        self._configframe.grid(row=0, column=0, sticky=(W,N))
        self._configframe.columnconfigure(0, weight=1)
        self._configframe.rowconfigure(0, weight=1)
        #config buttons
        self._pdu1conf_btn=tk.Button(self._configframe,text='PDU-1', command=lambda: self.pduconf(1))
        self._pdu1conf_btn.grid(row=0, column=1, sticky=W, padx=5)
        self._pdu2conf_btn=tk.Button(self._configframe,text='PDU-2', command=lambda: self.pduconf(2))
        self._pdu2conf_btn.grid(row=0, column=2, sticky=W, padx=5)
        self._pdu3conf_btn=tk.Button(self._configframe,text='PDU-3', command=lambda: self.pduconf(3))
        self._pdu3conf_btn.grid(row=1, column=1, sticky=W, padx=5)
        self._pdu4conf_btn=tk.Button(self._configframe,text='PDU-4', command=lambda: self.pduconf(4))
        self._pdu4conf_btn.grid(row=1, column=2, sticky=W, padx=5)
        #radio buttons - system selection

        self._root.mainloop()


    def pduconf(self,pdunum):
            self.butts = [self._pdu1conf_btn, self._pdu2conf_btn, self._pdu3conf_btn, self._pdu4conf_btn]
            for butt in self.butts:
                butt.config(state='disabled')
            self.print_to_gui('PDU-{} config started\n'.format(pdunum))
            self.pduconfbu=self.pduconf
            self.pduconf=self.ignore
            self._root.update()
            command("tcpip -S enable -i 9.151.140.15{} -s 255.255.255.0 -g 0.0.0.0 -h pdu-{}".format(pdunum,pdunum), 'config')

            for butt in self.butts:
                butt.config(state='active')
            self._root.after(2000, self.bindit)


    def bindit(self):
        for butt in self.butts:
            butt.config(state='active')
        self.pduconf=self.pduconfbu

    def ignore(self,*args,**kwargs):
        return 'break'

    def print_to_gui(self, txtstr):
        self._texbox.config(state="normal")
        self._texbox.insert('end', txtstr)
        self._texbox.config(state="disabled")
        self._root.update()
gui=ApcGui()


