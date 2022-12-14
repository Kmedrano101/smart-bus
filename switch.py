"""Support for smart-BUS G4 Switch Devices"""
import logging
import voluptuous as vol
try:
    from homeassistant.components.switch import SwitchEntity
except ImportError:
    from homeassistant.components.switch import SwitchDevice as SwitchEntity
from homeassistant.components.switch import  PLATFORM_SCHEMA
from homeassistant.const import CONF_NAME, STATE_ON
import homeassistant.helpers.config_validation as cv
from . import Switch_interface
from homeassistant.core import callback
from datetime import timedelta

from .const import (
    DOMAIN,
    CONF_RELE,
    CONF_DEVICE_ID,
    CONF_SUBNET_ID,
    ICON_SWITCH
)

SCAN_INTERVAL = timedelta(seconds=12)

_LOGGER = logging.getLogger(__name__)

RELE_SCHEMA = vol.Schema( 
    {
        vol.Required(CONF_NAME): cv.string,
        vol.Required(CONF_DEVICE_ID): cv.positive_int,
        vol.Required(CONF_SUBNET_ID, default=1): cv.positive_int,
    }
)
PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend(
    {
        vol.Required(CONF_RELE, default={}): vol.Schema({cv.positive_int: RELE_SCHEMA})
    })

async def async_setup_platform(hass, config, async_add_entities, discovery_info=None):
    """Set up the switch platform."""
    _LOGGER.info("Smart G4 Switch component running ...")
    reles = config.get(CONF_RELE)
    switches = []
    for pinnum, op in reles.items():
        switches.append(Smartg4Switch(pinnum, op, ICON_SWITCH))
        _LOGGER.info("Smart G4 Switch component added.")   
    async_add_entities(switches)
    

class Smartg4Switch(Switch_interface, SwitchEntity):

    def __init__(self, num_pin, options, icon):
        self._state = False
        self._name = options.get(CONF_NAME)
        self._device_id = options.get(CONF_DEVICE_ID)
        self._subnet_id = options.get(CONF_SUBNET_ID)
        self._numrele = num_pin
        self._icon = icon
        super().__init__(dev_id=self._device_id, sub_id=self._subnet_id)
        
    @property
    def is_on(self):
        """If the switch is currently on or off."""
        return self._state

    async def async_turn_on(self):
        """Turn the switch on."""
        self._state = True
        await self.async_set_relay(dev_canal=self._numrele, level=100)
        self.hass.data[DOMAIN]["data"] = None

    async def async_turn_off(self):
        """Turn the switch off."""
        self._state = False
        await self.async_set_relay(dev_canal=self._numrele, level=0)
        self.hass.data[DOMAIN]["data"] = None

    @property
    def should_poll(self):
        """Polling needed."""
        return True

    @property
    def name(self):
        """Name of the device."""
        return self._name
    
    @property
    def icon(self):
        """Return the image of the sensor."""
        return self._icon
    
    @callback
    async def async_update(self):
        _LOGGER.info("Smart G4 Ready for update")
        self._data = self.hass.data[DOMAIN]["data"]
        if self._data is not None:
            if self._data[25+self._numrele] == 0:
                    self._state = False
            else:
                self._state = STATE_ON
            return self._state
        else:
            _LOGGER.info("No data recived")
        return False