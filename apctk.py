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

import datetime
from serial.serialutil import SerialException
######Config file parsing part##############
def confparse():
    conf=open(os.path.join(os.path.dirname(os.path.abspath(__file__)),'apctk.conf'), 'r')
    syspatterns = {}
    delay=''
    comport=''
    for row in conf.readlines():
        if re.search(r"^delay:(\d{1,})",row): #delay
            delay = re.search(r"^delay:(\d{1,})",row)[1]
        elif re.search(r"^comport:(.*\d)", row):  # delay
            comport = re.search(r"^comport:(.*\d)", row)[1] #comport
        else: #regular row
            confrow=re.search(r"^<(.*)>.*output groups:(.*)",row)
            if confrow:
                sysname=confrow[1]
                groupstr=confrow[2].replace(" ", "").replace("\t", "")
                groups=groupstr.rstrip(';').split(";")
                syspatterns[sysname]=groups
    return(comport,delay,syspatterns)

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
    tel = telnetlib.Telnet('9.151.140.15{}'.format(host))
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

# class ThreadedSleep(threading.Thread):
#     def __init__(self, queue):
#         print('ThreadedSleep ')
#         threading.Thread.__init__(self)
#         self.queue = queue
#         #self.delay=delay
#     def run(self):
#         time.sleep(50)  # Simulate long running process
#         self.queue.put("Task finished")

