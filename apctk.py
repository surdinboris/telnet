import serial
import time
import io
import tkinter as tk
from tkinter import *
import threading
from tkinter import ttk,messagebox

debug = False

class Apconfg():
    def __init__(self):
        if __name__ == "__main__":
            self.comm=b'' #shared var
            self.buff = io.BytesIO(b'')
            self.ser = serial.Serial(
                'COM1',
                timeout=3,
                baudrate=9600,
                xonxoff=0,
                stopbits=1,
                parity=serial.PARITY_NONE,
                bytesize=8)

    def inwait(self):
        if (self.ser.inWaiting() > 0):
            time.sleep(1)
            # if incoming bytes are waiting to be read from the serial input buffer
            self.data_str = self.ser.read(self.ser.inWaiting()).decode('ascii')
            self.buff.write(self.ser.read(self.ser.inWaiting()))
            # read the bytes and convert from binary array to ASCII
            print(self.data_str, end='')

    def conn_init(self): #initiation procedure for console - need to send enter two  or more times fastly
        for x in range(3):
            self.ser.write(bytes("\r", encoding='ascii'))

    def sendcom(self,cmd=b''):
        self.ser.write(cmd)
        self.ser.write(bytes("\r", encoding='ascii'))
        time.sleep(2)
        if debug == True:
            self.inwait()

    def handler(self): #login/accept handler
        self.promt=self.ser.readlines()
        while len(self.promt) == 0: # activating new session
            print('Trying to bring up serial connection...')
            self.conn_init()
            self.promt=self.ser.readlines()
        if self.promt[-1] == b'User Name : ': #login prompt - login procedure execution
            print('Logging in...')
            self.sendcom(b'apc')
            self.ser.read_until(b'Password : ')
            self.sendcom(b'apc')
            self.ser.read_until(b'apc>')
            return True
        elif self.promt[-1] == b'apc>': #already logged in - not need to enter
            print('Already logged in...')
            return True
        elif self.promt[-1] == b"Enter 'YES' to continue or <ENTER> to cancel : " and self.comm == b'YES': # dialoque - need to pass accept command
            print('Passing accept command')
            return True
        else: #unexpected login prompt state
            raise BaseException(ConnectionError)

    def command(self,comm):
        print('Got command %s'% comm)
        self.comm=(comm.encode()) #updating shared class variable for handling accept commands
        self.handler()
        print('Passing command %s...' % comm)
        self.sendcom(comm.encode())
        time.sleep(2)
        return True

    def getver(self): #returns aos version
        self.handler()
        self.sendcom(b'about')
        self.ser.read_until(b"aos")
        self.ser.read_until(b"v")
        self.ver=self.ser.readlines()
        return self.ver[0]


#getver=app.getver()

#app.command('lcdBlink id#:1 1')
#
# if getver == b'5.1.4\r\n' or b'6.1.3\r\n':
#     print('Found compatible version %s' %getver.decode('ascii'))
#     app.command("tcpip -S enable -i 192.168.0.139 -s 255.255.255.0 -g 0.0.0.0 -h pdu-1")
#     app.command("reboot")
#     app.command("YES")

class ApcGui():

    def __init__(self):
        self.run = True
        self._root = Tk()
        self._root.title('LED test config\control tool')
        self.app = Apconfg()
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
            self.app.command("tcpip -S enable -i 9.151.140.15{} -s 255.255.255.0 -g 0.0.0.0 -h pdu-{}".format(pdunum,pdunum))
            self.app.command("reboot")
            self.app.command("YES")
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
