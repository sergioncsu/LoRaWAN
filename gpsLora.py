#!/usr/bin/env python3
import serial
import time
import pynmea2
import logging
from config import read_config_file
from serial.threaded import LineReader, ReaderThread
from lora_connection import arg, ConnectionState, PrintLines

# Configure logging
lora_config = read_config_file('config.txt')
logging.basicConfig(filename='serial_log.txt', level=logging.INFO)

port = lora_config['port']
baud = lora_config['baud']

ser = serial.Serial(port, baudrate=57600)

print(lora_config)

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
