#!/usr/bin/env python3

import serial
import time
import pynmea2
import logging

import time

from enum import IntEnum
import serial
from serial.threaded import LineReader, ReaderThread

# Configure logging
logging.basicConfig(filename='serial_log.txt', level=logging.INFO)

port = '/dev/ttyS0'
baud = 9600
APP_SESSION_KEY = "fd3add07a556a0eb8d9e83de5e165518"
NET_SESSION_KEY = "d9a9ba84de42adc98c44dc3fb79665f5"
DEVICE_ADDRESS = "00dda0f5"
PORT = "/dev/ttyUSB0"

class arg :
    joinmode = "abp"
    appskey = APP_SESSION_KEY
    nwkskey = NET_SESSION_KEY
    devaddr = DEVICE_ADDRESS
    appeui = ""
    deveui = ""
    appkey = ""
    port = PORT

class ConnectionState(IntEnum):
    SUCCESS = 0
    CONNECTING = 100
    CONNECTED = 200
    FAILED = 500
    TO_MANY_RETRIES = 520
    
args = arg()
print(args.appskey)
OTAA_RETRIES = 5


def read_config_file(filename):
    # Create an empty dictionary to store the variables
    config_vars = {}

    # Open the file and read each line
    with open(filename, 'r') as f:
        lines = f.readlines()

    # Process each line
    for line in lines:
        # Ignore comments and empty lines
        if line.startswith('#') or line.strip() == '':
            continue

        # Split the line into variable and value
        var, val = line.split('=')

        # Store the variable and value in the dictionary
        config_vars[var.strip()] = int(val.strip())

    return config_vars


class PrintLines(LineReader):

    retries = 0
    state = ConnectionState.CONNECTING

    def retry(self, action):
        if(self.retries >= OTAA_RETRIES):
            print("Too many retries, exiting")
            self.state = ConnectionState.TO_MANY_RETRIES
            return
        self.retries = self.retries + 1
        action()

    def get_var(self, cmd):
        self.send_cmd(cmd)
        return self.transport.serial.readline()

    def join(self):
        if args.joinmode == "abp":
            self.join_abp()
        else:
            self.join_otaa()

    def join_otaa(self):
        if len(args.appeui):
            self.send_cmd('mac set appeui %s' % args.appeui)
        if len(args.appkey):
            self.send_cmd('mac set appkey %s' % args.appkey)
        if len(args.deveui):
            self.send_cmd('mac set deveui %s' % args.deveui)
        self.send_cmd('mac join otaa')

    def join_abp(self):
        if len(args.devaddr):
            self.send_cmd('mac set devaddr %s' % args.devaddr)
        if len(args.appskey):
            self.send_cmd('mac set appskey %s' % args.appskey)
        if len(args.nwkskey):
            self.send_cmd('mac set nwkskey %s' % args.nwkskey)
        self.send_cmd('mac join abp')

    def connection_made(self, transport):
        print("Connection to LoStik established")
        self.transport = transport
        self.retry(self.join)

    def handle_line(self, data):
        print("STATUS: %s" % data)
        if data.strip() == "denied" or data.strip() == "no_free_ch":
            print("Retrying OTAA connection")
        #    self.retry(self.join)
        elif data.strip() == "accepted":
            print("UPDATING STATE to connected")
            self.state = ConnectionState.CONNECTED

    def connection_lost(self, exc):
        if exc:
            print(exc)
        print("Lost connection to serial device")

    def send_cmd(self, cmd, delay=.5):
        print(cmd)
        self.transport.write(('%s\r\n' % cmd).encode('UTF-8'))
        time.sleep(delay)

ser = serial.Serial(args.port, baudrate=57600)


config_vars = read_config_file('config.txt')
print(config_vars)  # Output: {'var1': 10, 'var2': 20}

with ReaderThread(ser, PrintLines) as protocol:
    time.sleep(2)
    sf = 7;
    dr = 0;
    while True:
        if protocol.state != ConnectionState.CONNECTED:
            print("NOT")
            time.sleep(1)
            continue
        try:
            serialPort = serial.Serial(port, baudrate=baud, timeout=30)
            raw_data = serialPort.readline().decode().strip()
            #print(raw_data)
            #raw_data = "$GPGGA,202530.00,5109.0262,N,11401.8407,W,5,40,0.5,1097.36,M,-17.00,M,18,TSTR*61"
            #raw_data= "$GPGGA,083459.00,3536.415917,N,07840.661100,W,1,05,2.3,99.7,M,-33.5,M,,*61"

            if raw_data.find('GGA') > 0:
                msg = pynmea2.parse(raw_data)
                #print(msg)
            #    test = input("waiting for RN2903 command\n")
             #   protocol.send_cmd(test)

                lat_int = int(abs(float(msg.latitude) * 1e8))
                lon_int = int(abs(float(msg.longitude) * 1e6))
                merged_coordinates = str(lat_int) + str(lon_int)
                
                #protocol.send_cmd("mac set dr 0")
                protocol.send_cmd("mac set dr %d" % dr)
                
                #protocol.send_cmd("radio set sf sf%d"%sf)
                #protocol.send_cmd("radio get sf")
                
                protocol.send_cmd("mac tx uncnf 1 " + merged_coordinates)
                #protocol.send_cmd("radio tx " + merged_coordinates)
                #protocol.send_cmd("radio get sf")
                #print(lat_int)
                #print(lon_int)
                #sf = sf + 1 if sf < 13 else 7
                dr = dr + 1 if dr < 3 else 0
        except Exception as e:
            logging.error(f"Serial port exception: {e}")
            print(e)
            serialPort.close()  # Close the serial port
            time.sleep(5)
            continue

        #exit(protocol.state)
