import serial
import time
import io

class Apconfg():
    def __init__(self,mode,command):
        if __name__ == "__main__":
            self.buff = io.BytesIO(b'')
            self.ser = serial.Serial('COM4',
                                     timeout=3,
                                     baudrate=9600,
                                     xonxoff=0,
                                     stopbits=1,
                                     parity=serial.PARITY_NONE,
                                     bytesize=8)
            if mode == 'verify':
                pass
            elif mode == 'exec':
                self.cmd=command
                #self.command(command)
            else:
                print('invalid mode')

    def inwait(self):
        if (self.ser.inWaiting() > 0):

            # if incoming bytes are waiting to be read from the serial input buffer
            self.data_str = self.ser.read(self.ser.inWaiting()).decode('ascii')
            self.buff.write(self.ser.read(self.ser.inWaiting()))
            # read the bytes and convert from binary array to ASCII

            print(self.data_str, end='')

    def sendcom(self,cmd=b''):
        self.inwait()
        self.ser.write(cmd)
        self.ser.write(bytes("\r", encoding='ascii'))
        time.sleep(1)
        self.inwait()

    def login(self):
        for e in range(3):
            self.sendcom()
        self.ser.read_until(b"User")
        self.sendcom(b'apc')
        self.ser.read_until(b"Password")
        self.sendcom(b'apc')
        self.ser.read_until(b"apc>")

    def command(self):
        print('Opening com interface...')
        self.login()
        self.sendcom(self.cmd.encode())
        self.sendcom(b'exit')

app=Apconfg(mode='exec',command='olReboot all',) #command, mode(exec, verify)
app.command()