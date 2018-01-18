import serial
import time
import io

class Apconfg():
    def __init__(self):
        if __name__ == "__main__":
            buff = io.BytesIO(b'')
            ser = serial.Serial('COM4',
                                     timeout=3,
                                     baudrate=9600,
                                     xonxoff=0,
                                     stopbits=1,
                                     parity=serial.PARITY_NONE,
                                     bytesize=8)
            command('lcdBlink id#:1 1')

  #sio = io.TextIOWrapper(ser,  newline='\r')

    def inwait(self):
        if (self.ser.inWaiting() > 0):
            # if incoming bytes are waiting to be read from the serial input buffer
            self.buff.write(self.ser.read(self.ser.inWaiting()))
            print(self.buff.getvalue().decode('ascii'))
            return self.buff.getvalue().decode('ascii')
            # read the bytes and convert from binary array to ASCII
            #print(data_str, end='')

    def sendcom(self,cmd=b''):
        print(self.ser)
        self.ser.write(cmd)
        self.ser.write(bytes("\r", encoding='ascii'))


    def login(self):
        for e in range(3):
            self.sendcom()
        self.ser.read_until(b"User")
        self.sendcom(b'apc')
        self.ser.read_until(b"Password")
        self.sendcom(b'apc')
        self.ser.read_until(b"apc>")
        self.inwait()

    def command(self,cmd='lcdBlink id#:1 1'):
        print('Opening com interface...')
        self.login()
        self.sendcom(cmd.encode())
        self.sendcom(b'exit')
        return self.buff.getvalue().decode('ascii')

app=Apconfg()