#!/usr/bin/env python3

import serial
import time
import pynmea2
import logging
from enum import IntEnum
from serial.threaded import LineReader, ReaderThread
from config import read_config_file
import logging
from logging.handlers import TimedRotatingFileHandler
import os
from datetime import datetime

# Create a logger
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Create a file handler
log_directory = 'logs'
if not os.path.exists(log_directory):
    os.makedirs(log_directory)
log_file = os.path.join(log_directory, f'{datetime.now().strftime("%Y-%m-%d")}.log')
file_handler = TimedRotatingFileHandler(log_file, when='midnight', interval=1)
file_handler.suffix = '%Y-%m-%d.log'
file_handler.setLevel(logging.INFO)

# Create a stream handler
stream_handler = logging.StreamHandler()
stream_handler.setLevel(logging.INFO)

# Create a formatter that adds timestamps
formatter = logging.Formatter('%(levelname)s - %(asctime)s - %(message)s',
datefmt='%H:%M:%S')
file_handler.setFormatter(formatter)
stream_handler.setFormatter(formatter)

# Add both handlers to the logger
logger.addHandler(file_handler)
logger.addHandler(stream_handler)

#logging.basicConfig(filename='serial_log.txt', level=logging.INFO)
lora_config = read_config_file('config.txt')

port = lora_config['port']
baud = lora_config['baud']
LORA_BAUD = lora_config['LORA_BAUD']

APP_SESSION_KEY = lora_config['APP_SESSION_KEY']
NET_SESSION_KEY = lora_config['NET_SESSION_KEY']
DEVICE_ADDRESS = lora_config['DEVICE_ADDRESS']

APPEUI = lora_config['APP_SESSION_KEY']
APPKEY = lora_config['NET_SESSION_KEY']
DEVEUI = lora_config['DEVICE_ADDRESS']
LORA_PORT = lora_config['LORA_PORT']
JOIN_MODE = lora_config['JOIN_MODE']
OTAA_RETRIES =  lora_config['RETRIES']

class ConnectionState(IntEnum):
    SUCCESS = 0
    CONNECTING = 100
    CONNECTED = 200
    FAILED = 500
    TO_MANY_RETRIES = 520
    
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
        print(JOIN_MODE)
        if JOIN_MODE == 'abp':
            self.join_abp()
        else:
            self.join_otaa()

    def join_otaa(self):
        if len(APPEUI):
            self.send_cmd('mac set appeui %s' % APPEUI)
        if len(APPKEY):
            self.send_cmd('mac set appkey %s' % APPKEY)
        if len(DEVEUI):
            self.send_cmd('mac set deveui %s' % DEVEUI)
        self.send_cmd('mac join otaa')

    def join_abp(self):
        if len(DEVICE_ADDRESS):
            self.send_cmd('mac set devaddr %s' % DEVICE_ADDRESS)
        if len(APP_SESSION_KEY):
            self.send_cmd('mac set appskey %s' % APP_SESSION_KEY)
        if len(NET_SESSION_KEY):
            self.send_cmd('mac set nwkskey %s' % NET_SESSION_KEY)
        self.send_cmd('mac join abp')

    def connection_made(self, transport):
        print("Connection to LoStik established")
        self.transport = transport
        self.retry(self.join)

    def handle_line(self, data):
        print("STATUS: %s" % data)
        if data.strip() == "denied" or data.strip() == "no_free_ch":
            print("Retrying OTAA connection")
            self.retry(self.join)
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

ser = serial.Serial(LORA_PORT, baudrate = LORA_BAUD)
config_vars = read_config_file('config.txt')

with ReaderThread(ser, PrintLines) as protocol:
    time.sleep(2)
    dr = 0;
    init_config = 1
    while True:
        if protocol.state != ConnectionState.CONNECTED:
            print("NOT")
            time.sleep(1)
            continue
        try:
            if (init_config and protocol.state == ConnectionState.CONNECTED):
                logging.info("Setting init variables...")
                protocol.send_cmd("mac set ar " + lora_config['ar'])
                protocol.send_cmd("mac set pwridx %d" % lora_config['pwridx'])
                protocol.send_cmd("mac set class " + lora_config['class'])
                protocol.send_cmd("mac set retx %d" % lora_config['retx'])
                protocol.send_cmd("mac set adr " lora_config['adr'])
                
                init_config = 0
            serialPort = serial.Serial(port, baudrate=baud, timeout=30)
            raw_data = serialPort.readline().decode().strip()
            
            #raw_data = "$GPGGA,202530.00,5109.0262,N,11401.8407,W,5,40,0.5,1097.36,M,-17.00,M,18,TSTR*61"
            #raw_data= "$GPGGA,083459.00,3536.415917,N,07840.661100,W,1,05,2.3,99.7,M,-33.5,M,,*61"

            if raw_data.find('GGA') > 0:
                msg = pynmea2.parse(raw_data)
                #print(msg)
                test = input("waiting for RN2903 command\n")
                protocol.send_cmd(test)

                lat_int = int(abs(float(msg.latitude) * 1e8))
                lon_int = int(abs(float(msg.longitude) * 1e6))
                merged_coordinates = str(lat_int) + str(lon_int)
                
                #protocol.send_cmd("mac set dr 0")
                protocol.send_cmd("mac set dr %d" % dr)
                
                               
                protocol.send_cmd("mac tx uncnf 1 " + merged_coordinates)
                #protocol.send_cmd("radio tx " + merged_coordinates)
                
                dr = dr + 1 if dr < lora_config['MAX_DR'] else lora_config['MIN_DR']
                
        except Exception as e:
            logging.error(f"Serial port exception: {e}")
            print(e)
            serialPort.close()  # Close the serial port
            time.sleep(5)
            continue

        #exit(protocol.state)
