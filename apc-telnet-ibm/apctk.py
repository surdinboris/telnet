#!/usr/bin/env python3.6
import serial
import time
import telnetlib
import tkinter as tk
import tkinter.scrolledtext as tkst
from tkinter import *
import os
import re
from tkinter import messagebox
# import threading
# from queue import Queue
ver="1.1"
import datetime
from serial.serialutil import SerialException
######Config file parsing part##############
def confparse():
    conf=open(os.path.join(os.path.dirname(os.path.abspath(__file__)),'apctk.conf'), 'r')
    syspatterns = {}
    delay=''
    comport=''
    ipaddr=''
    for row in conf.readlines():
        if re.search(r"^delay:(\d{1,})",row): #delay
            delay = re.search(r"^delay:(\d{1,})",row)[1]
        elif re.search(r"^comport:(.*\d)", row):  # delay
            comport = re.search(r"^comport:(.*\d)", row)[1] #comport
        elif re.search(r"^ipaddr:(.*\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})", row):
            ipaddr =(re.search(r"^ipaddr:(.*\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})", row)[1])

        else: #regular row
            confrow=re.search(r"^<(.*)>.*output groups:(.*)",row)
            if confrow:
                sysname="<"+confrow[1]+">"
                groupstr=confrow[2].replace(" ", "").replace("\t", "")
                groups=groupstr.rstrip(';').split(";")
                syspatterns[sysname]=groups

    return(comport,delay,syspatterns,ipaddr)