######GUI part##############
class ApcGui():
    def __init__(self):

        self.comport,self.delay,self.syspatterns=confparse() #Configuration parsing - building menu items and testing delay
        self._root = Tk()

        self.syst=IntVar()  #Radiobutton default value
        self.syst.set(0)    #Radiobutton default value
        self.testrun = True #Test interrupt var
        #images loading
        self.logo = tk.PhotoImage(file=os.path.join(os.path.dirname(os.path.abspath(__file__)),"logo.gif"))
        self.encnormfr = tk.PhotoImage(file=os.path.join(os.path.dirname(os.path.abspath(__file__)), "encnormfr.gif"))
        self.encopenedfr = tk.PhotoImage(file=os.path.join(os.path.dirname(os.path.abspath(__file__)), "encopenedfr.gif"))
        #geometry
        #fixed width
        self._root.title('LED test config/control tool')
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
        #config part
        self._configframe=tk.LabelFrame(self._mainframe, text='Config')
        self._configframe.grid(row=1, padx=15, pady=5, column=0, sticky=(W,N))
        self._configframe.columnconfigure(0, weight=1)
        self._configframe.rowconfigure(0, weight=1)
        #output part
        self._textboxframe=tk.LabelFrame(self._mainframe, text='Work log')
        self._textboxframe.grid(row=0,padx=5, pady=5, column=1, rowspan=3, sticky=(W,N))
        self._textboxframe.columnconfigure(0, weight=1)
        self._textboxframe.rowconfigure(0, weight=1)
        self._texbox = tkst.ScrolledText(self._textboxframe,wrap='word', width=45, height=25, state='disabled')
        self._texbox.grid(row=0, column=1, sticky=(W,N))
        #config buttons
        self._pdu1conf_btn=tk.Button(self._configframe,text='PDU-1', command=lambda: self.pduconf(1))
        self._pdu1conf_btn.grid(row=0,padx=15, pady=3, column=1, sticky=W)
        self._pdu3conf_btn = tk.Button(self._configframe, text='PDU-3', command=lambda: self.pduconf(3))
        self._pdu3conf_btn.grid(row=0, padx=15, pady=3, column=2, sticky=W)
        self._pdu2conf_btn=tk.Button(self._configframe,text='PDU-2', command=lambda: self.pduconf(2))
        self._pdu2conf_btn.grid(row=1,padx=15, pady=3, column=1, sticky=W)
        self._pdu4conf_btn=tk.Button(self._configframe,text='PDU-4', command=lambda: self.pduconf(4))
        self._pdu4conf_btn.grid(row=1,padx=15, pady=3,  column=2, sticky=W)
        #testing part
        self._testingframe=tk.LabelFrame(self._mainframe, text='Testing')
        self._testingframe.grid(row=2, padx=5, pady=5, column=0,sticky=(W,N))
        self._testingframe.columnconfigure(0, weight=1)
        self._testingframe.rowconfigure(0, weight=1)
        #radio buttons - system selection
        for self.ind,self.syspattern in enumerate(self.syspatterns):
            self._radiobutton = tk.Radiobutton(self._testingframe, text=self.syspattern, variable=self.syst, value=self.ind)
            self._radiobutton.grid(row=self.ind,  padx=1, pady=1, column=0,sticky=(W,N))
        #user entry
        self._userframe=tk.LabelFrame(self._testingframe, text='Execution')
        self._userframe.grid(row=self.ind+1,  padx=1, pady=1, column=0,sticky=(W,N))
        self._sysseriallbl = tk.Label(self._userframe, text='System SN:',width=10)
        self._sysseriallbl.grid(row=0 , padx=1, pady=1, column=0, sticky=(W, N))
        self._sysserial = tk.Entry(self._userframe,width=12)
        self._sysserial.grid(row=0, padx=1, pady=1, column=1, sticky=(W, N))
        self._unamelbl = tk.Label(self._userframe, text='User name:',width=10)
        self._unamelbl.grid(row=1, padx=1, pady=1, column=0, sticky=(W, N))
        self._uname=tk.Entry(self._userframe,width=12)
        self._uname.grid(row=1,  padx=1, pady=1, column=1,sticky=(W,N))
        # test buttons - start stop test
        self._startbutton=tk.Button(self._userframe, text='Start testing', command=self.starttest)
        self._startbutton.grid(row=self.ind+3,  padx=3, pady=3, column=0,sticky=(W,N))
        self.print_to_gui("Please configure PDU's via Serial cable (RJ-11), choose proper system type and run testing procedure.")
        self._root.mainloop()

    def starttest(self):
        global testrun
        self.testrun = True
        self._startbutton.config(text='Stop testing', command=self.stoptest)
        self.pattrns=(list(self.syspatterns.values())[self.syst.get()]) #get command scenarios for each pdu
        self.print_to_gui('Started test of %s' % list(self.syspatterns)[self.syst.get()])
        #Generating pattern per PDU for faster operation
        self.pttrnlist=[(self.itm.split(',')) for self.itm in self.pattrns]
        self.allencloper('Off')
    #Testing procedure - every enclosure will be turned on and off
        for self.enc,self.pattern in enumerate(self.pttrnlist,1): #enclosures iteration
            if self.testrun == True:
                self.print_to_gui('Turning on enclosure %s' %self.enc)
                for self.tpdu, self.toutl in enumerate(self.pattern,1): #pdu iteration
                    #sending command to each pdu
                    if self.toutl != '0':
                        if self.testrun == True:
                            texecute(self.tpdu, self.toutl,'On')
                        else:
                            break #stop button pressed
                self.popupgen(self.enc,'front panel of enclosure',self.encnormfr)
                if self.testrun == True: #checking for first abort
                    self.popupgen(self.enc, 'front panel of enclosure', self.encopenedfr)
                #time.sleep(int(self.delay)) #pdu iteration
                for self.tpdu, self.toutl in enumerate(self.pattern,1): #pdu iteration
                    #sending command to each pdu
                    if self.toutl != '0':
                        if self.testrun == True:
                            texecute(self.tpdu, self.toutl,'Off')
                        else:
                            break #stop button pressed
            else:
                break #stop button pressed
        self.allencloper('On')
        self._startbutton.config(text='Start testing', command=self.starttest)
        self.print_to_gui('Test is done.')


    def startreartest(self): #one-by-one PSU for each enc with target delay
        global testrun
        self.testrun = True
        self._startbutton.config(text='Stop testing', command=self.stoptest)
        self.pattrns = (list(self.syspatterns.values())[self.syst.get()])  # get command scenarios for each pdu
        self.print_to_gui('Started rear test of %s' % list(self.syspatterns)[self.syst.get()])
        # Generating pattern per PDU for faster operation
        self.pttrnlist = [(self.itm.split(',')) for self.itm in self.pattrns]
        self.allencloper('Off')
        for self.enc, self.pattern in enumerate(self.pttrnlist, 1):  # enclosures iteration
            if self.testrun == True:
                self.print_to_gui('Turning on enclosure %s' % self.enc)
                for self.tpdu, self.toutl in enumerate(self.pattern, 1):
                    # sending command to each pdu
                    if self.toutl != '0':
                        if self.testrun == True:
                            texecute(self.tpdu, self.toutl, 'On')
                            self.popupgen(self.enc, 'rear enclosure test')
                            texecute(self.tpdu, self.toutl, 'Off')
                        else:
                            break  # stop button pressed
            else:
                break  # stop button pressed
        self.allencloper('On')
        self._startbutton.config(text='Start testing', command=self.starttest)
        self.print_to_gui('Test is done.')

    def popupgen(self, testype, encnum, img):
        self._top = Toplevel()
        self._top.title("Please check {0} {1}".format(encnum,testype))
        self._top.resizable(width=False, height=False)
        self._messageframe = tk.LabelFrame(self._top, text='Picture')
        self._messageframe.grid(row=0, column=0, sticky=(E, W, N, S))
        self._frontmboxlogo = tk.Label(self._messageframe, image=img)
        self._frontmboxlogo.grid(row=0, padx=5, pady=5, column=0, sticky=(W, N))
        self._buttonsframe = tk.LabelFrame(self._top)
        self._buttonsframe.grid(row=1, column=0, sticky=(E, W, N, S))
        self._tpok = Button(self._buttonsframe, text="Ok", command=self._top.destroy)
        self._tpok.grid(row=1, padx=5, pady=5, column=0, sticky=(W, N))
        self._tpcancel = Button(self._buttonsframe, text="Abort testing",
                                command=self.combine_funcs(self.stoptest, self._top.destroy))
        self._tpcancel.grid(row=1, padx=5, pady=5, column=1, sticky=(W, N))
        self._top.grab_set()
        self._root.wait_window(self._top)

    def allencloper(self,comm):   #serial enclosure outlet operation at beginning and ending test
        self.print_to_gui(
            'Turning %s all enclosures...' %comm)
        self.perpdu=[self.z for self.z in zip(*self.pttrnlist)]
        for self.pdu,self.itm in enumerate(self.perpdu,1):
            self.outl=[x for x in filter(lambda x: x != '0',self.itm)] #collecting only involved outlets
            if len(self.outl) > 0:
                texecute(self.pdu, self.outl,comm)

    def combine_funcs(self,*funcs):
        def combined_func(*args, **kwargs):
            for f in funcs:
                f(*args, **kwargs)

        return combined_func

    def stoptest(self):
        self.testrun=False
        self.print_to_gui('Test was interrupted.')
        self._root.after(2000, self._startbutton.config(text='Start testing', command=self.starttest))
    def pduconf(self,pdunum):
            self.butts = [self._pdu1conf_btn, self._pdu2conf_btn, self._pdu3conf_btn, self._pdu4conf_btn]
            for self.butt in self.butts:
                self.butt.config(state='disabled')
            self.print_to_gui('PDU-{} config started'.format(pdunum))
            self.pduconfbu=self.pduconf
            self.pduconf=self.ignore
            self._root.update()
            command(self.comport,"tcpip -S enable -i 9.151.140.15{} -s 255.255.255.0 -g 0.0.0.0 -h pdu-{}".format(pdunum,pdunum), 'config')
            for self.butt in self.butts:
                self.butt.config(state='active')
            self.print_to_gui('PDU-{} config finished'.format(pdunum))
            self._root.after(2000, self.bindit)
    def bindit(self):
        for butt in self.butts:
            butt.config(state='active')
        self.pduconf=self.pduconfbu
    def ignore(self,*args,**kwargs):
        return 'break'
    def logging(self, txtstr ):
        #creating logfile

        pass
    def print_to_gui(self, txtstr):
        self._texbox.config(state='normal')
        self._texbox.insert('end', '%s\n' %txtstr)
        self._texbox.config(state="disabled")
        self._texbox.see("end")
        self._root.update()
gui=ApcGui()
