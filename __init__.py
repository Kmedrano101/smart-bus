"""
 Support for smart-BUS G4 devices
 @author: Kmedrano101
 Created on Tue Aug 30 15:45:35 2022
 List of operations code
     Relays:
         - single channel control : 0x0031 >> response: 0x0032 add 0FEEEEEEEE at the begining
         - read status of channels: 0x0033 >> response: 0x0034 add 0BEEEEEEEE at the begining
     Sensors:
         - read status
 Protocol information from: www.smarthomebus.com/downloads-7-protocols.html
"""
# Import modules

import asyncio
import binascii
import socket
from ctypes import c_ushort, c_ubyte, c_byte
from homeassistant.helpers import discovery
from homeassistant.helpers.entity import Entity
import logging

DOMAIN = "smartg4"

_LOGGER = logging.getLogger(__name__)

# start socket server
IP = ""
PORT = 6000
ADDRESS = (IP,PORT)
server = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
server.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
server.bind(ADDRESS)

# Define protocol base Smart-Bus G4

CRC_TAB = [ 0x0000, 0x1021, 0x2042, 0x3063, 0x4084, 0x50a5, 0x60c6, 0x70e7,
            0x8108, 0x9129, 0xa14a, 0xb16b, 0xc18c, 0xd1ad, 0xe1ce, 0xf1ef,
            0x1231, 0x0210, 0x3273, 0x2252, 0x52b5, 0x4294, 0x72f7, 0x62d6,
            0x9339, 0x8318, 0xb37b, 0xa35a, 0xd3bd, 0xc39c, 0xf3ff, 0xe3de,
            0x2462, 0x3443, 0x0420, 0x1401, 0x64e6, 0x74c7, 0x44a4, 0x5485,
            0xa56a, 0xb54b, 0x8528, 0x9509, 0xe5ee, 0xf5cf, 0xc5ac, 0xd58d,
            0x3653, 0x2672, 0x1611, 0x0630, 0x76d7, 0x66f6, 0x5695, 0x46b4,
            0xb75b, 0xa77a, 0x9719, 0x8738, 0xf7df, 0xe7fe, 0xd79d, 0xc7bc,
            0x48c4, 0x58e5, 0x6886, 0x78a7, 0x0840, 0x1861, 0x2802, 0x3823,
            0xc9cc, 0xd9ed, 0xe98e, 0xf9af, 0x8948, 0x9969, 0xa90a, 0xb92b,
            0x5af5, 0x4ad4, 0x7ab7, 0x6a96, 0x1a71, 0x0a50, 0x3a33, 0x2a12,
            0xdbfd, 0xcbdc, 0xfbbf, 0xeb9e, 0x9b79, 0x8b58, 0xbb3b, 0xab1a,
            0x6ca6, 0x7c87, 0x4ce4, 0x5cc5, 0x2c22, 0x3c03, 0x0c60, 0x1c41,
            0xedae, 0xfd8f, 0xcdec, 0xddcd, 0xad2a, 0xbd0b, 0x8d68, 0x9d49,
            0x7e97, 0x6eb6, 0x5ed5, 0x4ef4, 0x3e13, 0x2e32, 0x1e51, 0x0e70,
            0xff9f, 0xefbe, 0xdfdd, 0xcffc, 0xbf1b, 0xaf3a, 0x9f59, 0x8f78,
            0x9188, 0x81a9, 0xb1ca, 0xa1eb, 0xd10c, 0xc12d, 0xf14e, 0xe16f,
            0x1080, 0x00a1, 0x30c2, 0x20e3, 0x5004, 0x4025, 0x7046, 0x6067,
            0x83b9, 0x9398, 0xa3fb, 0xb3da, 0xc33d, 0xd31c, 0xe37f, 0xf35e,
            0x02b1, 0x1290, 0x22f3, 0x32d2, 0x4235, 0x5214, 0x6277, 0x7256,
            0xb5ea, 0xa5cb, 0x95a8, 0x8589, 0xf56e, 0xe54f, 0xd52c, 0xc50d,
            0x34e2, 0x24c3, 0x14a0, 0x0481, 0x7466, 0x6447, 0x5424, 0x4405,
            0xa7db, 0xb7fa, 0x8799, 0x97b8, 0xe75f, 0xf77e, 0xc71d, 0xd73c,
            0x26d3, 0x36f2, 0x0691, 0x16b0, 0x6657, 0x7676, 0x4615, 0x5634,
            0xd94c, 0xc96d, 0xf90e, 0xe92f, 0x99c8, 0x89e9, 0xb98a, 0xa9ab,
            0x5844, 0x4865, 0x7806, 0x6827, 0x18c0, 0x08e1, 0x3882, 0x28a3,
            0xcb7d, 0xdb5c, 0xeb3f, 0xfb1e, 0x8bf9, 0x9bd8, 0xabbb, 0xbb9a,
            0x4a75, 0x5a54, 0x6a37, 0x7a16, 0x0af1, 0x1ad0, 0x2ab3, 0x3a92,
            0xfd2e, 0xed0f, 0xdd6c, 0xcd4d, 0xbdaa, 0xad8b, 0x9de8, 0x8dc9,
            0x7c26, 0x6c07, 0x5c64, 0x4c45, 0x3ca2, 0x2c83, 0x1ce0, 0x0cc1,
            0xef1f, 0xff3e, 0xcf5d, 0xdf7c, 0xaf9b, 0xbfba, 0x8fd9, 0x9ff8,
            0x6e17, 0x7e36, 0x4e55, 0x5e74, 0x2e93, 0x3eb2, 0x0ed1, 0x1ef0 ]