######Serial part##############
def crconn(comport):
    ser = serial.Serial(
        comport,
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
    attcount=0
    while len(promt) == 0 and attcount < 4: # activating new session
        attcount+=1
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

def command(comport,comm,type):
    print('Got command {} of type {}'.format(comm, type))
    ser=crconn(comport)
    if type == 'config':
        handler(ser,[comm,'reboot','YES'])
    elif type == 'action':
        handler(ser, [comm])
    else:  # unexpected login prompt state
        raise BaseException(ConnectionError)
    print('Closing session.')
    ser.close()
    return True

def getver(comport): #returns aos version
    ser=crconn(comport)
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
def texecute(host, outl, act):  # patterns generation & execution. delay in sec, act - On, Off
    print(host,outl,act)
    tel = telnetlib.Telnet(host)
    tel.read_until(b'User Name')
    sendtel(tel,b'apc')
    tel.read_until(b'Password  :')
    sendtel(tel,b'apc')
    if type(outl) == str:
        sendtel(tel, ("ol%s %s" % (act,outl)).encode())
        if tel.read_until(b'E000:'):
            print('command passed')
        else:
            raise BaseException(ConnectionRefusedError)
    if type(outl) == list:
        out=','.join(outl)
        sendtel(tel, ("ol%s %s" % (act, out)).encode())
        if tel.read_until(b'E000:'):
            print('command list passed')
        else:
            raise BaseException(ConnectionRefusedError)
    sendtel(tel,b'exit')

def sendtel(tel,tcmd):
    tel.write(tcmd)
    time.sleep(0.5)
    tel.write(b'\r')


######GUI part##############
class ApcGui():
    def __init__(self):
        # Configuration parsing - building menu items and testing delay
        self.comport,self.delay,self.syspatterns,self.ipaddr=confparse()
        self._root = Tk()
        self.syst=IntVar()  #Radiobutton default value
        self.syst.set(0)    #Radiobutton default value
        self.testrun = True #Test interrupt var
        #images loading
        self.logo = tk.PhotoImage(file=os.path.join(os.path.dirname(os.path.abspath(__file__)),"logo.gif"))
        #geometry
        #fixed width
        self._root.title('APC PDU control tool')
        self._root.resizable(width=False,height=False)
        #fixed fullscreen
        # self._root.overrideredirect(True)
        # self._root.overrideredirect(False)
        # self._root.attributes('-fullscreen', True)
        #main window
        self._mainframe = tk.Frame(self._root)
        self._mainframe.grid(row=0, column=0, sticky=(E, W, N, S))
        #image
        self._logo = tk.Label(self._mainframe,image=self.logo)
        self._logo.grid(row=0, padx=5, pady=5, column=0, sticky=(W,N))
        #output part
        self._textboxframe=tk.LabelFrame(self._mainframe, text='Work log')
        self._textboxframe.grid(row=0,padx=5, pady=5, column=1, rowspan=3, sticky=(W,N))
        self._textboxframe.columnconfigure(0, weight=1)
        self._textboxframe.rowconfigure(0, weight=1)
        self._texbox = tkst.ScrolledText(self._textboxframe,wrap='word', width=39, height=25, state='disabled')
        self._texbox.grid(row=0, column=1, sticky=(W,N))

        #testing part
        self._testingframe=tk.LabelFrame(self._mainframe, text='Testing')
        self._testingframe.grid(row=1, padx=5, pady=5, column=0,sticky=W)
        self._testingframe.columnconfigure(0, weight=1)
        self._testingframe.rowconfigure(0, weight=1)
        #radio buttons - system selection
        self._radiobuttons=[] #array for further manipulations
        for self.ind,self.syspattern in enumerate(self.syspatterns):
            self._radiobutton = tk.Radiobutton(self._testingframe, text=self.syspattern, variable=self.syst, value=self.ind)
            self._radiobutton.grid(row=self.ind,  padx=1, pady=1, column=0,sticky=(W,N))
            self._radiobuttons.append(self._radiobutton)
        self.print_to_gui("PDU control tool ver.{}".format(ver))

        #user entry
        self._userframe=tk.LabelFrame(self._testingframe, text='Execution')
        self._userframe.grid(row=self.ind+1,  padx=1, pady=1, column=0,sticky=(W,N))
        # test buttons - start stop test
        self._startbutton=tk.Button(self._userframe, text='Turn ON', command=self.turnOn)
        self._startbutton.grid(row=self.ind+3,  padx=3, pady=3, column=0,sticky=(W,N))
        self._stopbutton = tk.Button(self._userframe, text='Turn OFF', command=self.turnOff)
        self._stopbutton.grid(row=self.ind + 3, padx=3, pady=3, column=1, sticky=(W, N))
        # self.print_to_gui("Please configure PDU's via Serial cable (RJ-11), choose proper system type and run testing procedure.")
        self._root.mainloop()
    def disbutt(self,opt):
        for self.bu in self._radiobuttons:
            self.bu['state'] = opt
    def turnOn(self,):
        # print(self.curbuttnames)
        self.testrun = True
        self.disbutt('disabled')
        # self._startbutton.config(text='Stop testing', command=self.stoptest)
        self.pattrns=(list(self.syspatterns.values())[self.syst.get()]) #get command scenarios for each pdu
        # self.texboxclear()
        self.print_to_gui('{} {} turned On'.format(datetime.datetime.now().strftime('%d/%m %H:%M:%S')
                                                        ,list(self.syspatterns)[self.syst.get()]))
        #Generating pattern per PDU for faster operation
        self.pttrnlist = self.pattrns[0].split(',')
        for self.toutl in self.pttrnlist:  #outlets iteration
            #sending command to each pdu
            if self.toutl and self.toutl != '0':
                texecute(self.ipaddr, self.toutl,'On') #need to implement command generation accordingly to a pressed button +update GUI field
        #updating menu entries

        for self.but in self._radiobuttons:
            self.filteredButtName = re.search(r'(\<.*\>)', self.but["text"])
            if self.filteredButtName.group(0) == list(self.syspatterns)[self.syst.get()]:
                self.but.config(text=list(self.syspatterns)[self.syst.get()] + " is On")
                self._root.update()
        self.disbutt('normal')

    def turnOff(self,):
        global testrun
        self.testrun = True
        self.disbutt('disabled')
        # self._startbutton.config(text='Stop testing', command=self.stoptest)
        self.pattrns=(list(self.syspatterns.values())[self.syst.get()]) #get command scenarios for each pdu
        # self.texboxclear()
        self.print_to_gui('{} {} turned Off'.format(datetime.datetime.now().strftime('%H:%M:%S')
                                                        ,list(self.syspatterns)[self.syst.get()]))
        #Generating pattern per PDU for faster operation
        self.pttrnlist=self.pattrns[0].split(',')
        for self.toutl in self.pttrnlist: #outlets iteration
            #sending command to each pdu
            if self.toutl and self.toutl != '0':
                texecute(self.ipaddr, self.toutl,'Off') #need to implement command generation accordingly to a pressed button +update GUI field

        for self.but in self._radiobuttons:
            self.filteredButtName = re.search(r'(\<.*\>)', self.but["text"])
            if self.filteredButtName.group(0) == list(self.syspatterns)[self.syst.get()]:
                self.but.config(text=list(self.syspatterns)[self.syst.get()] + " is Off")
                self._root.update()
        self.disbutt('normal')

    def combine_funcs(self,*funcs): #combining functions for one button execution binding
        def combined_func(*args, **kwargs):
            for f in funcs:
                f(*args, **kwargs)
        return combined_func


    def ignore(self,*args,**kwargs):
        return 'break'
    def logging(self, txtstr, sysname ): #creating logfile
        self.syslog = open(os.path.join(os.path.dirname(os.path.abspath(__file__)),'logs', '{0}_{1}'.format(sysname, datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S"))+'.log'), 'w')
        self.syslog.writelines(txtstr)
        self.syslog.close()

    def print_to_gui(self, txtstr):
        self._texbox.config(state='normal')
        self._texbox.insert('end', '%s\n' %txtstr)
        self._texbox.config(state="disabled")
        self._texbox.see('end')
        self._root.update()
    def texboxclear(self):
        self._texbox.config(state='normal')
        self._texbox.delete('1.0', END)
        self._texbox.config(state="disabled")
        self._root.update()
ApcGui()
