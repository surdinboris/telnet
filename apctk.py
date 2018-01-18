import serial
import time
import io
import sys

debug = False
class Apconfg():
    def __init__(self):
        if __name__ == "__main__":
            self.comm=b''
            self.buff = io.BytesIO(b'')
            self.ser = serial.Serial('COM1',
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
    def conn_init(self):
        for x in range(2):
            self.ser.write(bytes("\r", encoding='ascii'))

    def sendcom(self,cmd=b''):
        self.ser.write(cmd)

        self.ser.write(bytes("\r", encoding='ascii'))
        time.sleep(2)
        if debug == True:
            self.inwait()

    def handler(self):
        self.promt=self.ser.readlines()
        while len(self.promt) == 0: # activating new session
            print('Trying to initialize serial connection...')
            self.conn_init()
            self.promt=self.ser.readlines()
            print(self.promt)

            #print('modified',self.promt)

        if self.promt[-1] == b'User Name : ':
            print('logging in...')
            self.sendcom(b'apc')
            self.ser.read_until(b'Password : ')
            self.sendcom(b'apc')
            self.ser.read_until(b'apc>')
            return True
        elif self.promt[-1] == b'apc>':
            return True
        elif self.promt[-1] == b"Enter 'YES' to continue or <ENTER> to cancel : " and self.comm == b'YES':
            return True
        else:
            print(self.promt)
            raise BaseException(ConnectionError)

    def command(self,comm):
        self.comm=(comm.encode()) #updating class variable for handling accept commands
        print('Executing command...')
        self.handler()
        self.sendcom(comm.encode())
        time.sleep(3)

    def getver(self):
        self.handler()
        self.sendcom(b'about')
        self.ser.read_until(b"aos")
        self.ser.read_until(b"v")

        self.ver=self.ser.readlines()
        print(self.ver)
        return self.ver[0]

app=Apconfg()
app.command('olReboot all')
getver=app.getver()

if getver == b'5.1.4\r\n' or b'6.1.3\r\n':
    print('ver 5.1.4')
    app.command("tcpip -S enable -i 192.168.0.122 -s 255.255.255.0 -g 0.0.0.0 -h pdu-1")
    app.command("reboot")
    app.command("YES")
