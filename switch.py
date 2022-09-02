"""Support for smart-BUS G4 Switch Devices"""
import logging
import voluptuous as vol
try:
    from homeassistant.components.switch import SwitchEntity
except ImportError:
    from homeassistant.components.switch import SwitchDevice as SwitchEntity
from homeassistant.components.switch import  PLATFORM_SCHEMA
from homeassistant.const import CONF_NAME
import homeassistant.helpers.config_validation as cv
from . import DOMAIN

_LOGGER = logging.getLogger(__name__)


CONF_RELE = "reles"
CONF_DEVICE_ID = "device_id"
CONF_SUBNET_ID = "subnet_id"

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
    _LOGGER.debug("Smart G4 Switch component running ...")
    device = hass.data[DOMAIN]
    reles = config.get(CONF_RELE)
    switches = []
    for pinnum, op in reles.items():
        switches.append(Smartg4Switch(pinnum, op, device))   
    async_add_entities(switches)

class Smartg4Switch(SwitchEntity):

    def __init__(self, num_pin, options, device):
        self._state = False
        self._name = options.get(CONF_NAME)
        self._device_id = options.get(CONF_DEVICE_ID)
        self._subnet_id = options.get(CONF_SUBNET_ID)
        self._numrele = num_pin
        self._trama_udp = device.generate_trama
        self.turn_on_handler = device.turn_on_relay
        self.turn_off_handler = device.turn_off_relay
        self.update_state_handler = device.get_status_relay
    
    @property
    def is_on(self):
        """If the switch is currently on or off."""
        return self._state

    async def async_turn_on(self):
        """Turn the switch on."""
        self._state = True
        self._trama_udp(self._numrele, self._device_id, 100, self._subnet_id)
        self.turn_on_handler()
        self.schedule_update_ha_state()

    async def async_turn_off(self):
        """Turn the switch off."""
        self._state = False
        self._trama_udp(self._numrele, self._device_id, 0, self._subnet_id)
        self.turn_off_handler()
        self.schedule_update_ha_state()

    @property
    def should_poll(self):
        """No polling needed."""
        return False

    @property
    def name(self):
        """Name of the device."""
        return self._name

    async def async_update(self):
        _LOGGER.debug("Smart G4 Ready for update")
        #self._trama_udp(self._numrele, self._device_id, 0, self._subnet_id, command_type="read_relay")
        #self._state = self.update_state_handler(self._numrele, self._device_id, self._subnet_id)
        return self._state