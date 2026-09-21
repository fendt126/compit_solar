import logging
import time
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.const import CONF_EMAIL, CONF_PASSWORD
from homeassistant.helpers.aiohttp_client import async_get_clientsession

import compit_inext_api.definitions
from compit_inext_api.device_definitions import DeviceDefinitionsLoader
from compit_inext_api.types.DeviceDefinitions import Device
from compit_inext_api.params_dictionary import PARAMS
from compit_inext_api.consts import CompitParameter
from compit_inext_api.connector import CompitApiConnector

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

# Informujemy HA, że mamy platformy sensor i climate
PLATFORMS = ["sensor", "climate"]

# --- MONKEY PATCHING DLA MODELU 68 ORAZ BRAKUJĄCYCH ZMIENNYCH ---
original_get_def = DeviceDefinitionsLoader.get_device_definitions

async def patched_get_device_definitions(lang: str):
    definitions = await original_get_def(lang)
    
    if not any(d.code == 68 for d in definitions.devices):
        base_device = next((d for d in definitions.devices if d.code == 45), None)
        parameters = base_device.parameters if base_device else []
        
        definitions.devices.append(
            Device(
                name="SolarComp 971SD B1",
                parameters=parameters,
                code=68,
                device_class=18,
                id=None
            )
        )
    return definitions

DeviceDefinitionsLoader.get_device_definitions = patched_get_device_definitions

# Przypisanie kluczy znanych modeli do modelu 68
for param, mapping in PARAMS.items():
    if 45 in mapping and 68 not in mapping:
        mapping[68] = mapping[45]

# Naprawa brakujących kluczy odczytywanych przez sterownik jako "niedostępne"
PARAMS.setdefault(CompitParameter.TANK_T4_TEMPERATURE, {})[68] = "__t4"
PARAMS.setdefault(CompitParameter.ENERGY_TOTAL, {})[68] = "__ecala"
PARAMS.setdefault(CompitParameter.ENERGY_CONSUMPTION, {})[68] = "__eelmwh"
PARAMS.setdefault(CompitParameter.ENERGY_YESTERDAY, {})[68] = "__eelkwh"
# -------------------------------------------------------------

class CompitDeviceData:
    """Współdzielona klasa zarządzająca buforowaniem odświeżania do max 1 zapytania na 45 sek."""
    def __init__(self, connector, device_id):
        self.connector = connector
        self.device_id = device_id
        self.last_update = 0

    async def async_update(self):
        now = time.time()
        if now - self.last_update > 45:
            await self.connector.update_state(self.device_id)
            self.last_update = now


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    email = entry.data[CONF_EMAIL]
    password = entry.data[CONF_PASSWORD]
    session = async_get_clientsession(hass)

    connector = CompitApiConnector(session)
    success = await connector.init(email, password, lang="en")
    
    if not success or not connector.all_devices:
        _LOGGER.error("Brak połączenia lub urządzeń Compit")
        return False
        
    solar_device_id = next(
        (d_id for d_id, d in connector.all_devices.items() if getattr(d.definition, 'code', 0) == 68), 
        list(connector.all_devices.keys())[0]
    )

    data_manager = CompitDeviceData(connector, solar_device_id)

    # Przekazanie instancji danych do poszczególnych platform (sensor / number)
    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN][entry.entry_id] = data_manager

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True

async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)