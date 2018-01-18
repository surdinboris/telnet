import serial
import time
import io

buff=io.BytesIO(b'')


ser=serial.Serial('COM4',
                  timeout=5,
                  baudrate=9600,
                  xonxoff=0,
                  stopbits=1,
                  parity=serial.PARITY_NONE,
                  bytesize=8)

#sio = io.TextIOWrapper(ser,  newline='\r')

def inwait(func): #decorator function for monitoring
    def wrapper(*args,**kwargs):
        func(*args,**kwargs)
        if (ser.inWaiting() > 0):
            # if incoming bytes are waiting to be read from the serial input buffer
            data_str = ser.read(ser.inWaiting()).decode('ascii')
            buff.write(ser.read(ser.inWaiting()))
            print(data_str, end='')
    return wrapper

@inwait
def sendcom(cmd=b''):
    ser.write(cmd)
    ser.write(bytes("\r", encoding='ascii'))
    time.sleep(0.5)

@inwait
def login():
    for e in range(3):
        sendcom()
    ser.read_until(b"User Name :")
    sendcom(b'apc')
    ser.read_until(b"Password  :")
    sendcom(b'apc')
    ser.read_until(b"apc>")


@inwait
def command(cmd='lcdBlink id#:1 1'):
    print('Opening com interface...')
    login()
    sendcom(cmd.encode())
    sendcom(b'exit')
    return buff.getvalue().decode('ascii')


if __name__ == "__main__":
    command('tcpip')