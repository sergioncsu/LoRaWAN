
from config import read_config_file
from serial.threaded import LineReader
from enum import IntEnum
import time
from logger import setup_logger
import logging

lora_config = read_config_file('config.txt')
setup_logger()
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
        if(self.retries >= lora_config['RETRIES']):
            logging.info("Too many retries, exiting")
            self.state = ConnectionState.TO_MANY_RETRIES
            return
        self.retries = self.retries + 1
        action()

    def get_var(self, cmd):
        self.send_cmd(cmd)
        return self.transport.serial.readline()

    def join(self):
        if lora_config['JOIN_MODE'] == 'abp':
            self.join_abp()
        else:
            self.join_otaa()

    def join_otaa(self):
        
        self.send_cmd('mac set appeui %s' % lora_config['APP_SESSION_KEY'])
        self.send_cmd('mac set appkey %s' % lora_config['NET_SESSION_KEY'])
        self.send_cmd('mac set deveui %s' % lora_config['DEVICE_ADDRESS'])
        self.send_cmd('mac join otaa')

    def join_abp(self):

        self.send_cmd('mac set devaddr %s' % lora_config['DEVICE_ADDRESS'])
        self.send_cmd('mac set appskey %s' % lora_config['APP_SESSION_KEY'])
        self.send_cmd('mac set nwkskey %s' % lora_config['NET_SESSION_KEY'])
        self.send_cmd('mac join abp')
        time.sleep(2)
        logging.info("Setting init variables...")
        self.send_cmd("mac set ar " + lora_config['ar'])
        self.send_cmd("mac set pwridx %d" % lora_config['pwridx'])
        self.send_cmd("mac set class " + lora_config['class'])
        self.send_cmd("mac set retx %d" % lora_config['retx'])
        self.send_cmd("mac set adr " + lora_config['adr'])
        logging.info("Done...")

    def connection_made(self, transport):
        print("Connection to LoStik established")
        self.transport = transport
        self.retry(self.join)

    def handle_line(self, data):
        print("STATUS: %s" % data)
        if data.strip() == "denied" or data.strip() == "no_free_ch":
            logging.info("Retrying OTAA connection")
            self.retry(self.join)
        elif data.strip() == "accepted":
            logging.info("UPDATING STATE to connected")
            self.state = ConnectionState.CONNECTED

    def connection_lost(self, exc):
        if exc:
            logging.error(f"Serial port exception: {exc}")
        logging.error(f"Lost connection to LoRa serial device: {exc}")

    def send_cmd(self, cmd, delay=0.5):
        logging.info(cmd)
        self.transport.write(('%s\r\n' % cmd).encode('UTF-8'))
        time.sleep(delay)
