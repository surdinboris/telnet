import serial
import time
import telnetlib
import tkinter as tk
import tkinter.scrolledtext as tkst
from tkinter import *
import os
import re
from serial.serialutil import SerialException
######Config file parsing part##############
#apctk config file
#system types format sysname, output groups: pdu1,pdu2; pdu1,pdu2,pdu3,pdu4; ....
#system  step-by-step will turn off and turn on every group per declared order with delay
#parameter shoulb be entered from beginning of the row, else it will be ignored
# delay:5
# #System list
# <f1000_1ph_2> output groups:12,13; 17,18; 19,20;
# <f1000_3ph_2> output groups:12,13; 17,18; 19,20;
# <f2000_1ph_2> output groups:12,13; 17,18; 19,20;
# <f2000_3ph_2> output groups:12,13; 17,18; 19,20;
# <f4000_1ph_4> output groups:12,13; 17, 18,18,16;  19,20, 17,20;
# <f4000_3ph_2> output groups:12,13; 17,18; 19,20;
# <f6000_1ph_4> output groups:12,13; 17,18; 19,20;
# <f6000_3ph_4> output groups:12,13; 17,18; 19,20;

def confparse():
    conf=open(os.path.join(os.getcwd(),'apctk.conf'), 'r')
    syspatterns = {}
    delay=''
    for row in conf.readlines():
        if re.search(r"^delay:(\d{1,})",row): #delay
            delay = re.search(r".*delay:(\d{1,})",row)[1]
        else: #regular row
            confrow=re.search(r"^<(.*)>.*output groups:(.*)",row)
            if confrow:
                sysname=confrow[1]
                groupstr=confrow[2].replace(" ", "").replace("\t", "")
                groups=groupstr.rstrip(';').split(";")
                syspatterns[sysname]=groups

    return(delay,syspatterns)

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
        self.delay,self.syspatterns=confparse()
        self._root = Tk()
        self.syst=IntVar()
        self.syst.set(0)
        self._root.title('LED test config\control tool')
        self._root.resizable(width=False,height=False)
        #main window
        self._mainframe = tk.Frame(self._root)
        self._mainframe.grid(row=0, column=0, sticky=(E, W, N, S))
        #config part
        self._configframe=tk.LabelFrame(self._mainframe, text='Config')
        self._configframe.grid(row=0, padx=5, pady=5, column=0, sticky=(W,N))
        self._configframe.columnconfigure(0, weight=1)
        self._configframe.rowconfigure(0, weight=1)

        #output part
        self._textboxframe=tk.LabelFrame(self._mainframe, text='Work log')
        self._textboxframe.grid(row=0,padx=5, pady=5, column=1, rowspan=2, sticky=(W,N))
        self._textboxframe.columnconfigure(0, weight=1)
        self._textboxframe.rowconfigure(0, weight=1)
        self._texbox = tkst.ScrolledText(self._textboxframe,wrap='word', width=45, height=25, state='disabled')
        self._texbox.grid(row=0, column=1, sticky=(W,N))

        #config buttons
        self._pdu1conf_btn=tk.Button(self._configframe,text='PDU-1', command=lambda: self.pduconf(1))
        self._pdu1conf_btn.grid(row=0,padx=3, pady=3, column=1, sticky=W)
        self._pdu2conf_btn=tk.Button(self._configframe,text='PDU-2', command=lambda: self.pduconf(2))
        self._pdu2conf_btn.grid(row=0,padx=3, pady=3, column=2, sticky=W)
        self._pdu3conf_btn=tk.Button(self._configframe,text='PDU-3', command=lambda: self.pduconf(3))
        self._pdu3conf_btn.grid(row=1,padx=3, pady=3,  column=1, sticky=W)
        self._pdu4conf_btn=tk.Button(self._configframe,text='PDU-4', command=lambda: self.pduconf(4))
        self._pdu4conf_btn.grid(row=1,padx=3, pady=3,  column=2, sticky=W)
        #testing part
        self._testingframe=tk.LabelFrame(self._mainframe, text='Testing')
        self._testingframe.grid(row=1, padx=5, pady=5, column=0,sticky=(W,N))
        self._testingframe.columnconfigure(0, weight=1)
        self._testingframe.rowconfigure(0, weight=1)
        #radio buttons - system selection
        for self.ind,self.syspattern in enumerate(self.syspatterns):
            self._radiobutton = tk.Radiobutton(self._testingframe, text=self.syspattern, variable=self.syst, value=self.ind)
            self._radiobutton.grid(row=self.ind,  padx=3, pady=3, column=0,sticky=(W,N))
        #test buttons - start stop test
        self._startbutton=tk.Button(self._testingframe, text='Start testing', command=self.starttest)
        self._startbutton.grid(row=self.ind+1,  padx=3, pady=3, column=0,sticky=(W,N))
        self.print_to_gui("Please configure PDU's via Serial cable (RJ-11), choose proper system type and run testing procedure.")
        self._root.mainloop()

    def starttest(self):
        self._startbutton.config(text='Stop testing')
        print(list(self.syspatterns.values())[self.syst.get()])
        #need to pass outlet values to pdu's and print feedback to operator

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
        self._texbox.config(state='normal')
        self._texbox.insert('end', '%s\n' %txtstr)
        self._texbox.config(state="disabled")
        self._root.update()
gui=ApcGui()