# List of telegram initial values 0 > Relay Switch and Ligth dimmer
SMART_BUS_START_DATA = "C0A801DE534D415254434C4F5544AAAA"
SMART_BUS_COMMAND = {"write_relay":["0FEEEEEEEE0031","0032"],
                     "read_relay":["0BEEEEEEEE0033","0034"]} # According to smart-bus operation code from structure protocol
SMART_BUS_PROTOCOL = {"write_relay": [15, 238, 238, 238, 238, 0, 49, 0, 0, 0, 0, 0, 0, 0, 0], # Set status Relay
                      "read_relay":  [11, 238, 238, 238, 238, 0, 51, 0, 0, 0, 0]}             # Get status Relay

def setup(hass, config):
    """Set up the Smart G4 component."""
    _LOGGER.debug("Created the base object G4")
    hass.data[DOMAIN] = Smartg4Device()
    return True

class udp_interface:
    """High-level interface for UDP connections.
    It is initialized with an optional queue size for the incoming datagrams.
    """

    def __init__(self, transport, port=6000):
        self._port = port
        self._closed = False
        self._transport = transport
        
    def close(self):
        if self._closed:
            return
        self._closed = True
        if self._transport:
            self._transport.close()

    # User methods

    def send(self, data, addr):
        """Send a datagram to the given address."""
        self._transport.sendto(data, addr)
        if self._closed:
            raise IOError("udp_interface is closed")

    async def receive(self):
        """Wait for an incoming datagram and return it with
        the corresponding address.
        """
        data, addr = self._transport.recvfrom(1024)
        return data, addr

    def abort(self):
        """Close the transport immediately."""
        if self._closed:
            raise IOError("udp_interface is closed")
        self._transport.abort()
        self.close()

    # Properties

    @property
    def address(self):
        """The udp_interface address as a (host, port) tuple."""
        return self._transport.getsockname()

    @property
    def closed(self):
        """Indicates whether the endpoint is closed or not."""
        return self._closed

