import serial
import time
import io
import tkinter as tk
from tkinter import *
from tkinter import ttk,messagebox

debug = False

def crconn():
    ser = serial.Serial(
        'COM1',
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
    print('Got command %s of type'% comm, type)
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




class ApcGui():

    def __init__(self):
        self.run = True
        self._root = Tk()
        self._root.title('LED test config\control tool')

        self._mainframe = tk.Frame(self._root)
        self._mainframe.grid(row=0, column=0, sticky=(E, W, N, S))
        self._configframe=tk.LabelFrame(self._mainframe, text='Config')
        self._configframe.grid(row=0, column=0, sticky=(W,S))
        self._configframe.columnconfigure(0, weight=1)
        self._configframe.rowconfigure(0, weight=1)
        self._pdu1conf_btn=tk.Button(self._configframe,text='PDU-1', command=lambda: self.pduconf(1))
        self._pdu1conf_btn.grid(row=0, column=1, sticky=W, padx=5)
        self._pdu2conf_btn=tk.Button(self._configframe,text='PDU-2', command=lambda: self.pduconf(2))
        self._pdu2conf_btn.grid(row=0, column=2, sticky=W, padx=5)
        self._pdu3conf_btn=tk.Button(self._configframe,text='PDU-3', command=lambda: self.pduconf(3))
        self._pdu3conf_btn.grid(row=1, column=1, sticky=W, padx=5)
        self._pdu4conf_btn=tk.Button(self._configframe,text='PDU-4', command=lambda: self.pduconf(4))
        self._pdu4conf_btn.grid(row=1, column=2, sticky=W, padx=5)

        self._root.mainloop()


    def pduconf(self,pdunum):
            self.butts = [self._pdu1conf_btn, self._pdu2conf_btn, self._pdu3conf_btn, self._pdu4conf_btn]
            for butt in self.butts:
                butt.config(state='disabled')
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

        return "break"



gui=ApcGui()
