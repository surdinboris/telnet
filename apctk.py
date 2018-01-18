import serial
import time
import io

class Apconfg():
    def __init__(self):
        if __name__ == "__main__":
            self.buff = io.BytesIO(b'')
            self.ser = serial.Serial('COM4',
                                     timeout=3,
                                     baudrate=9600,
                                     xonxoff=0,
                                     stopbits=1,
                                     parity=serial.PARITY_NONE,
                                     bytesize=8)
            self.command('olReboot all')

  #sio = io.TextIOWrapper(ser,  newline='\r')

    def inwait(self):
        if (self.ser.inWaiting() > 0):
            # if incoming bytes are waiting to be read from the serial input buffer
            self.buff.write(self.ser.read(self.ser.inWaiting()))
            # read the bytes and convert from binary array to ASCII
            self.data_str = self.ser.read(self.ser.inWaiting()).decode('ascii')
            print('data',self.data_str, end='')

    def sendcom(self,cmd=b''):
        self.ser.write(cmd)
        self.ser.write(bytes("\r", encoding='ascii'))
        self.inwait()


    def login(self):
        for e in range(3):
            self.sendcom()
        self.ser.read_until(b"User")
        self.sendcom(b'apc')
        self.ser.read_until(b"Password")
        self.sendcom(b'apc')
        self.ser.read_until(b"apc>")
        self.inwait()

    def command(self,cmd='tcpip'):
        print('Opening com interface...')
        self.login()
        self.sendcom(cmd.encode())
        self.sendcom(b'exit')
        self.inwait()

app=Apconfg()