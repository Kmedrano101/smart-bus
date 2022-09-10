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

import binascii
import socket
from ctypes import c_ushort, c_ubyte, c_byte
from datetime import timedelta
from homeassistant.helpers.event import track_time_interval
from homeassistant.helpers.entity import Entity
import logging
from .const import (
    DOMAIN,
    IP,
    PORT,
    CRC_TAB,
    SMART_BUS_START_DATA,
    SMART_BUS_COMMAND,
    SMART_BUS_PROTOCOL
)

_LOGGER = logging.getLogger(__name__)

# start socket server
ADDRESS = (IP,PORT)
server = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
server.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
server.bind(ADDRESS)


def setup(hass, config):
    """Set up the Smart G4 component."""
    _LOGGER.info("Created the base object G4")
    hass.data[DOMAIN] = {}
    hass.data[DOMAIN]["data"] = None 
    
    device = Switch_interface()
    
    def request_status_relay(event_time):
        # send request to device 
        _LOGGER.info("Running the update function")
        device.set_status_relay(0,command_type="read_relay")

    track_time_interval(hass, request_status_relay, timedelta(seconds=3))
    
    def call_buffer(event_time):
        device.get_data_status_relay()
        if device._data is not None:
            hass.data[DOMAIN]["data"] = device._data
        else:
            _LOGGER.info(
                "Couldn't get values from device, retrying on next scheduled update ..."
            )
            
    track_time_interval(hass, call_buffer, timedelta(seconds=0.5))
    return True

class Switch_interface(Entity):
    """High-level interface for UDP connections.
    It is initialized with an optional queue size for the incoming datagrams.
    """

    def __init__(self, dev_id=27, sub_id=1, port=6000):
        self._port = port
        self._closed = False
        self._data = None
        self._telegram_udp = None
        self._dev_id = dev_id
        self._sub_id = sub_id
        
    def close(self):
        if self._closed:
            return
        self._closed = True
        if server:
            server.close()

    # User methods
    def get_data_status_relay(self) -> None:
        """ Get status of a channel relay """
        data, (host, port) =  server.recvfrom(1024)
        if port == self._port:
            if len(data) == 43 and data[21] == 0 and data[22] == 52:
                self._data = data

    def set_status_relay(self, dev_canal, level=None, command_type="write_relay") -> None:
        """Create UPD telegram according to smart-bus g4 protocol"""
        intBufLen = 13
        if command_type == "read_relay":
            intBufLen = 9
        SMART_BUS_PROTOCOL[command_type][7] = self._sub_id
        SMART_BUS_PROTOCOL[command_type][8] = self._dev_id
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
        
        SUBNET_ID = hex(self._sub_id).lstrip("0x").upper()
        if len(SUBNET_ID)==1:
            SUBNET_ID = "0"+SUBNET_ID
        DEVICE_ID = hex(self._dev_id).lstrip("0x").upper()
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
        self._telegram_udp = binascii.a2b_hex(telegram_udp)
        server.sendto(self._telegram_udp, ('<broadcast>',self._port))