class Smartg4Device(Entity):
    """Smart-Bus G4 base low control for devices"""
    
    def __init__(self): 
        self.telegram_udp = binascii.a2b_hex("00000000") # this just for test
        self.port = 6000 

    def turn_on_relay(self):
        # Send datagram 
        server.sendto(self.telegram_udp, ('<broadcast>',self.port))
        
    def turn_off_relay(self):
        # Send datagram 
        server.sendto(self.telegram_udp, ('<broadcast>',self.port))
    
    def generate_trama(self, dev_canal, dev_id, level, sub_id=1, command_type="write_relay") -> None:
        """Create UPD telegram according to smart-bus g4 protocol"""
        intBufLen = 13
        if command_type == "read_relay":
            intBufLen = 9
        SMART_BUS_PROTOCOL[command_type][7] = sub_id
        SMART_BUS_PROTOCOL[command_type][8] = dev_id
        if command_type == "write_relay":
            SMART_BUS_PROTOCOL[command_type][9] = dev_canal
            SMART_BUS_PROTOCOL[command_type][10] = level
        
        wdCRC = c_ushort(0)
        wdCRC.value = 0
        wdPtrCount = 0
        bytDat = c_ubyte(0)
        bytDat.value = 0
        AuxByDat=0
        auxB = c_byte(0)
        CRCHigh = c_ubyte(0)
        CRCLow = c_ubyte(0)

        while intBufLen != 0:
            bytDat.value = wdCRC.value >> 8
            wdCRC.value = wdCRC.value << 8
            AuxByDat = bytDat.value
            auxB.value = AuxByDat ^ SMART_BUS_PROTOCOL[command_type][wdPtrCount]
            AuxwdCRC = wdCRC.value
            wdCRC.value = AuxwdCRC ^ CRC_TAB[auxB.value]
            wdPtrCount = wdPtrCount + 1
            intBufLen = intBufLen -1
        
        CRCHigh.value = wdCRC.value >> 8
        CRCLow.value = wdCRC.value & 0xff
        
        SUBNET_ID = hex(sub_id).lstrip("0x").upper()
        if len(SUBNET_ID)==1:
            SUBNET_ID = "0"+SUBNET_ID
        DEVICE_ID = hex(dev_id).lstrip("0x").upper()
        if len(DEVICE_ID)==1:
            DEVICE_ID = "0"+DEVICE_ID
            
        if command_type == "write_relay":
            CANNAL = hex(dev_canal).lstrip("0x").upper()
            if len(CANNAL)==1:
                CANNAL = "0"+CANNAL
            if  level == 0:
                LEVEL = "00"
            else:
                LEVEL = hex(level).lstrip("0x").upper()
                if len(LEVEL)==1:
                    LEVEL = "0"+LEVEL
        CRC_H = hex(CRCHigh.value).lstrip("0x").upper()
        if len(CRC_H)==1:
            CRC_H = "0"+CRC_H
        CRC_L = hex(CRCLow.value).lstrip("0x").upper()
        if len(CRC_L)==1:
            CRC_L = "0"+CRC_L    
            
        # Create the final datagram to send
        if command_type == "write_relay":
            telegram_udp = SMART_BUS_START_DATA+SMART_BUS_COMMAND[command_type][0]+SUBNET_ID+DEVICE_ID+CANNAL+LEVEL+"0000"+CRC_H+CRC_L
        if command_type == "read_relay":
            telegram_udp = SMART_BUS_START_DATA+SMART_BUS_COMMAND[command_type][0]+SUBNET_ID+DEVICE_ID+CRC_H+CRC_L
        self.telegram_udp = binascii.a2b_hex(telegram_udp)
    
    async def get_status_relay(self,dev_canal,dev_id, sub_id=1):
        """ Get status of a channel relay """
        status = False
        data, (host, port) = await self.receive()
        if len(data) == 43 and data[17]==sub_id and data[18]==dev_id:
            if data[21] == 0 and data[22] == 52:
                # update this for diferent percent % of lights
                if data[25+dev_canal] == 0:
                    status = False
                else:
                    status = True
        return status
                
"""
async def main():
    objeto = Smartg4Device()
    await objeto.generate_trama_to_send(7, 27, 100,command_type="read_relay")
    while True:
        print("Ready to capture")
        await objeto.get_status_relay(7,27,sub_id=1)
    
    
if __name__ == "__main__":
    asyncio.run(main()) # run_forever"""