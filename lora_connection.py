#!/usr/bin/env python3
import io
import sys
import time
import datetime
import argparse
import subprocess
from enum import IntEnum
import serial
from serial.threaded import LineReader, ReaderThread
from config import read_config_file

# Configure logging
lora_config = read_config_file('config.txt')

port = lora_config['port']
APP_SESSION_KEY = lora_config['APP_SESSION_KEY']
NET_SESSION_KEY = lora_config['NET_SESSION_KEY']
DEVICE_ADDRESS = lora_config['DEVICE_ADDRESS']
PORT = lora_config['PORT']

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
