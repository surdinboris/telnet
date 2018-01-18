import serial
import time
import io

debug = True
buff=io.BytesIO(b'')
ser=serial.Serial('COM4',
                  timeout=3,
                  baudrate=9600,
                  xonxoff=0,
                  stopbits=1,
                  parity=serial.PARITY_NONE,
                  bytesize=8)

#sio = io.TextIOWrapper(ser,  newline='\r')

def inwait(func): #decorator function for monitoring
    def wrapper(*args,**kwargs):
        func(*args, **kwargs)
        if debug == True and (ser.inWaiting() > 0):
            # if incoming bytes are waiting to be read from the serial input buffer
            data_str = ser.read(ser.inWaiting()).decode('ascii')
            buff.write(ser.read(ser.inWaiting()))
            print(data_str, end='')

    return wrapper

@inwait
def sendcom(cmd=b''):
    ser.write(cmd)
    ser.write(bytes("\r", encoding='ascii'))
    time.sleep(1)


def login():
    for e in range(2):
        sendcom()
    ser.read_until(b"User Name :")
    sendcom(b'apc')
    ser.read_until(b"Password  :")
    sendcom(b'apc')
    ser.read_until(b"apc>")


def command(cmd='lcdBlink id#:1 1'):
    print('Opening com interface...')
    login()
    sendcom(cmd.encode())
    sendcom(b'exit')


if __name__ == "__main__":
    command('tcpip')