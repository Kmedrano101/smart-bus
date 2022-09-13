"""Support for smart-BUS G4 Light Devices"""
import logging
from datetime import timedelta
import voluptuous as vol
from homeassistant.const import CONF_NAME, STATE_ON
import homeassistant.helpers.config_validation as cv
from . import Switch_interface
from homeassistant.core import callback
from homeassistant.components.light import  (
    ATTR_BRIGHTNESS,
    PLATFORM_SCHEMA,
    SUPPORT_BRIGHTNESS,
    LightEntity,
)
from .const import (
    DOMAIN,
    CONF_DEVICE_ID,
    CONF_SUBNET_ID,
    CONF_DIMMER,
    ICON_LIGHT
)

_LOGGER = logging.getLogger(__name__)

SUPPORT_SMARTG4 = SUPPORT_BRIGHTNESS
SCAN_INTERVAL = timedelta(seconds=12)

DIMMER_SCHEMA = vol.Schema( 
    {
        vol.Required(CONF_NAME): cv.string,
        vol.Required(CONF_DEVICE_ID): cv.positive_int,
        vol.Required(CONF_SUBNET_ID, default=1): cv.positive_int,
    }
)
PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend(
    {
        vol.Required(CONF_DIMMER, default={}): vol.Schema({cv.positive_int: DIMMER_SCHEMA})
    }
)

async def async_setup_platform(hass, config, async_add_entities, discovery_info=None):
    """Set up the light platform."""
    _LOGGER.info("Smart G4 Light component running ...")
    dimmers = config.get(CONF_DIMMER)
    lights = []
    for pinnum, op in dimmers.items():
        lights.append(Smartg4Light(pinnum, op, ICON_LIGHT))   
    async_add_entities(lights)
	
class Smartg4Light(Switch_interface, LightEntity):

    def __init__(self, num_pin, options, icon):
        self._state = False
        self._name = options.get(CONF_NAME)
        self._device_id = options.get(CONF_DEVICE_ID)
        self._subnet_id = options.get(CONF_SUBNET_ID)
        self._numrele = num_pin
        super().__init__(dev_id=self._device_id, sub_id=self._subnet_id)
        self._brightness = 0
        self._level = 0
        self._icon = icon

    @property
    def name(self):
        """Name of the device."""
        return self._name

    @property
    def icon(self):
        """Return the image of the device."""
        return self._icon

    @property
    def brightness(self):
        """Return the brightness of this light between 0-255"""
        return self._brightness

    @property
    def is_on(self):
        """If the light is currently on or off."""
        return self._state

    @property
    def supported_features(self):
        """Flag supported features."""
        return SUPPORT_SMARTG4

    @property
    def should_poll(self):
        """Polling needed."""
        return True

    async def async_turn_on(self, **kwargs):
        """Turn the Light on."""
        brightness = kwargs.get(ATTR_BRIGHTNESS)
        if brightness is not None:
            self._brightness = brightness
        self._level = (int)((self._brightness * 100 )/ 255)
        await self.async_set_relay(dev_canal=self._numrele, level=self._level)
        self.hass.data[DOMAIN]["data"] = None
        self._state = True

    async def async_turn_off(self):
        """Turn the light off."""
        await self.async_set_relay(dev_canal=self._numrele, level=0)
        self.hass.data[DOMAIN]["data"] = None
        self._state = False

    @callback
    async def async_update(self):
        _LOGGER.info("Smart G4 Ready for update")
        self._data = self.hass.data[DOMAIN]["data"]
        if self._data is not None:
            if self._data[25+self._numrele] == 0:
                    self._state = False
                    self._brightness = 0
            else:
                self._state = STATE_ON
                self._brightness = self._data[25+self._numrele]
            return self._state
        else:
            _LOGGER.info("No data recived")
        return False