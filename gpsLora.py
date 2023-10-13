#!/usr/bin/env python3
import os
import serial
import time
import pynmea2
import logging

from enum import IntEnum
from datetime import datetime
from config import read_config_file
from lora_connection import PrintLines, ConnectionState
from serial.threaded import ReaderThread
from logger import setup_logger

config = read_config_file('config.txt')
ser = serial.Serial(config['LORA_PORT'], baudrate = config['LORA_BAUD'])
setup_logger()

with ReaderThread(ser, PrintLines) as protocol:
    time.sleep(2)
    dr = config['MIN_DR'];
    c = 0
    dr_delay= [1.5,1.5,1.5,1.5,1.5]
    while True:
        if protocol.state != ConnectionState.CONNECTED:
            logging.info("Not Connected to LoRaWAN Network...")
            time.sleep(1)
            continue
        try:
            serialPort = serial.Serial(config['GPS_PORT'], baudrate=config['GPS_BAUD'], timeout=30)
            raw_data = serialPort.readline().decode().strip()
            
        #   Uncomment One of those if you want to test with hardcoded location (Indoor testing)
            #raw_data = "$GPGGA,202530.00,5109.0262,N,11401.8407,W,5,40,0.5,1097.36,M,-17.00,M,18,TSTR*61"
            raw_data= "$GPGGA,083459.00,3536.415917,N,07840.661100,W,1,05,2.3,99.7,M,-33.5,M,,*61"

            if raw_data.find('GGA') > 0:
                msg = pynmea2.parse(raw_data)
                lat_int = int(abs(float(msg.latitude) * 1e8))
                lon_int = int(abs(float(msg.longitude) * 1e6))
                merged_coordinates = str(dr) + str(lat_int) + str(lon_int)
                c=c+1
              # Uncomment if you want to test LoRa commands.  
               # test = input("waiting for RN2903 command\n")
               # protocol.send_cmd(test)
              # -------------------------
                protocol.send_cmd("mac set dr %d" % dr,1)                               
                protocol.send_cmd("mac tx uncnf 1 " + merged_coordinates, dr_delay[dr])
                
                dr = dr + 1 if dr < config['MAX_DR'] else config['MIN_DR']
                
        except Exception as e:
            logging.error(f"Serial port exception: {e}")
            serialPort.close()  # Close the serial port
            time.sleep(5)
            continue

        #exit(protocol.state)
